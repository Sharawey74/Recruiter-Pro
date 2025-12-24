import pytest
import shutil
import json
from pathlib import Path
from src.match_history import MatchHistoryManager
from src.agents.agent2 import CandidateExtractor

class TestCoreLogic:
    
    @pytest.fixture
    def setup_dirs(self):
        """Create temporary data directories"""
        base_path = Path("data")
        test_file = base_path / "test_history.json"
        
        # Cleanup before test
        if test_file.exists():
            test_file.unlink()
            
        yield test_file
        
        # Cleanup after test
        if test_file.exists():
            test_file.unlink()

    def test_save_match_flattening(self, setup_dirs):
        """Test that nested skill data is correctly flattened"""
        mgr = MatchHistoryManager(history_file=str(setup_dirs))
        
        nested_matches = [{
            "job_id": "123",
            "score": 0.9,
            "skill_match": {
                "matched_skills": ["python", "aws"],
                "missing_skills": ["java"],
                "skill_match_score": 0.8
            }
        }]
        
        mgr.save_batch_matches("Test Candidate", nested_matches)
        
        # Verify saved data
        assert setup_dirs.exists()
        with open(setup_dirs, 'r') as f:
            data = json.load(f)
            
        saved_match = data[0]
        assert saved_match['candidate_name'] == "Test Candidate"
        # CRITICAL: Verify flattening works
        assert saved_match['matched_skills'] == ["python", "aws"]
        assert saved_match['missing_skills'] == ["java"]
        
    def test_name_extraction_filters(self):
        """Test improved name extraction logic"""
        extractor = CandidateExtractor()
        
        # Case 1: Email exclusion
        text_with_email = """
        E-mail: john.doe@example.com
        contact: +123456789
        John Doe
        Software Engineer
        """
        lines = [l.strip() for l in text_with_email.split('\n') if l.strip()]
        name = extractor._extract_name(lines, text_with_email)
        assert name == "John Doe", f"Expected 'John Doe', got '{name}'"
        
        # Case 2: Header Priority
        text_with_header = """
        Resume of Alice Smith
        Senior Developer
        alicemail@example.com
        """
        lines = [l.strip() for l in text_with_header.split('\n') if l.strip()]
        name = extractor._extract_name(lines, text_with_header)
        assert name == "Alice Smith", f"Expected 'Alice Smith', got '{name}'"

        # Case 3: Job Title Skipper (Implicit via regex/heuristics)
        # Note: Truly robust title skipping requires a dictionary, but we test the heuristic here
        text_title_confusion = """
        Software Engineer
        Bob Jones
        New York, NY
        """
        lines = [l.strip() for l in text_title_confusion.split('\n') if l.strip()]
        
        # This largely depends on whether "Software Engineer" passes _is_valid_name
        # Hopefully "Software Engineer" fails the heuristic if implemented correctly or if specific logic exists
        # If not, let's at least ensure basic validity
        name = extractor._extract_name(lines, text_title_confusion)
        assert name != "Software Engineer", "Should not extract job title as name"
        assert name == "Bob Jones"
