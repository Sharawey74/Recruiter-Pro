"""
One prompt, shared by every model-backed provider.

Ollama, OpenRouter and LangChain were each building their own version of the
same instruction. Three copies of a prompt drift, and then two providers
silently produce differently-shaped explanations for identical input -- which
looks like a model difference and is not.
"""

from __future__ import annotations

from .protocol import ExplanationContext

SYSTEM = (
    "You are an HR assistant analyzing a candidate-job match. "
    "Be professional and factual. Never invent facts that are not in the data given."
)

# Model output is not trusted. Anything shorter than this is treated as a
# failure and falls back, rather than being returned as an explanation.
MIN_USABLE_LENGTH = 50


def build(c: ExplanationContext) -> str:
    """Render the user half of the prompt for one match."""
    matched = ", ".join(c.matched_skills[:5]) if c.matched_skills else "None"
    missing = ", ".join(c.missing_skills[:5]) if c.missing_skills else "None"

    flags = []
    if c.overqualified:
        flags.append("Overqualified")
    if c.underqualified:
        flags.append("Underqualified")
    flag_line = ", ".join(flags) if flags else "None"

    return f"""**Match Details:**
- Candidate: {c.candidate_name}
- Position: {c.job_title}
- Final Score: {c.final_score:.0%}
- Decision: {c.decision.upper()}
- Confidence: {c.confidence:.0%}

**Score Breakdown:**
- Skill Match: {c.skill_score:.0%} ({len(c.matched_skills)} matched, {len(c.missing_skills)} missing)
- Experience: {c.experience_score:.0%}
- Education: {c.education_score:.0%}
- Keywords: {c.keyword_score:.0%}

**Matched Skills:** {matched}
**Missing Skills:** {missing}
**Flags:** {flag_line}

**Instructions:**
Write a concise 2-3 paragraph explanation that:
1. Summarizes why this decision was made
2. Highlights 2-3 key strengths based on matched skills and scores
3. Notes 1-2 concerns based on missing skills or gaps
4. Provides 1-2 actionable recommendations for HR

Keep it professional, factual, and under 200 words. Do NOT invent facts not in \
the data above."""
