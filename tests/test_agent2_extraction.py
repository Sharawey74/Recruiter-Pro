import pytest
import shutil
import os
from src.agents.agent2_extractor import NLP_Extractor

class TestNLPExtractor:
    
    @pytest.fixture
    def extractor(self):
        output_dir = "tests/temp_structured"
        agent = NLP_Extractor(output_dir=output_dir)
        yield agent
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    def test_full_extraction(self, extractor):
        raw_input = {
            "profile_id": "test_full",
            "raw_text": "Jane Doe. 5 years experience.",
            "sections": {
                "skills_block": "Python, Java, Kotlin",
                "experience_block": "I have worked for 5 years as a dev.",
                "education_block": "Masters in CS"
            }
        }
        
        result = extractor.process_profile(raw_input)
        
        assert result["profile_id"] == "test_full"
        assert "Python" in result["skills"]
        assert result["years_of_experience"] == 5
        assert result["education_level"] == "Masters"
        assert result["seniority_level"] == "Mid-Level"

    def test_fallback_strategies(self, extractor):
        # Case where sections are empty, should use raw_text
        raw_input = {
            "profile_id": "test_fallback",
            "raw_text": "Experienced in React and Node.js. 2 years experience. Bachelors degree.",
            "sections": {}
        }
        
        result = extractor.process_profile(raw_input)
        assert "React" in result["skills"] or "Node.js" in result["skills"]
        assert result["education_level"] == "Bachelors"
        assert result["years_of_experience"] == 2
