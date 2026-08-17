"""
The `LLMProvider` protocol and the two types it moves between.

ADR-2 decided this shape: two methods, no base class, no registry, no plugin
discovery. Implementations are related by structure rather than inheritance, so
each one is independently testable and a fake is about five lines.

`ExplanationContext` exists so providers never import `src.storage.models`. An
explanation needs thirteen scalar facts about a match; handing providers the
whole `MatchResult` would couple every provider to the persistence layer and to
whatever that model grows next.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, runtime_checkable

# Where an explanation came from. Surfaced to the caller as
# `explanation_source` so a rule-based fallback is visible rather than silently
# passed off as model output.
SOURCE_RULE_BASED = "rule_based"


@dataclass(frozen=True)
class ExplanationContext:
    """Everything a provider needs to explain one match. No model objects."""

    candidate_name: str
    job_title: str
    final_score: float
    decision: str
    confidence: float

    skill_score: float
    experience_score: float
    education_score: float
    keyword_score: float

    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)

    overqualified: bool = False
    underqualified: bool = False

    # Optional because rule-based scoring runs with no model at all.
    ml_score: Optional[float] = None

    @classmethod
    def from_match_result(cls, match) -> "ExplanationContext":
        """Build a context from a MatchResult. The only place the two meet."""
        score = match.score_breakdown
        return cls(
            candidate_name=match.candidate_name or "This candidate",
            job_title=match.job_title,
            final_score=match.final_score,
            decision=match.decision.decision.value,
            confidence=match.decision.confidence,
            skill_score=score.skill_score,
            experience_score=score.experience_score,
            education_score=score.education_score,
            keyword_score=score.keyword_score,
            matched_skills=list(score.matched_skills or []),
            missing_skills=list(score.missing_skills or []),
            overqualified=bool(score.overqualified),
            underqualified=bool(score.underqualified),
            ml_score=score.ml_score,
        )


@dataclass(frozen=True)
class Explanation:
    """One explanation, tagged with what produced it."""

    text: str
    source: str


@runtime_checkable
class LLMProvider(Protocol):
    """
    Two methods. Streaming, token counting, retry policy and model selection
    stay inside implementations, where they actually differ -- a protocol that
    grows to cover every provider's features becomes the union of all of them
    and constrains nothing.

    `explain` takes and returns a list because the caller explains a bounded
    batch (at most `MatchingPipeline.MAX_EXPLANATIONS`) and a provider that can
    genuinely batch should be free to. Returning a list of the same length as
    the input is part of the contract.
    """

    name: str

    def is_available(self) -> bool:
        """Whether this provider can serve a request right now."""
        ...

    def explain(self, batch: List[ExplanationContext]) -> List[Explanation]:
        """Explain each context. Must return one Explanation per input."""
        ...
