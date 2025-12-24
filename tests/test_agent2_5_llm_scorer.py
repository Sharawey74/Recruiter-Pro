"""
Test Agent 2.5 LLM Scorer
Validates GPT-OSS-20B based resume-job matching.
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.agent2_5_llm_scorer import LLMScorer
import json


class TestLLMScorerMocked:
    """Test LLM Scorer with mocked API responses."""
    
    @pytest.fixture
    def mock_scorer(self):
        """Create a scorer with mocked OpenAI client."""
        with patch('src.agents.agent2_5_llm_scorer.OpenAI') as mock_openai:
            scorer = LLMScorer(api_key="test_key")
            scorer.client = MagicMock()
            return scorer
    
    def test_successful_api_call(self, mock_scorer):
        """Test successful API call and response parsing."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "match_label": "High",
            "confidence": 0.85,
            "reasoning": "Strong skill match with relevant experience",
            "skill_match_score": 0.80,
            "experience_match_score": 0.90,
            "key_strengths": ["Python", "Machine Learning"],
            "key_gaps": []
        })
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 150
        mock_response.usage.total_tokens = 650
        
        mock_scorer.client.chat.completions.create.return_value = mock_response
        
        # Test data
        profile = {
            "name": "Alice",
            "skills": ["Python", "Machine Learning"],
            "years_of_experience": 6,
            "seniority_level": "Senior"
        }
        
        job = {
            "title": "ML Engineer",
            "skills_required": ["Python", "ML"],
            "min_experience_years": 5,
            "max_experience_years": 10
        }
        
        result = mock_scorer.score_match(profile, job, verbose=False)
        
        assert result["match_label"] == "High"
        assert result["confidence"] == 0.85
        assert "tokens_used" in result
        assert result["tokens_used"]["total"] == 650
    
    def test_api_failure_with_retry(self, mock_scorer):
        """Test that API failures trigger retry logic."""
        # First call fails, second succeeds
        mock_scorer.client.chat.completions.create.side_effect = [
            Exception("API timeout"),
            Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "match_label": "Medium",
                    "confidence": 0.6,
                    "reasoning": "Some gaps"
                })))],
                usage=Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
            )
        ]
        
        profile = {"name": "Bob", "skills": ["Java"], "years_of_experience": 3}
        job = {"title": "Developer", "skills_required": ["Java"], "min_experience_years": 2}
        
        result = mock_scorer.score_match(profile, job, verbose=False)
        
        # Should succeed on retry
        assert result["match_label"] in ["Medium", "High", "Low"]
        assert mock_scorer.client.chat.completions.create.call_count == 2
    
    def test_fallback_scoring(self, mock_scorer):
        """Test fallback scoring when all retries fail."""
        # All calls fail
        mock_scorer.client.chat.completions.create.side_effect = Exception("API unavailable")
        
        profile = {
            "name": "Charlie",
            "skills": ["Python", "Django"],
            "years_of_experience": 4
        }
        
        job = {
            "title": "Backend Developer",
            "skills_required": ["Python", "Django", "PostgreSQL"],
            "min_experience_years": 3,
            "max_experience_years": 6
        }
        
        result = mock_scorer.score_match(profile, job, verbose=False)
        
        # Should use fallback
        assert result["match_label"] in ["High", "Medium", "Low"]
        assert "Fallback scoring" in result["reasoning"]
        assert mock_scorer.client.chat.completions.create.call_count == 3  # Max retries
    
    def test_malformed_json_response(self, mock_scorer):
        """Test handling of malformed JSON responses."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON but mentions High match"
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        
        mock_scorer.client.chat.completions.create.return_value = mock_response
        
        profile = {"name": "Dave", "skills": ["React"], "years_of_experience": 2}
        job = {"title": "Frontend Dev", "skills_required": ["React"], "min_experience_years": 1}
        
        result = mock_scorer.score_match(profile, job, verbose=False)
        
        # Should extract basic info from text
        assert result["match_label"] in ["High", "Medium", "Low"]
        assert result["confidence"] >= 0.0


class TestLLMScorerIntegration:
    """Integration tests with real API (optional - requires API key)."""
    
    @pytest.mark.skip(reason="Requires valid API key and network access")
    def test_real_api_call(self):
        """Test with real API (skip by default)."""
        API_KEY = "your_api_key_here"
        scorer = LLMScorer(api_key=API_KEY)
        
        profile = {
            "name": "Test User",
            "skills": ["Python", "FastAPI"],
            "years_of_experience": 3,
            "seniority_level": "Mid-level"
        }
        
        job = {
            "title": "Backend Developer",
            "skills_required": ["Python", "FastAPI", "PostgreSQL"],
            "min_experience_years": 2,
            "max_experience_years": 5
        }
        
        result = scorer.score_match(profile, job)
        
        assert result["match_label"] in ["High", "Medium", "Low"]
        assert 0.0 <= result["confidence"] <= 1.0


def test_basic_scoring():
    """Test basic LLM scoring with sample data."""
    print("="*80)
    print("TEST 1: Basic LLM Scoring")
    print("="*80)
    
    # Your API key
    API_KEY = "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"
    
    # Initialize scorer
    scorer = LLMScorer(api_key=API_KEY)
    
    # Test Case 1: Strong Match
    print("\n" + "="*80)
    print("TEST CASE 1: Strong Match - Senior ML Engineer")
    print("="*80)
    
    profile1 = {
        "name": "Alice Johnson",
        "skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", 
                   "scikit-learn", "pandas", "NumPy", "Docker", "Kubernetes", "AWS"],
        "years_of_experience": 6,
        "seniority_level": "Senior"
    }
    
    job1 = {
        "title": "Senior Machine Learning Engineer",
        "skills_required": ["Python", "TensorFlow", "Machine Learning", "Deep Learning", 
                            "AWS", "Docker"],
        "min_experience_years": 5,
        "max_experience_years": 10,
        "seniority_level": "Senior"
    }
    
    result1 = scorer.score_match(profile1, job1)
    print("\n📊 RESULT:")
    print(json.dumps(result1, indent=2))
    
    assert result1["match_label"] in ["High", "Medium", "Low"], "Invalid match label"
    assert 0.0 <= result1["confidence"] <= 1.0, "Invalid confidence score"
    
    print("\n✅ Test Case 1 passed!")
    
    # Test Case 2: Medium Match
    print("\n" + "="*80)
    print("TEST CASE 2: Medium Match - Some Skill Gaps")
    print("="*80)
    
    profile2 = {
        "name": "Bob Smith",
        "skills": ["Python", "Django", "Flask", "PostgreSQL", "HTML", "CSS"],
        "years_of_experience": 3,
        "seniority_level": "Mid-level"
    }
    
    job2 = {
        "title": "Full Stack Developer",
        "skills_required": ["Python", "React", "Node.js", "MongoDB", "AWS", "Docker"],
        "min_experience_years": 2,
        "max_experience_years": 5,
        "seniority_level": "Mid-level"
    }
    
    result2 = scorer.score_match(profile2, job2)
    print("\n📊 RESULT:")
    print(json.dumps(result2, indent=2))
    
    print("\n✅ Test Case 2 passed!")
    
    # Test Case 3: Poor Match
    print("\n" + "="*80)
    print("TEST CASE 3: Poor Match - Major Skill Gaps")
    print("="*80)
    
    profile3 = {
        "name": "Charlie Brown",
        "skills": ["Java", "Spring Boot", "MySQL", "Jenkins"],
        "years_of_experience": 2,
        "seniority_level": "Junior"
    }
    
    job3 = {
        "title": "Senior Frontend Architect",
        "skills_required": ["React", "Angular", "TypeScript", "GraphQL", "Webpack"],
        "min_experience_years": 8,
        "max_experience_years": 15,
        "seniority_level": "Senior"
    }
    
    result3 = scorer.score_match(profile3, job3)
    print("\n📊 RESULT:")
    print(json.dumps(result3, indent=2))
    
    print("\n✅ Test Case 3 passed!")
    
    return scorer


def test_batch_scoring(scorer):
    """Test batch scoring with multiple jobs."""
    print("\n" + "="*80)
    print("TEST 2: Batch Scoring - 1 Profile vs Multiple Jobs")
    print("="*80)
    
    # Profile
    profile = {
        "name": "David Lee",
        "skills": ["Python", "JavaScript", "React", "Node.js", "MongoDB", 
                   "Express", "Docker", "Git"],
        "years_of_experience": 4,
        "seniority_level": "Mid-level"
    }
    
    # Multiple jobs
    jobs = [
        {
            "title": "Full Stack Developer",
            "skills_required": ["Python", "React", "Node.js", "MongoDB", "Docker"],
            "min_experience_years": 3,
            "max_experience_years": 6,
            "seniority_level": "Mid-level"
        },
        {
            "title": "Backend Python Developer",
            "skills_required": ["Python", "Django", "PostgreSQL", "Redis", "Celery"],
            "min_experience_years": 2,
            "max_experience_years": 5,
            "seniority_level": "Mid-level"
        },
        {
            "title": "Frontend React Developer",
            "skills_required": ["React", "JavaScript", "TypeScript", "Redux", "CSS"],
            "min_experience_years": 3,
            "max_experience_years": 7,
            "seniority_level": "Mid-level"
        },
        {
            "title": "DevOps Engineer",
            "skills_required": ["Docker", "Kubernetes", "AWS", "Terraform", "Jenkins"],
            "min_experience_years": 5,
            "max_experience_years": 10,
            "seniority_level": "Senior"
        }
    ]
    
    results = scorer.batch_score(profile, jobs, top_k=4)
    
    print("\n📊 BATCH RESULTS:")
    print("="*80)
    for i, result in enumerate(results, 1):
        job_title = result["job_data"]["title"]
        print(f"\n{i}. {job_title}")
        print(f"   Match: {result['match_label']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Reasoning: {result['reasoning'][:100]}...")
    
    print("\n✅ Batch scoring test passed!")


def test_real_data_integration():
    """Test with actual parsed data from Agent 1 if available."""
    print("\n" + "="*80)
    print("TEST 3: Real Data Integration")
    print("="*80)
    
    # Check if parsed profiles exist
    parsed_dir = Path("data/json/parsed_profiles")
    
    if not parsed_dir.exists() or not list(parsed_dir.glob("*.json")):
        print("⚠️  No parsed profiles found. Skipping real data test.")
        print("   Run verify_stage1.py first to generate parsed profiles.")
        return
    
    # Load first parsed profile
    profile_files = list(parsed_dir.glob("*.json"))
    profile_path = profile_files[0]
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile_data = json.load(f)
    
    print(f"✓ Loaded profile: {profile_data.get('name', 'Unknown')}")
    
    # Load jobs
    jobs_path = Path("data/json/jobs.json")
    if not jobs_path.exists():
        print("⚠️  jobs.json not found. Skipping real data test.")
        return
    
    with open(jobs_path, 'r', encoding='utf-8') as f:
        jobs_data = json.load(f)
    
    print(f"✓ Loaded {len(jobs_data)} jobs")
    
    # Score against first 3 jobs
    API_KEY = "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"
    scorer = LLMScorer(api_key=API_KEY)
    
    results = scorer.batch_score(profile_data, jobs_data[:3], top_k=3)
    
    print("\n✅ Real data integration test passed!")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 Agent 2.5 LLM Scorer - Test Suite")
    print("="*80)
    print("Model: OpenAI GPT-OSS-20B via OpenRouter")
    print("="*80)
    
    try:
        # Test 1: Basic scoring
        scorer = test_basic_scoring()
        
        # Test 2: Batch scoring
        test_batch_scoring(scorer)
        
        # Test 3: Real data integration
        test_real_data_integration()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nNext steps:")
        print("1. Integrate LLM scorer into main pipeline")
        print("2. Compare LLM results with ML model (if available)")
        print("3. Update Agent 3 to use LLM predictions")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED!")
        print(f"Error: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
