"""
The provider that always works.

ADR-2's load-bearing claim: rule-based explanation is a first-class provider,
not an error path. It satisfies the same protocol as the model-backed ones, is
selectable by config, and is what CI runs -- no network, no key, no quota. Every
other provider falls back to it, so it must never fail.

The logic is ported from the fallback inside agent4_llm_explainer, with one
defect fixed on the way: variant selection used `hash(candidate) % 3`. Python
randomises string hashing per process, so the same candidate got a different
opening sentence after every server restart. That is the same non-determinism
that produced varying keyword scores in Agent 3 and it violates the determinism
rule in ADR-1. It uses crc32 now, which is stable across processes and
machines.
"""

from __future__ import annotations

from typing import List
from zlib import crc32

from .protocol import SOURCE_RULE_BASED, Explanation, ExplanationContext


def _variant(seed: str, options: List[str]) -> str:
    """Pick a variant deterministically. See the module docstring."""
    return options[crc32(seed.encode("utf-8")) % len(options)]


class RuleBasedProvider:
    """Deterministic, offline, always available."""

    name = SOURCE_RULE_BASED

    def is_available(self) -> bool:
        """Always. That is the entire point of this provider."""
        return True

    def explain(self, batch: List[ExplanationContext]) -> List[Explanation]:
        return [Explanation(self._render(c), self.name) for c in batch]

    # -- rendering -------------------------------------------------------

    def _render(self, c: ExplanationContext) -> str:
        parts = [
            self._opening(c),
            self._strengths(c),
            self._concerns(c),
            self._recommendation(c),
        ]
        return " ".join(p for p in parts if p)

    @staticmethod
    def _opening(c: ExplanationContext) -> str:
        name, title, s = c.candidate_name, c.job_title, c.final_score
        if s >= 0.90:
            options = [
                f"{name} demonstrates outstanding qualifications for the {title} position with a {s:.0%} match score.",
                f"Exceptional match: {name} achieves a {s:.0%} alignment score for the {title} role.",
                f"{name} presents an excellent profile scoring {s:.0%} for this {title} opportunity.",
            ]
        elif s >= 0.80:
            options = [
                f"{name} presents strong credentials for the {title} position with a {s:.0%} match score.",
                f"Strong candidate: {name} scores {s:.0%} for the {title} role.",
                f"{name} demonstrates solid qualifications with a {s:.0%} match for this {title} position.",
            ]
        elif s >= 0.70:
            options = [
                f"{name} shows good potential for the {title} position with a {s:.0%} match score.",
                f"Promising candidate: {name} achieves a {s:.0%} alignment for the {title} role.",
                f"{name} presents a viable profile scoring {s:.0%} for this {title} opportunity.",
            ]
        elif s >= 0.60:
            options = [
                f"{name} presents a moderate fit for the {title} position with a {s:.0%} match score.",
                f"Borderline candidate: {name} scores {s:.0%} for the {title} role.",
                f"{name} shows potential but has gaps, scoring {s:.0%} for this {title} position.",
            ]
        else:
            options = [
                f"{name} falls below requirements for the {title} position with a {s:.0%} match score.",
                f"Limited alignment: {name} achieves only a {s:.0%} match for the {title} role.",
                f"{name} shows significant gaps with a {s:.0%} score for this {title} opportunity.",
            ]
        return _variant(name, options)

    @staticmethod
    def _strengths(c: ExplanationContext) -> str:
        details = []

        if c.matched_skills:
            count = len(c.matched_skills)
            top = ", ".join(c.matched_skills[:6])
            if c.skill_score >= 0.85:
                details.append(
                    f"Excellent technical proficiency demonstrated in {top} ({count} matched skills)."
                )
            elif c.skill_score >= 0.70:
                details.append(f"Strong capabilities in {top} with {count} matched skills.")
            else:
                details.append(f"Proficient in {top}, covering {count} required areas.")

        if c.experience_score >= 0.85:
            details.append("Experience level aligns perfectly with role requirements.")
        elif c.experience_score >= 0.70:
            details.append("Relevant experience level for this position.")

        if c.education_score >= 0.90:
            details.append("Educational background exceeds role requirements.")
        elif c.education_score >= 0.75:
            details.append("Appropriate educational qualifications.")

        if c.keyword_score >= 0.80:
            details.append("Resume demonstrates relevant domain expertise and terminology.")

        return " ".join(details)

    @staticmethod
    def _concerns(c: ExplanationContext) -> str:
        details = []

        if c.missing_skills:
            count = len(c.missing_skills)
            sample = ", ".join(c.missing_skills[:5])
            if count >= 5:
                details.append(f"Notable gaps in {sample} and {count - 5} other areas.")
            elif count >= 3:
                details.append(f"Missing key competencies: {sample}.")
            else:
                details.append(f"Minor gaps in {sample}.")

        if c.experience_score < 0.50:
            details.append("Experience level may be insufficient for role demands.")
        if c.underqualified:
            details.append("Overall skill coverage falls short of requirements.")
        if c.overqualified:
            details.append("Candidate may be overqualified, consider retention risk.")

        return " ".join(details)

    @staticmethod
    def _recommendation(c: ExplanationContext) -> str:
        decision = (c.decision or "").lower()
        parts = []

        if decision == "shortlist":
            if c.matched_skills:
                focus = ", ".join(c.matched_skills[:3])
                parts.append(f"Proceed with technical interview focusing on {focus}.")
            else:
                parts.append("Proceed with technical screening to validate qualifications.")
            if c.final_score >= 0.85:
                parts.append("Assess cultural fit and discuss role expectations.")
            else:
                parts.append(
                    "Verify proficiency in matched skills and assess learning agility for gaps."
                )

        elif decision == "review":
            parts.append("Recommend detailed manual review of experience and portfolio.")
            if c.missing_skills:
                training = ", ".join(c.missing_skills[:3])
                parts.append(f"Evaluate training potential for {training}.")
            if c.skill_score < 0.65:
                parts.append(
                    "Consider alternative roles better matching candidate's skill profile."
                )

        else:  # reject
            if c.final_score < 0.50:
                parts.append("Candidate does not meet minimum requirements for this position.")
            else:
                parts.append("Current profile does not align with role needs.")
            if c.missing_skills:
                gaps = ", ".join(c.missing_skills[:3])
                parts.append(f"Suggest developing competencies in {gaps} for future consideration.")
            else:
                parts.append("Consider for alternative roles or revisit if requirements evolve.")

        return " ".join(parts)
