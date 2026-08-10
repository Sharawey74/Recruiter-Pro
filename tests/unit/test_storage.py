"""
Unit tests for storage layer (models and database)
"""
import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path

from src.storage.models import (
    CVProfile,
    JobPosting,
    ScoreBreakdown,
    MatchDecision,
    MatchResult,
    MatchHistory,
    DecisionType,
    match_result_to_history
)
from src.storage.database import Database


class TestModels:
    """Test Pydantic models"""
    
    def test_cv_profile_creation(self):
        """Test CVProfile model"""
        cv = CVProfile(
            cv_id="cv_001",
            file_name="test.pdf",
            name="John Doe",
            email="john@example.com",
            skills=["Python", "FastAPI"],
            experience_years=5.0
        )
        
        assert cv.cv_id == "cv_001"
        assert cv.name == "John Doe"
        assert len(cv.skills) == 2
        assert cv.experience_years == 5.0
    
    def test_job_posting_creation(self):
        """Test JobPosting model"""
        job = JobPosting(
            job_id="job_001",
            title="Python Developer",
            category="engineering",
            company_name="Test Corp",
            location_city="Cairo",
            location_country="Egypt",
            remote_type="remote",
            employment_type="full-time",
            seniority_level="mid",
            description="Python developer role building web services.",
            required_skills=["Python", "Django"],
            min_experience_years=3.0,
            max_experience_years=6.0,
            posted_date="2026-07-01"
        )
        
        assert job.job_id == "job_001"
        assert job.title == "Python Developer"
        assert len(job.required_skills) == 2
    
    def test_score_breakdown_validation(self):
        """Test ScoreBreakdown score validation"""
        score = ScoreBreakdown(
            skill_score=0.8,
            experience_score=0.7,
            education_score=0.6,
            keyword_score=0.5,
            rule_based_score=0.75,
            ml_score=0.82,
            hybrid_score=0.78
        )
        
        assert 0.0 <= score.hybrid_score <= 1.0
        
        # Test validation enforces range
        with pytest.raises(Exception):  # Pydantic will raise ValidationError
            ScoreBreakdown(hybrid_score=1.5)
    
    def test_match_decision_creation(self):
        """Test MatchDecision model"""
        decision = MatchDecision(
            decision=DecisionType.SHORTLIST,
            confidence=0.9,
            reason="Strong skill match",
            recommendations=["Schedule interview"]
        )
        
        assert decision.decision == DecisionType.SHORTLIST
        assert decision.confidence == 0.9
        assert len(decision.recommendations) == 1
    
    def test_match_result_complete(self):
        """Test complete MatchResult creation"""
        score_breakdown = ScoreBreakdown(
            skill_score=0.85,
            experience_score=0.75,
            rule_based_score=0.80,
            hybrid_score=0.80,
            matched_skills=["Python", "FastAPI"],
            missing_skills=["Docker"]
        )
        
        decision = MatchDecision(
            decision=DecisionType.SHORTLIST,
            confidence=0.88,
            reason="Excellent technical fit"
        )
        
        match = MatchResult(
            match_id="match_001",
            cv_id="cv_001",
            job_id="job_001",
            candidate_name="John Doe",
            job_title="Python Developer",
            score_breakdown=score_breakdown,
            final_score=0.80,
            decision=decision,
            processing_time_ms=125.5
        )
        
        assert match.match_id == "match_001"
        assert match.final_score == 0.80
        assert match.decision.decision == DecisionType.SHORTLIST
    
    def test_match_result_to_history_conversion(self):
        """Test conversion from MatchResult to MatchHistory"""
        score_breakdown = ScoreBreakdown(
            skill_score=0.85,
            experience_score=0.75,
            education_score=0.65,
            keyword_score=0.55,
            rule_based_score=0.75,
            hybrid_score=0.80,
            matched_skills=["Python"],
            missing_skills=["Docker"]
        )
        
        decision = MatchDecision(
            decision=DecisionType.REVIEW,
            confidence=0.75,
            reason="Good but needs review"
        )
        
        match = MatchResult(
            match_id="match_002",
            cv_id="cv_002",
            job_id="job_002",
            job_title="DevOps Engineer",
            score_breakdown=score_breakdown,
            final_score=0.75,
            decision=decision
        )
        
        history = match_result_to_history(match)
        
        assert history.match_id == "match_002"
        assert history.final_score == 0.75
        assert history.decision == "review"
        assert json.loads(history.matched_skills) == ["Python"]


