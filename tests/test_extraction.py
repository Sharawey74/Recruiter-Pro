"""
Unit Tests for Agent 3 Extractor
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.agent3_extractor import Agent3Extractor

@pytest.fixture
def agent():
    return Agent3Extractor()

class TestNameExtraction:
    """Test name extraction rules"""
    
    def test_header_extraction_candidate(self, agent):
        """Rule 1: Explicit 'Candidate:' header"""
        text = "Candidate: John Doe\nAddress: 123 Main St\nPhone: 555-1234"
        result = agent.extract(text)
        assert result['name'] == "John Doe"
    
    def test_header_extraction_name(self, agent):
        """Rule 1: Explicit 'Name:' header"""
        text = "Name: Jane Smith\nEmail: jane@example.com"
        result = agent.extract(text)
        assert result['name'] == "Jane Smith"
    
    def test_heuristic_extraction(self, agent):
        """Rule 2: First valid capitalized line"""
        text = "AHMED MOHAMED\nSoftware Engineer\n123 Tech Road"
        result = agent.extract(text)
        assert result['name'] == "AHMED MOHAMED"
    
    def test_no_address_confusion(self, agent):
        """Ensure addresses are not extracted as names"""
        text = "Mohamed Ali\nSheikh Zayed City\nPhone: 555-1234"
        result = agent.extract(text)
        assert result['name'] == "Mohamed Ali"
        assert "zayed" not in result['name'].lower()
    
    def test_critical_case_from_spec(self, agent):
        """Critical test case from specification"""
        text = "Candidate: abdelrahman Mohamed\nAddress: Sheikh Zayed"
        result = agent.extract(text)
        assert result['name'] == "abdelrahman Mohamed"
        assert "zayed" not in result['name'].lower()

class TestSkillExtraction:
    """Test skill extraction"""
    
    def test_basic_skills(self, agent):
        """Extract common technical skills"""
        text = "Experienced in Python, JavaScript, and Docker. Proficient with SQL databases."
        result = agent.extract(text)
        assert "python" in result['skills']
        assert "javascript" in result['skills'] or "js" in result['skills']
        assert "docker" in result['skills']
        assert "sql" in result['skills']
    
    def test_multiword_skills(self, agent):
        """Extract multi-word skills"""
        text = "Expert in machine learning and data science. Strong project management skills."
        result = agent.extract(text)
        # Should match at least some skills
        assert len(result['skills']) > 0

class TestContactExtraction:
    """Test email and phone extraction"""
    
    def test_email_extraction(self, agent):
        """Extract email address"""
        text = "Contact me at john.doe@example.com for inquiries."
        result = agent.extract(text)
        assert result['email'] == "john.doe@example.com"
    
    def test_phone_extraction_international(self, agent):
        """Extract international phone number"""
        text = "Phone: +1 555-123-4567"
        result = agent.extract(text)
        assert result['phone']
        assert "555" in result['phone']

class TestExperienceExtraction:
    """Test years of experience extraction"""
    
    def test_experience_pattern_1(self, agent):
        """Pattern: 'X years experience'"""
        text = "5 years experience in software development"
        result = agent.extract(text)
        assert result['experience_years'] == 5
    
    def test_experience_pattern_2(self, agent):
        """Pattern: 'Experience: X years'"""
        text = "Experience: 3 years in data analytics"
        result = agent.extract(text)
        assert result['experience_years'] == 3

class TestDeterminism:
    """Test deterministic behavior"""
    
    def test_same_input_same_output(self, agent):
        """Same input should produce same output"""
        text = "Candidate: Test User\nSkills: Python, SQL\nExperience: 2 years"
        result1 = agent.extract(text)
        result2 = agent.extract(text)
        assert result1 == result2
