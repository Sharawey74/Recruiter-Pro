"""
Structured insights: strengths, weaknesses and recommendations as lists.

Separate from explanation because it is a different product. An explanation is
prose for a person to read; insights are three lists a UI renders as bullets.
Only the rule-based derivation exists -- no provider generates these, and none
needs to: they are read directly off the score breakdown, so sending them to a
model would add latency and a hallucination surface for no gain.

Ported from agent4_llm_explainer.generate_structured_insights, behaviour
unchanged.
"""
from __future__ import annotations

from typing import Dict, List

from .protocol import ExplanationContext


def build(c: ExplanationContext) -> Dict[str, List[str]]:
    """Return {'strengths': [...], 'weaknesses': [...], 'recommendations': [...]}."""
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []

    if c.matched_skills:
        strengths.append(
            f"Proficient in {len(c.matched_skills)} key skills: "
            f"{', '.join(c.matched_skills[:4])}"
        )
    if c.experience_score >= 0.8:
        strengths.append("Experience level aligns well with job requirements")
    if c.education_score >= 0.9:
        strengths.append("Educational qualifications meet or exceed requirements")
    if c.ml_score and c.ml_score >= 0.75:
        strengths.append(f"Strong ATS compatibility score ({c.ml_score:.0%})")

    if c.missing_skills:
        weaknesses.append(
            f"Lacks {len(c.missing_skills)} required skills: "
            f"{', '.join(c.missing_skills[:4])}"
        )
    if c.experience_score < 0.5:
        weaknesses.append("Experience level below job requirements")
    if c.underqualified:
        weaknesses.append("Insufficient overall skill coverage for this role")
    if c.overqualified:
        weaknesses.append("May be overqualified; risk of low retention")

    decision = (c.decision or "").lower()
    if decision == "shortlist":
        recommendations.extend([
            "Schedule technical interview to validate key skills",
            "Assess cultural fit and team dynamics",
            "Verify depth of experience in matched skills",
        ])
    elif decision == "review":
        recommendations.extend([
            "Deep-dive review of work history and projects",
            f"Assess learning potential for missing skills: "
            f"{', '.join(c.missing_skills[:3])}",
            "Consider alternative roles that better match skill set",
        ])
    else:
        recommendations.extend([
            "Keep profile for future positions with different requirements",
            "Consider for junior roles if experience is the main gap",
        ])

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
    }
