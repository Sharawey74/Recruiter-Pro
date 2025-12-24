import pytest
from src.agents.agent3 import JobMatcher
from src.backend import HRBackend

class TestAdvancedMatching:
    
    def test_method_a_job_filtering(self):
        """Test that jobs with fewer than 3 skills are filtered out"""
        backend = HRBackend()
        raw_jobs = [
            {"Job Id": "1", "Job Title": "Bad Job", "skills": "Python", "Qualifications": "None"},
            {"Job Id": "2", "Job Title": "Good Job", "skills": "Python|Java|Docker", "Qualifications": "Good"}
        ]
        
        normalized = backend._normalize_jobs(raw_jobs)
        
        assert len(normalized) == 1
        assert normalized[0]['job_id'] == "2"
        assert len(normalized[0]['required_skills']) == 3

    def test_method_c_log_scaling(self):
        """Test that 100% match on few skills yields lower score than many skills"""
        matcher = JobMatcher()
        
        # Case 1: 1 matches 1 (100% ratio, but low confidence)
        cand_skills_1 = ["python"]
        job_skills_1 = ["python"]
        score_1, _, _ = matcher._score_skills(cand_skills_1, job_skills_1)
        
        # Case 2: 3 matches 3 (100% ratio, high confidence)
        cand_skills_3 = ["python", "java", "docker"]
        job_skills_3 = ["python", "java", "docker"]
        score_3, _, _ = matcher._score_skills(cand_skills_3, job_skills_3)
        
        print(f"Score 1 (1 skill): {score_1}")
        print(f"Score 3 (3 skills): {score_3}")
        
        assert score_1 < score_3, "Method C failed: 1 skill match should match score lower than 3 skills match"
        assert score_3 == 1.0, "3 skills match should be perfect score"
        assert score_1 <= 0.34, "1 skill match should be roughly 1/3 scaling factor"

    def test_method_d_category_penalty(self):
        """Test that Manager jobs penalize non-manager candidates"""
        matcher = JobMatcher()
        
        candidate = {
            "skills": ["python", "java"], # Engineering skills
            "experience_years": 5,
            "education": [],
            "name": "Dev"
        }
        
        # Engineering Job
        job_eng = {
            "job_title": "Senior Python Developer",
            "required_skills": ["python", "java"],
            "experience_required": {"min_years": 5},
            "description": "Code stuff"
        }
        
        # Manager Job
        job_mgr = {
            "job_title": "Engineering Manager",
            "required_skills": ["python", "java"], # Same skills required!
            "experience_required": {"min_years": 5},
            "description": "Manage stuff"
        }
        
        # Run matching
        # We need to call match_and_decide to see the penalty applied to final_score
        # But match_and_decide takes a list
        
        results_eng = matcher.match_and_decide(candidate, [job_eng])
        results_mgr = matcher.match_and_decide(candidate, [job_mgr])
        
        score_eng = results_eng[0]['score']
        score_mgr = results_mgr[0]['score']
        
        print(f"Eng Score: {score_eng}, Mgr Score: {score_mgr}")
        
        # Mgr score should be lower due to 0.8 penalty
        assert score_mgr < score_eng, "Method D failed: Manager job should have penalty for non-manager candidate"
