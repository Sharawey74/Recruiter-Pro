"""
Agent 3: Hybrid Scoring Agent

Composes the scoring collaborators in src/agents/scoring/ and blends their
output. It holds no scoring logic of its own: its job is to hold the two
dependencies, apply the configured weights, and assemble a ScoreBreakdown.

    SkillMatcher   owns the skill vocabulary
    MLScorer       owns the ATS model
    components     the scorers that depend on nothing

Every weight below comes from config/agents.yaml and nowhere else. The
percentages this docstring used to quote (60/25/10/5) were wrong on two counts:
they had never matched the runtime values, and they omitted title similarity
entirely -- which is 17% of every rule-based score.
"""

import logging
from typing import List, Optional

from ..storage.models import ScoreBreakdown, CVProfile, JobPosting
from ..core.config import get_config
from ..core.vocabulary import load_alias_index
from .scoring import components
from .scoring.ml_scorer import MLScorer
from .scoring.skill_matcher import SkillMatch, SkillMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Re-exported: SkillMatch was defined here before the split.
__all__ = ["HybridScoringAgent", "SkillMatch"]


class HybridScoringAgent:
    """
    Agent 3: Hybrid Scorer

    1. Rule-based: skills, title, experience, education and keywords, each
       weighted by config/agents.yaml
    2. ML-based: ATS Engine prediction (optional; absent model -> rule-based)
    3. Hybrid: rule_weight/ml_weight blend of the two
    """

    def __init__(self, config=None):
        self.config = config or get_config()
        self.scoring_config = self.config.scoring

        # The model is loaded here, not inside MLScorer's constructor: 2.7 says
        # constructing a scorer must not read the filesystem. An unloadable
        # model yields an inert scorer and a warning, never an exception.
        self.ml_scorer = MLScorer.load() if self.scoring_config.ml_enabled else MLScorer(None)

        # The vocabulary is read once, here, and handed to the matcher that
        # owns it. Nothing else in this class needs it.
        self.skill_matcher = SkillMatcher(load_alias_index(self.config.skills_database_path))

    def score_matches(
        self, cv: CVProfile, jobs: List[JobPosting], include_ml: bool = True
    ) -> List[ScoreBreakdown]:
        """
        Score one CV against many jobs, with a single ML call for the batch.

        Same results as calling score_match in a loop -- the rule-based path is
        per-job either way, and the batched model call is row-independent. The
        difference is that the model is invoked once rather than once per job,
        which was 8.13 s of the 8.0 s upload against the real corpus.

        Args:
            cv: Candidate CV profile
            jobs: Job postings to score against
            include_ml: Whether to include ML scoring

        Returns:
            One ScoreBreakdown per job, in the order given.
        """
        ml_scores = self.ml_scorer.score_batch(cv, jobs) if include_ml else [None] * len(jobs)
        return [
            self._score_one(cv, job, ml_score)
            # strict: score_batch returns one entry per job by contract. If
            # that ever stops being true, fail loudly rather than silently
            # scoring a prefix of the corpus.
            for job, ml_score in zip(jobs, ml_scores, strict=True)
        ]

    def score_match(
        self, cv: CVProfile, job: JobPosting, include_ml: bool = True
    ) -> ScoreBreakdown:
        """
        Score CV-Job match using hybrid approach

        Args:
            cv: Candidate CV profile
            job: Job posting requirements
            include_ml: Whether to include ML scoring

        Returns:
            ScoreBreakdown with all scoring components
        """
        ml_score = self.ml_scorer.score(cv, job) if include_ml else None
        return self._score_one(cv, job, ml_score)

    def _score_one(
        self, cv: CVProfile, job: JobPosting, ml_score: Optional[float]
    ) -> ScoreBreakdown:
        """
        Assemble one breakdown from an already-computed ML score.

        Split out so the single-job and batch paths share every line of the
        rule-based scoring and the blend. Only how the ML score is obtained
        differs between them.
        """
        # 1. Rule-based scoring
        skill_match = self.skill_matcher.match(cv.skills, job.required_skills, job.preferred_skills)
        experience_score = components.score_experience(cv, job)
        education_score = components.score_education(cv, job)
        keyword_score = components.score_keywords(cv, job)
        title_score = components.score_title_similarity(cv, job)

        # Weighted rule-based score. The weights live in config/agents.yaml and
        # nowhere else -- they used to be hardcoded here while config declared a
        # different set that nothing read, so retuning the YAML did nothing.
        weights = self.scoring_config
        rule_based_score = (
            skill_match.match_ratio * weights.skill_weight
            + title_score * weights.title_weight
            + experience_score * weights.experience_weight
            + education_score * weights.education_weight
            + keyword_score * weights.keyword_weight
        )

        # 2. Calculate hybrid score
        if ml_score is not None:
            hybrid_score = (
                rule_based_score * self.scoring_config.rule_weight
                + ml_score * self.scoring_config.ml_weight
            )
        else:
            hybrid_score = rule_based_score

        # 3. Detect over/under qualification
        overqualified = components.is_overqualified(cv, job, experience_score)
        underqualified = components.is_underqualified(cv, job, skill_match.match_ratio)

        # 4. Build score breakdown
        return ScoreBreakdown(
            skill_score=skill_match.match_ratio,
            title_score=title_score,
            experience_score=experience_score,
            education_score=education_score,
            keyword_score=keyword_score,
            rule_based_score=rule_based_score,
            ml_score=ml_score,
            hybrid_score=hybrid_score,
            matched_skills=skill_match.matched_skills,
            missing_skills=skill_match.missing_skills,
            extra_skills=skill_match.extra_skills,
            overqualified=overqualified,
            underqualified=underqualified,
        )
