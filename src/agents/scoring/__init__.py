"""
Agent 3's scoring collaborators.

Agent 3 was one 544-line class holding seven scoring components, a vocabulary
and an ML model. The split follows the dependency seam rather than the
component list: measured across all 18 methods, 209 LOC touched no instance
state at all, and exactly two things owned a dependency worth injecting.

    skill_matcher.SkillMatcher   owns the skill vocabulary
    ml_scorer.MLScorer           owns the ATS model
    components                   pure functions -- (cv, job) in, float out

`HybridScoringAgent` keeps only what is genuinely its own job: holding the two
collaborators, applying the configured weights, and assembling a
`ScoreBreakdown`.

An earlier plan called for five classes -- SkillMatcher, ExperienceScorer,
EducationScorer, MLScorer, HybridScorer. It was dropped for two reasons. It had
nowhere to put title similarity (the largest method in the file at 91 LOC) or
keyword scoring, so both would have landed in the class named for combining
rather than scoring. And four of the five would have wrapped functions that read
no state, giving them empty constructors -- ceremony that satisfies "inject your
dependencies" only because there are none to inject.
"""

from .components import (
    extract_keywords,
    is_overqualified,
    is_underqualified,
    score_education,
    score_experience,
    score_keywords,
    score_title_similarity,
)
from .ml_scorer import MLScorer
from .skill_matcher import SkillMatch, SkillMatcher

__all__ = [
    "SkillMatch",
    "SkillMatcher",
    "MLScorer",
    "score_experience",
    "score_title_similarity",
    "score_education",
    "score_keywords",
    "extract_keywords",
    "is_overqualified",
    "is_underqualified",
]
