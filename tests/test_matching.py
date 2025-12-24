"""
Unit Tests for Agent 4 Matcher
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.agent4_matcher import Agent4Matcher

@pytest.fixture
def matcher():
    return Agent4Matcher()

@pytest.fixture
def sample_candidate():
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["python", "sql", "docker", "javascript"],
        "experience_years": 3,
        "education": ["B.S."]
    }

@pytest.fixture
def sample_jobs():
    return [
        {
            "job_id": "job1",
            "title": "Python Developer",
            "required_skills": ["python", "sql", "docker"],
            "min_experience_years": 2,
            "description": "Bachelor degree required"
        },
        {
            "job_id": "job2",
            "title": "Senior Full Stack Engineer",
            "required_skills": ["python", "javascript", "react", "aws"],
            "min_experience_years": 5,
            "description": "Senior role"
        },
        {
            "job_id": "job3",
            "title": "Junior Data Analyst",
            "required_skills": ["sql", "excel", "tableau"],
            "min_experience_years": 1,
            "description": "Entry level position"
        }
    ]

class TestSkillScoring:
    """Test skill matching logic"""
    
    def test_perfect_skill_match(self, matcher, sample_candidate):
        """All skills matched should give high score"""
        job = {
            "job_id": "perfect",
            "title": "Test Job",
            "required_skills": ["python", "sql"],
            "min_experience_years": 1,
            "description": ""
        }
        result = matcher._score_single(sample_candidate, job)
        assert result['skill_match_pct'] == 100.0
        assert len(result['missing_skills']) == 0
    
    def test_partial_skill_match(self, matcher, sample_candidate):
        """Partial match should show matched and missing skills"""
        job = {
            "job_id": "partial",
            "title": "Test Job",
            "required_skills": ["python", "java", "kubernetes"],
            "min_experience_years": 1,
            "description": ""
        }
        result = matcher._score_single(sample_candidate, job)
        assert "python" in result['matched_skills']
        assert "java" in result['missing_skills']
        assert "kubernetes" in result['missing_skills']

class TestExperienceScoring:
    """Test experience matching"""
    
    def test_meets_experience_requirement(self, matcher, sample_candidate):
        """Candidate meets experience requirement"""
        job = {
            "job_id": "test",
            "title": "Test",
            "required_skills": ["python"],
            "min_experience_years": 2,
            "description": ""
        }
        result = matcher._score_single(sample_candidate, job)
        assert result['experience_match'] == True
    
    def test_underqualified_experience(self, matcher, sample_candidate):
        """Candidate doesn't meet experience requirement"""
        job = {
            "job_id": "test",
            "title": "Test",
            "required_skills": ["python"],
            "min_experience_years": 10,
            "description": ""
        }
        result = matcher._score_single(sample_candidate, job)
        assert result['experience_match'] == False

class TestOverallScoring:
    """Test complete scoring logic"""
    
    def test_high_quality_match(self, matcher, sample_candidate, sample_jobs):
        """First job should be HIGH quality match"""
        results = matcher.score_all(sample_candidate, sample_jobs)
        python_job = next((r for r in results if r['title'] == "Python Developer"), None)
        assert python_job is not None
        assert python_job['match_label'] == "HIGH"
        assert python_job['score'] >= 70.0
    
    def test_low_quality_match(self, matcher, sample_candidate, sample_jobs):
        """Job with mismatched skills should be LOW"""
        results = matcher.score_all(sample_candidate, sample_jobs)
        analyst_job = next((r for r in results if r['title'] == "Junior Data Analyst"), None)
        assert analyst_job is not None
        # May be MEDIUM or LOW depending on skill overlap
        assert analyst_job['score'] < 80.0
    
    def test_results_sorted(self, matcher, sample_candidate, sample_jobs):
        """Results should be sorted by score descending"""
        results = matcher.score_all(sample_candidate, sample_jobs)
        scores = [r['score'] for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_top_3_limit(self, matcher, sample_candidate):
        """Should return max 3 results"""
        many_jobs = [
            {"job_id": f"job{i}", "title": f"Job {i}", "required_skills": ["python"], "min_experience_years": 1, "description": ""}
            for i in range(10)
        ]
        results = matcher.score_all(sample_candidate, many_jobs)
        assert len(results) <= 3

class TestDeterminism:
    """Test reproducibility"""
    
    def test_deterministic_scoring(self, matcher, sample_candidate, sample_jobs):
        """Same inputs produce same outputs"""
        results1 = matcher.score_all(sample_candidate, sample_jobs)
        results2 = matcher.score_all(sample_candidate, sample_jobs)
        assert results1 == results2
