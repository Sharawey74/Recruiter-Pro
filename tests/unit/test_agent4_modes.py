"""
Test Agent 4 modes: Direct HTTP vs LangChain
Run with: pytest tests/test_agent4_modes.py -v -s
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
            extra_skills=["Java", "Spring Boot"]
        ),
        final_score=0.82,
        decision=MatchDecision(
            decision=DecisionType.SHORTLIST,
            confidence=0.85,
            reason="Strong technical fit",
            strengths=["Solid Python skills", "Cloud experience"],
            red_flags=[],
            recommendations=["Technical interview", "System design assessment"]
        ),
        timestamp=datetime.now()
    )


def test_direct_http_mode(sample_match):
    """Test Direct HTTP mode (fast)"""
    print("\n" + "="*60)
    print("TEST 1: Direct HTTP Mode (Fast)")
    print("="*60)
    
    agent = get_explainer_agent(use_langchain=False)
    explanation = agent.generate_explanation(sample_match)
    
    print(f"\nAgent Type: {type(agent).__name__}")
    print(f"Explanation Length: {len(explanation)} characters")
    print(f"\nExplanation:\n{explanation}")
    
    assert len(explanation) > 50, "Explanation too short"
    assert "Python" in explanation, "Should mention matched skills"
    assert "Developer" in explanation, "Should mention job title"
    
    print("\n✅ Direct HTTP mode test PASSED")


def test_langchain_mode(sample_match):
    """Test LangChain mode (advanced)"""
    print("\n" + "="*60)
    print("TEST 2: LangChain Mode (Advanced)")
    print("="*60)
    
    try:
        agent = get_explainer_agent(use_langchain=True)
        print(f"Agent Type: {type(agent).__name__}")
        
        explanation = agent.generate_explanation(sample_match)
        
        print(f"Explanation Length: {len(explanation)} characters")
        print(f"\nExplanation:\n{explanation}")
        
        assert len(explanation) > 50, "Explanation too short"
        assert any(skill in explanation for skill in ["Python", "Django", "PostgreSQL"]), \
            "Should mention matched skills"
        
        print("\n✅ LangChain mode test PASSED")
        
    except ImportError as e:
        pytest.skip(f"LangChain not installed: {e}")


def test_factory_fallback(sample_match):
    """Test graceful fallback from LangChain to Direct HTTP"""
    print("\n" + "="*60)
    print("TEST 3: Factory Fallback Mechanism")
    print("="*60)
    
    # Even if LangChain is requested but fails, should work
    agent = get_explainer_agent(use_langchain=True)
    explanation = agent.generate_explanation(sample_match)
    
    print(f"Agent Type: {type(agent).__name__}")
    print(f"Explanation:\n{explanation}")
    
    assert explanation is not None
    assert len(explanation) > 50
    
    print("\n✅ Fallback test PASSED")


def test_structured_insights(sample_match):
    """Test structured insights generation"""
    print("\n" + "="*60)
    print("TEST 4: Structured Insights (Backward Compatibility)")
    print("="*60)
    
    agent = get_explainer_agent(use_langchain=False)
    insights = agent.generate_structured_insights(sample_match)
    
    print("\nInsights:")
    print(f"  Strengths: {insights['strengths']}")
    print(f"  Weaknesses: {insights['weaknesses']}")
    print(f"  Recommendations: {insights['recommendations']}")
    
    assert 'strengths' in insights
    assert 'weaknesses' in insights
    assert 'recommendations' in insights
    assert len(insights['strengths']) > 0
    
    print("\n✅ Structured insights test PASSED")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AGENT 4 MODE TESTING SUITE")
    print("="*60)
    pytest.main([__file__, "-v", "-s"])
