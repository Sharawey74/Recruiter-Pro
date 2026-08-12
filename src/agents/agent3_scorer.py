"""
Agent 3: Hybrid Scoring Agent
Combines rule-based scoring with ML predictions for robust matching

Architecture:
- Rule-based scoring: Skill matching, experience, education (60% weight)
- ML scoring: ATS engine predictions (40% weight)
- Hybrid score: Weighted combination of both approaches
"""
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from ..storage.models import ScoreBreakdown, CVProfile, JobPosting
from ..core.config import get_config
from ..core.vocabulary import build_alias_index, load_alias_index
from ..ml_engine.ats_predictor import ATSPredictor
from .scoring import components

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SkillMatch:
    """Skill matching results"""
    matched_skills: List[str]
    missing_skills: List[str]
    extra_skills: List[str]
    match_ratio: float


class HybridScoringAgent:
    """
    Agent 3: Hybrid Scorer
    
    Combines rule-based and ML approaches for robust scoring:
    1. Rule-based: Skills (60%), Experience (25%), Education (10%), Keywords (5%)
    2. ML-based: ATS Engine prediction (optional)
    3. Hybrid: Weighted combination based on configuration
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.scoring_config = self.config.scoring
        
        # Initialize ML predictor if enabled
        self.ml_predictor = None
        if self.scoring_config.ml_enabled:
            try:
                self.ml_predictor = ATSPredictor(model_dir="models/production")
                if self.ml_predictor.load_model():
                    logger.info("[OK] ML Predictor initialized for hybrid scoring")
                    model_info = self.ml_predictor.get_model_info()
                    logger.info(f"   Model: {model_info.get('model_name', 'Unknown')}")
                    logger.info(f"   Test Recall: {model_info.get('test_metrics', {}).get('recall', 'N/A')}")
                else:
                    logger.warning("[WARN] Failed to load ML model. Using rule-based only.")
                    self.ml_predictor = None
            except Exception as e:
                logger.warning(f"[WARN] ML Predictor unavailable: {e}. Using rule-based only.")
                self.ml_predictor = None
        
        # Load the skill vocabulary as a flat {alias_lower: Canonical} index.
        self.skills_database = self._load_skills_database()

    @staticmethod
    def _build_alias_index(raw: Dict) -> Dict[str, str]:
        """Flatten the vocabulary. Delegates to the shared loader -- see
        src/core/vocabulary.py for why there is exactly one of these."""
        return build_alias_index(raw)

    def _load_skills_database(self) -> Dict[str, str]:
        """Load the shared skill vocabulary as a flat {alias_lower: Canonical}."""
        return load_alias_index(self.config.skills_database_path)

    def score_match(
        self, 
        cv: CVProfile, 
        job: JobPosting,
        include_ml: bool = True
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
        # 1. Rule-based scoring
        skill_match = self._score_skills(cv, job)
        experience_score = components.score_experience(cv, job)
        education_score = components.score_education(cv, job)
        keyword_score = components.score_keywords(cv, job)
        title_score = components.score_title_similarity(cv, job)
        
        # Weighted rule-based score. The weights live in config/agents.yaml and
        # nowhere else -- they used to be hardcoded here while config declared a
        # different set that nothing read, so retuning the YAML did nothing.
        weights = self.scoring_config
        rule_based_score = (
            skill_match.match_ratio * weights.skill_weight +
            title_score * weights.title_weight +
            experience_score * weights.experience_weight +
            education_score * weights.education_weight +
            keyword_score * weights.keyword_weight
        )
        
        # 2. ML-based scoring (if enabled)
        ml_score = None
        ml_probability = None
        if include_ml and self.ml_predictor:
            ml_result = self._get_ml_score(cv, job)
            if ml_result:
                # Convert ml_score from 0-100 to 0-1 scale
                ml_score = ml_result['ml_score'] / 100.0 if ml_result['ml_score'] > 1 else ml_result['ml_score']
                ml_probability = ml_result['probability']
        
        # 3. Calculate hybrid score
        if ml_score is not None:
            hybrid_score = (
                rule_based_score * self.scoring_config.rule_weight +
                ml_score * self.scoring_config.ml_weight
            )
        else:
            hybrid_score = rule_based_score
        
        # 4. Detect over/under qualification
        overqualified = components.is_overqualified(cv, job, experience_score)
        underqualified = components.is_underqualified(cv, job, skill_match.match_ratio)
        
        # 5. Build score breakdown
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
            underqualified=underqualified
        )
    
    def _score_skills(self, cv: CVProfile, job: JobPosting) -> SkillMatch:
        """
        Score skill matching between CV and job with enhanced precision
        
        Uses fuzzy matching, synonym detection, and weighted scoring
        """
        cv_skills = set(self._normalize_skills(cv.skills))
        required_skills = set(self._normalize_skills(job.required_skills))
        preferred_skills = set(self._normalize_skills(job.preferred_skills))
        
        # Sorted throughout: these lists were built with list(set(...)), so they
        # reordered between process restarts and extra_skills[:10] returned a
        # different ten skills each time. Same defect as the one already fixed
        # in _extract_keywords.
        matched_required = self._find_skill_matches(cv_skills, required_skills)
        matched_preferred = self._find_skill_matches(cv_skills, preferred_skills)
        matched_skills = sorted(set(matched_required + matched_preferred))

        # Find gaps
        missing_required = sorted(s for s in required_skills if not self._has_skill_match(s, cv_skills))
        missing_preferred = sorted(s for s in preferred_skills if not self._has_skill_match(s, cv_skills))

        # Extra skills candidate has
        extra_skills = sorted(cv_skills - required_skills - preferred_skills)
        
        # Calculate match ratio with enhanced precision
        total_required = len(required_skills) or 1
        total_preferred = len(preferred_skills) or 0
        
        # Weighted ratio: required skills are critical (85%), preferred are bonus (15%)
        required_match_ratio = len(matched_required) / total_required
        preferred_match_ratio = len(matched_preferred) / max(total_preferred, 1) if total_preferred > 0 else 0
        
        match_ratio = (required_match_ratio * 0.85) + (preferred_match_ratio * 0.15)
        
        # Penalty for missing critical required skills
        if len(missing_required) > len(required_skills) * 0.5:  # Missing more than 50%
            match_ratio *= 0.7  # 30% penalty
        
        return SkillMatch(
            matched_skills=matched_skills,
            missing_skills=missing_required + missing_preferred,
            extra_skills=extra_skills[:10],  # Limit to top 10
            match_ratio=min(1.0, match_ratio)
        )
    
    def _find_skill_matches(self, cv_skills: set, job_skills: set) -> List[str]:
        """
        Find which of job_skills the CV covers.

        Both sides have already been resolved to canonical names by
        _normalize_skills, so a direct set membership test is the match. There
        used to be a ~45-key synonym dict rebuilt as a local literal on every
        call -- once per job, plus once per missing skill -- which made it tens
        of thousands of reconstructions per upload. It was also unreachable:
        its keys and aliases are lowercase, while 667 of the 669 canonical
        names carry uppercase, so the comparison could never fire for any skill
        the vocabulary recognised. The two cases it did cover (devops, ai) were
        genuine vocabulary gaps and are now canonical entries in skills.json.

        Partial credit is granted on whole tokens, not raw substrings. The
        previous rule was `job_skill in cv_skill or cv_skill in job_skill`,
        which credited any pair sharing a character run of four or more --
        "Java" against "JavaScript", "Git" against "GitHub Actions", "SQL"
        against "MySQL", and ".NET" reduced to "net" against the "net" inside
        "PeNETration Testing". Twenty-nine such collisions exist among the 669
        canonical names.

        Requiring the job skill's tokens to be a subset of the CV skill's
        tokens removes all of those while keeping the cases where one skill
        genuinely contains the other as a named concept: "Communication"
        against "Written Communication" still matches, because "communication"
        is a whole token of it.
        """
        matches = []
        cv_token_sets = [(s, self._skill_tokens(s)) for s in cv_skills]

        for job_skill in job_skills:
            # Direct match on canonical names
            if job_skill in cv_skills:
                matches.append(job_skill)
                continue

            job_tokens = self._skill_tokens(job_skill)
            if not job_tokens:
                continue

            for _cv_skill, cv_tokens in cv_token_sets:
                if job_tokens < cv_tokens:
                    matches.append(job_skill)
                    break

        return matches

    @staticmethod
    def _skill_tokens(skill: str) -> frozenset:
        """Split a skill into comparable whole tokens, ignoring punctuation."""
        return frozenset(
            t for t in re.split(r"[^a-z0-9+#]+", skill.lower()) if t
        )

    def _has_skill_match(self, skill: str, cv_skills: set) -> bool:
        """Check if a skill has a match in CV skills"""
        return len(self._find_skill_matches(cv_skills, {skill})) > 0
    
    def _get_ml_score(self, cv: CVProfile, job: JobPosting) -> Optional[Dict]:
        """Get ML model prediction score"""
        if not self.ml_predictor:
            return None
        
        try:
            # Prepare CV data for ML predictor
            cv_data = {
                'Skills': ', '.join(cv.skills),
                'Experience': cv.experience_years or 0,
                'Education': cv.education or 'Bachelor',
                'Certifications': cv.extracted_data.get('certifications', 'None'),
                'Job Role': job.title,
                'Projects Count': cv.extracted_data.get('projects_count', 0),
                'Salary': cv.extracted_data.get('expected_salary', 50000)
            }
            
            # Get prediction from ML predictor
            result = self.ml_predictor.predict(cv_data, use_optimal_threshold=True)
            
            return result
            
        except Exception as e:
            logger.error(f"ML scoring failed: {e}")
            return None
    
    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """
        Resolve skill names to their canonical form.

        The vocabulary is consulted before punctuation is stripped, not after.
        Stripping first destroyed 16 index keys and made six canonical skills
        unreachable by their own name -- .NET normalized to "net", which matches
        nothing, so it passed through as the literal string. T-SQL, Monday.com,
        Outreach.io, Stand-ups and Non-Conformance Management failed the same
        way. The stripped form is still tried as a fallback, so inputs the
        index does not carry verbatim ("node.js" against a "nodejs" alias)
        still resolve.
        """
        normalized = []

        for skill in skills:
            cleaned = skill.lower().strip()

            canonical = self._get_canonical_skill(cleaned)
            if canonical:
                normalized.append(canonical)
                continue

            # Fall back to the punctuation-stripped form.
            stripped = cleaned.replace('.', '').replace('-', ' ')
            normalized.append(self._get_canonical_skill(stripped) or stripped)

        return normalized
    
    def _get_canonical_skill(self, skill: str) -> Optional[str]:
        """
        Resolve a skill to its canonical name.

        One dict lookup against the alias index built at load time, instead of
        the previous linear scan over the whole vocabulary per skill. That scan
        ran once per skill per job -- so at 800 jobs it was the hot path -- and
        it was also where A0 lived. See _build_alias_index.
        """
        if not self.skills_database:
            return None
        return self.skills_database.get(skill.lower())
    