import pytest
from src.agents.agent3 import JobMatcher

class TestSkillLogic:
    
    def test_strict_thresholds(self):
        """
        Verify:
        - < 50% Skill Match -> REJECT
        - 50-84% Skill Match -> REVIEW
        - >= 85% Skill Match -> SHORTLIST
        """
        matcher = JobMatcher()
        
        # Helper to run decision logic
        # We can test _make_decision directly since it's the gatekeeper
        
        # Case 1: Low Score
        assert matcher._make_decision(0.9, 0.49) == "REJECT", "Skill < 50% should be REJECT regardless of final score"
        
        # Case 2: Mid Score
        assert matcher._make_decision(0.9, 0.70) == "REVIEW", "Skill 70% should be REVIEW"
        
        # Case 3: High Score
        assert matcher._make_decision(0.9, 0.85) == "SHORTLIST", "Skill 85% should be SHORTLIST"
        
    def test_full_skill_listing(self):
        """
        Verify explanation lists ALL matched skills, not truncated.
        """
        matcher = JobMatcher()
        
        matched = {"python", "java", "c++", "sql", "docker", "aws"} # 6 skills
        missing = set()
        
        # Shortlist explanation
        text = matcher._explanation_shortlist(
            "Cand", "Job", 0.9, 0.9, 1.0, 
            len(matched), 6, 0, matched, missing, 5, 5
        )
        
        # Check all skills present in text
        for s in matched:
            assert s in text, f"Skill '{s}' missing from explanation: {text}"
            
        # Review explanation
        text_review = matcher._explanation_review(
            "Cand", "Job", 0.6, 0.6, 1.0, 
            len(matched), 6, 0, matched, missing, 5, 5
        )
        for s in matched:
            assert s in text_review, f"Skill '{s}' missing from review explanation: {text_review}"
