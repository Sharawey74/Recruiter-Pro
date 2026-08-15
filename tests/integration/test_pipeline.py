"""
Integration Tests for 4-Agent Pipeline
Tests the complete workflow from CV file to match decision
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.storage.models import CVProfile, JobPosting, DecisionType
from src.agents.agent3_scorer import HybridScoringAgent
from src.agents.agent4_factory import get_explainer_agent
from src.agents.pipeline import MatchingPipeline


class TestAgent3Scorer:
    """Test Agent 3 (Hybrid Scorer)"""
    
    @pytest.fixture
    def agent3(self):
        return HybridScoringAgent()
    
    @pytest.fixture
    def sample_cv(self):
        return CVProfile(
            cv_id="test_cv_001",
            file_name="test.pdf",
            name="John Doe",
            email="john@example.com",
            skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            experience_years=5.0,
            education="Bachelor's Degree in Computer Science",
            raw_text="Experienced Python developer with 5 years of backend development..."
        )
    
    @pytest.fixture
    def sample_job(self):
        return JobPosting(
            job_id="test_job_001",
            title="Senior Python Developer",
            category="engineering",
            company_name="Test Corp",
            location_city="Cairo",
            location_country="Egypt",
            remote_type="remote",
            employment_type="full-time",
            seniority_level="senior",
            required_skills=["Python", "FastAPI", "SQL"],
            preferred_skills=["Docker", "Kubernetes", "AWS"],
            min_experience_years=3.0,
            max_experience_years=8.0,
            education_level="Bachelor's Degree",
            posted_date="2026-07-01",
            description="Looking for senior Python developer with FastAPI experience..."
        )
    
    def test_score_calculation(self, agent3, sample_cv, sample_job):
        """Test basic scoring functionality"""
        score = agent3.score_match(sample_cv, sample_job)
        
        assert 0.0 <= score.hybrid_score <= 1.0
        assert 0.0 <= score.skill_score <= 1.0
        assert 0.0 <= score.experience_score <= 1.0
        assert score.rule_based_score > 0
    
    def test_skill_matching(self, agent3, sample_cv, sample_job):
        """Test skill matching logic"""
        score = agent3.score_match(sample_cv, sample_job)
        
        # Should match several skills (at least 2-3 out of Python, FastAPI, Docker, PostgreSQL)
        assert len(score.matched_skills) >= 2
        # Check if python-related skills are matched (normalized form).
        #
        # The 'programming' alternative was removed here: it accepted
        # 'programming_languages', the family name A0 produced, which meant
        # this test passed *because of* the bug rather than despite it. That
        # clause is how A0 survived. Guarded now by
        # tests/unit/test_skill_normalization.py.
        matched_lower = [s.lower() for s in score.matched_skills]
        assert any('python' in s or 'fastapi' in s for s in matched_lower)
        
        # Should be missing some skills
        assert len(score.missing_skills) >= 1
    
    def test_experience_scoring(self, agent3, sample_cv, sample_job):
        """Test experience scoring"""
        score = agent3.score_match(sample_cv, sample_job)
        
        # 5 years vs 3 required = good match
        assert score.experience_score >= 0.8
    
    def test_overqualified_detection(self, agent3, sample_cv, sample_job):
        """Test overqualification detection"""
        # Make candidate significantly overqualified
        overqualified_cv = CVProfile(
            **{**sample_cv.model_dump(), 'experience_years': 15.0}
        )
        
        score = agent3.score_match(overqualified_cv, sample_job)
        
        # Should flag as overqualified (15 years >> 3 required)
        assert score.overqualified is True
    
    def test_underqualified_detection(self, agent3, sample_cv, sample_job):
        """Test underqualification detection"""
        # Remove most skills
        underqualified_cv = CVProfile(
            **{**sample_cv.model_dump(), 'skills': ["Python"]}
        )
        
        score = agent3.score_match(underqualified_cv, sample_job)
        
        # Should flag as underqualified
        assert score.underqualified is True


class TestAgent4Explainer:
    """Test Agent 4 (LLM Explainer)"""
    
    @pytest.fixture
    def agent4(self):
        return get_explainer_agent()
    
    @pytest.fixture
    def sample_match_result(self):
        from src.storage.models import MatchResult, ScoreBreakdown, MatchDecision
        
        score = ScoreBreakdown(
            skill_score=0.85,
            experience_score=0.90,
            education_score=0.95,
            keyword_score=0.75,
            rule_based_score=0.87,
            ml_score=0.88,
            hybrid_score=0.875,
            matched_skills=["Python", "FastAPI", "PostgreSQL"],
            missing_skills=["Kubernetes", "AWS"]
        )
        
        decision = MatchDecision(
            decision=DecisionType.SHORTLIST,
            confidence=0.92,
            reason="Excellent technical fit with strong experience"
        )
        
        return MatchResult(
            match_id="test_match_001",
            cv_id="test_cv_001",
            job_id="test_job_001",
            candidate_name="Jane Smith",
            job_title="Senior Python Developer",
            score_breakdown=score,
            final_score=0.875,
            decision=decision,
            processing_time_ms=150.0
        )
    
    def test_explanation_generation(self, agent4, sample_match_result):
        """Test explanation generation"""
        explanation = agent4.generate_explanation(sample_match_result)
        
        assert explanation is not None
        assert len(explanation) > 50
        assert isinstance(explanation, str)
    
    def test_explanation_contains_key_info(self, agent4, sample_match_result):
        """Test that explanation contains key information"""
        explanation = agent4.generate_explanation(sample_match_result)
        
        # Should mention candidate or position
        assert "candidate" in explanation.lower() or "position" in explanation.lower()
        
        # Should be professional (no profanity, reasonable length)
        assert len(explanation) < 2000
    
    def test_structured_insights(self, agent4, sample_match_result):
        """Test structured insights generation"""
        insights = agent4.generate_structured_insights(sample_match_result)
        
        assert 'strengths' in insights
        assert 'weaknesses' in insights
        assert 'recommendations' in insights
        
        assert len(insights['strengths']) > 0
        assert len(insights['recommendations']) > 0


class TestMatchingPipeline:
    """Test complete pipeline integration"""
    
    @pytest.fixture
    def pipeline(self):
        # Don't save to DB during tests
        return MatchingPipeline(save_to_db=False)
    
    @pytest.fixture
    def test_cv_file(self):
        """Create a temporary test CV file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            John Doe
            Email: john.doe@example.com
            Phone: +1-555-0123
            
            EXPERIENCE:
            Senior Python Developer at Tech Corp (2019-2024) - 5 years
            - Developed REST APIs using FastAPI
            - Worked with PostgreSQL databases
            - Deployed applications with Docker
            
            SKILLS:
            Python, FastAPI, PostgreSQL, Docker, Git, Linux
            
            EDUCATION:
            Bachelor of Science in Computer Science
            Tech University, 2018
            """)
            return f.name
    
    @pytest.fixture
    def sample_job(self):
        return JobPosting(
            job_id="test_job_pipeline",
            title="Senior Python Developer",
            category="engineering",
            company_name="Test Corp",
            location_city="Cairo",
            location_country="Egypt",
            remote_type="remote",
            employment_type="full-time",
            seniority_level="senior",
            required_skills=["Python", "FastAPI", "SQL"],
            preferred_skills=["Docker", "AWS"],
            min_experience_years=3.0,
            max_experience_years=8.0,
            education_level="Bachelor's Degree",
            posted_date="2026-07-01",
            description="Senior Python role with FastAPI and SQL responsibilities."
        )
    
    def test_pipeline_initialization(self, pipeline):
        """Test that pipeline initializes all agents"""
        assert pipeline.agent1 is not None
        assert pipeline.agent2 is not None
        assert pipeline.agent3 is not None
        assert pipeline.agent4 is not None
    
    def test_full_pipeline_execution(self, pipeline, test_cv_file, sample_job):
        """Test complete pipeline from file to decision"""
        result = pipeline.process_cv_for_job(
            cv_file_path=test_cv_file,
            job=sample_job,
            generate_explanation=False  # Skip LLM for faster tests
        )
        
        # Validate result structure
        assert result.match_id is not None
        assert result.cv_id is not None
        assert result.job_id == sample_job.job_id
        assert result.final_score >= 0.0
        assert result.final_score <= 1.0
        assert result.decision.decision in [DecisionType.SHORTLIST, DecisionType.REVIEW, DecisionType.REJECT]
        
        # Cleanup
        Path(test_cv_file).unlink()
    
    def test_pipeline_scoring_accuracy(self, pipeline, test_cv_file, sample_job):
        """Test that pipeline produces reasonable scores"""
        result = pipeline.process_cv_for_job(
            cv_file_path=test_cv_file,
            job=sample_job,
            generate_explanation=False
        )
        
        # CV has Python, FastAPI, PostgreSQL, Docker - good match
        assert result.final_score >= 0.6  # Should be at least 60%
        assert len(result.score_breakdown.matched_skills) >= 3
        
        # Cleanup
        Path(test_cv_file).unlink()
    
    def test_decision_making(self, pipeline, test_cv_file, sample_job):
        """Test decision logic"""
        result = pipeline.process_cv_for_job(
            cv_file_path=test_cv_file,
            job=sample_job,
            generate_explanation=False
        )
        
        # Strong match should be SHORTLIST or REVIEW
        if result.final_score >= 0.75:
            assert result.decision.decision == DecisionType.SHORTLIST
        elif result.final_score >= 0.50:
            assert result.decision.decision == DecisionType.REVIEW
        else:
            assert result.decision.decision == DecisionType.REJECT
        
        # Cleanup
        Path(test_cv_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
