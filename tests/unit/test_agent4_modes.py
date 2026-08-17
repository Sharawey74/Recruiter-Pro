"""
Agent 4 end-to-end: the factory builds an explainer and it produces text.

This file used to test "Direct HTTP vs LangChain" -- two modes that both ended
at the same Ollama server. The LangChain one is gone, so what is left is the
part that was always the point: whatever provider is configured, a MatchResult
goes in and a usable explanation comes out. Provider selection itself is
covered in test_explaining_providers.py.
"""

import pytest
from src.agents.agent4_factory import get_explainer_agent
from src.storage.models import MatchResult, ScoreBreakdown, MatchDecision, DecisionType
from datetime import datetime


@pytest.fixture
def sample_match():
    """Create sample match result for testing"""
    return MatchResult(
        match_id="test_123",
        cv_id="cv_456",
        job_id="job_789",
        candidate_name="John Doe",
        job_title="Python Developer",
        score_breakdown=ScoreBreakdown(
            skill_score=0.85,
            experience_score=0.75,
            education_score=0.80,
            keyword_score=0.70,
            rule_based_score=0.80,
            hybrid_score=0.82,
            matched_skills=["Python", "Django", "PostgreSQL", "Docker", "AWS"],
            missing_skills=["Kubernetes", "Redis"],
            extra_skills=["Java", "Spring Boot"],
        ),
        final_score=0.82,
        decision=MatchDecision(
            decision=DecisionType.SHORTLIST,
            confidence=0.85,
            reason="Strong technical fit",
            strengths=["Solid Python skills", "Cloud experience"],
            red_flags=[],
            recommendations=["Technical interview", "System design assessment"],
        ),
        timestamp=datetime.now(),
    )


def test_configured_provider_explains(sample_match):
    """The configured provider turns a MatchResult into an explanation."""
    agent = get_explainer_agent()
    explanation = agent.generate_explanation(sample_match)

    assert len(explanation) > 50, "Explanation too short"
    assert "Python" in explanation, "Should mention matched skills"
    assert "Developer" in explanation, "Should mention job title"


def test_an_unresolvable_provider_still_explains(sample_match):
    """
    A provider name the factory cannot build must not cost the caller an
    explanation. This was the "graceful fallback from LangChain" test; the
    property it asserted is about the factory, not about LangChain, so it
    outlived the provider that prompted it.
    """
    agent = get_explainer_agent(provider="nonsense")

    assert agent.provider.name == "rule_based"
    assert len(agent.generate_explanation(sample_match)) > 50


def test_structured_insights(sample_match):
    """Strengths, weaknesses and recommendations are read off the breakdown."""
    agent = get_explainer_agent()
    insights = agent.generate_structured_insights(sample_match)

    assert "strengths" in insights
    assert "weaknesses" in insights
    assert "recommendations" in insights
    assert len(insights["strengths"]) > 0


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AGENT 4 MODE TESTING SUITE")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