class TestDatabase:
    """Test database operations"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = Database(db_path)
        db.initialize_schema()
        
        yield db
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def sample_match(self):
        """Create sample match result"""
        score_breakdown = ScoreBreakdown(
            skill_score=0.9,
            experience_score=0.8,
            education_score=0.7,
            keyword_score=0.6,
            rule_based_score=0.85,
            ml_score=0.88,
            hybrid_score=0.86,
            matched_skills=["Python", "FastAPI", "PostgreSQL"],
            missing_skills=["Kubernetes"]
        )
        
        decision = MatchDecision(
            decision=DecisionType.SHORTLIST,
            confidence=0.92,
            reason="Exceptional candidate",
            explanation="Strong technical background with relevant experience"
        )
        
        return MatchResult(
            match_id="match_test_001",
            cv_id="cv_test_001",
            job_id="job_test_001",
            candidate_name="Jane Smith",
            job_title="Senior Python Developer",
            score_breakdown=score_breakdown,
            final_score=0.86,
            decision=decision,
            processing_time_ms=150.2
        )
    
    def test_initialize_schema(self, temp_db):
        """Test database schema creation"""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='match_history'
            """)
            assert cursor.fetchone() is not None
    
    def test_save_and_retrieve_match(self, temp_db, sample_match):
        """Test saving and retrieving match"""
        # Save
        record_id = temp_db.save_match(sample_match)
        assert record_id > 0
        
        # Retrieve
        retrieved = temp_db.get_match_by_id("match_test_001")
        assert retrieved is not None
        assert retrieved.match_id == "match_test_001"
        assert retrieved.candidate_name == "Jane Smith"
        assert retrieved.final_score == 0.86
        assert retrieved.decision == "shortlist"
    
    def test_get_matches_for_cv(self, temp_db, sample_match):
        """Test retrieving matches for specific CV"""
        temp_db.save_match(sample_match)
        
        matches = temp_db.get_matches_for_cv("cv_test_001")
        assert len(matches) == 1
        assert matches[0].cv_id == "cv_test_001"
    
    def test_get_matches_for_job(self, temp_db, sample_match):
        """Test retrieving matches for specific job"""
        temp_db.save_match(sample_match)
        
        matches = temp_db.get_matches_for_job("job_test_001")
        assert len(matches) == 1
        assert matches[0].job_id == "job_test_001"
    
    def test_get_top_matches(self, temp_db):
        """Test getting top matches with filtering"""
        # Create multiple matches
        for i in range(5):
            score_breakdown = ScoreBreakdown(
                skill_score=0.5 + (i * 0.1),
                experience_score=0.6,
                education_score=0.7,
                keyword_score=0.5,
                rule_based_score=0.6 + (i * 0.05),
                hybrid_score=0.6 + (i * 0.05)
            )
            
            decision_type = DecisionType.SHORTLIST if i >= 3 else DecisionType.REVIEW
            
            decision = MatchDecision(
                decision=decision_type,
                confidence=0.7 + (i * 0.05),
                reason=f"Test match {i}"
            )
            
            match = MatchResult(
                match_id=f"match_{i}",
                cv_id=f"cv_{i}",
                job_id=f"job_{i}",
                job_title=f"Job {i}",
                score_breakdown=score_breakdown,
                final_score=0.6 + (i * 0.05),
                decision=decision
            )
            
            temp_db.save_match(match)
        
        # Test filtering by decision
        shortlisted = temp_db.get_top_matches(decision="shortlist")
        assert len(shortlisted) == 2
        
        # Test filtering by score
        high_scores = temp_db.get_top_matches(min_score=0.75)
        assert len(high_scores) == 2
        
        # Test limit
        limited = temp_db.get_top_matches(limit=3)
        assert len(limited) == 3
    
    def test_get_statistics(self, temp_db, sample_match):
        """Test statistics calculation"""
        temp_db.save_match(sample_match)
        
        stats = temp_db.get_statistics()
        
        assert stats['total_matches'] == 1
        assert 'shortlist' in stats['decision_counts']
        assert stats['decision_counts']['shortlist'] == 1
        assert stats['averages']['avg_score'] == 0.86
    
    def test_delete_match(self, temp_db, sample_match):
        """Test deleting a match"""
        temp_db.save_match(sample_match)
        
        deleted = temp_db.delete_match("match_test_001")
        assert deleted is True
        
        retrieved = temp_db.get_match_by_id("match_test_001")
        assert retrieved is None
    
    def test_clear_all_matches(self, temp_db, sample_match):
        """Test clearing all matches"""
        temp_db.save_match(sample_match)
        
        count = temp_db.clear_all_matches()
        assert count == 1
        
        stats = temp_db.get_statistics()
        assert stats['total_matches'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
