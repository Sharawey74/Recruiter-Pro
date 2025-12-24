"""
Unit tests for Agent 1: Profile & Job Parser
"""
import pytest
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent1_parser import ProfileJobParser
from src.utils.text_processing import (
    clean_text,
    extract_years_of_experience,
    extract_email,
    extract_phone
)
from src.utils.skill_extraction import (
    extract_skills,
    extract_skills_from_list,
    calculate_skill_match
)


class TestTextProcessing:
    """Test text processing utilities."""
    
    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = "  Hello   World!  \n\n  Test  "
        cleaned = clean_text(dirty_text)
        assert "hello world" in cleaned
        assert "  " not in cleaned
    
    def test_extract_email(self):
        """Test email extraction."""
        text = "Contact me at john.doe@example.com for more info"
        email = extract_email(text)
        assert email == "john.doe@example.com"
    
    def test_extract_email_not_found(self):
        """Test email extraction when not present."""
        text = "No email here"
        email = extract_email(text)
        assert email == ""
    
    def test_extract_phone(self):
        """Test phone extraction."""
        text = "Call me at (555) 123-4567"
        phone = extract_phone(text)
        assert "555" in phone
        assert "123" in phone
    
    def test_extract_years_of_experience(self):
        """Test experience extraction."""
        text = "I have 5 years of experience in software development"
        years = extract_years_of_experience(text)
        assert years == 5
    
    def test_extract_years_of_experience_variations(self):
        """Test various experience formats."""
        test_cases = [
            ("5+ years of experience", 5),
            ("Experience: 8 years", 8),
            ("10 yrs experience", 10),
            ("No experience mentioned", 0),
        ]
        
        for text, expected in test_cases:
            years = extract_years_of_experience(text)
            assert years == expected, f"Failed for: {text}"


class TestSkillExtraction:
    """Test skill extraction utilities."""
    
    def test_extract_skills_basic(self):
        """Test basic skill extraction."""
        text = "I am proficient in Python, Java, and JavaScript"
        skills = extract_skills(text)
        assert "python" in skills
        assert "java" in skills
        assert "javascript" in skills
    
    def test_extract_skills_from_list(self):
        """Test extracting skills from delimited list."""
        text = "python | java | sql | docker | kubernetes"
        skills = extract_skills_from_list(text, delimiter='|')
        assert len(skills) == 5
        assert "python" in skills
        assert "kubernetes" in skills
    
    def test_calculate_skill_match(self):
        """Test skill matching calculation."""
        profile_skills = ["python", "java", "sql", "docker"]
        job_skills = ["python", "java", "kubernetes", "aws"]
        
        match = calculate_skill_match(profile_skills, job_skills)
        
        assert match['match_count'] == 2  # python, java
        assert len(match['matched_skills']) == 2
        assert len(match['missing_skills']) == 2  # kubernetes, aws
        assert match['match_ratio'] == 0.5  # 2/4
    
    def test_skill_match_empty(self):
        """Test skill matching with empty lists."""
        match = calculate_skill_match([], [])
        assert match['match_count'] == 0
        assert match['match_ratio'] == 0.0


class TestProfileJobParser:
    """Test ProfileJobParser class."""
    
    @pytest.fixture
    def parser(self, tmp_path):
        """Create parser instance with temp directory."""
        return ProfileJobParser(output_dir=str(tmp_path / "parsed_profiles"))
    
    @pytest.fixture
    def sample_profile_text(self):
        """Sample profile text for testing."""
        return """
        John Doe
        Email: john.doe@example.com
        Phone: +1-555-123-4567
        
        PROFESSIONAL SUMMARY
        Senior Software Engineer with 8 years of experience in full-stack development.
        
        SKILLS
        Python, Java, JavaScript, React, Node.js, SQL, AWS, Docker, Kubernetes
        
        EXPERIENCE
        Senior Software Engineer - Tech Corp (2018-2023)
        Led development of microservices architecture
        
        Software Engineer - StartupXYZ (2015-2018)
        Developed web applications using React and Node.js
        
        EDUCATION
        Bachelor of Science in Computer Science - MIT (2015)
        Master of Science in Software Engineering - Stanford (2017)
        """
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample job data for testing."""
        return {
            'Job Id': '12345',
            'Job Title': 'Senior Python Developer',
            'Experience': '5 - 8 yrs',
            'Qualifications': 'Strong Python skills, experience with Django/Flask, AWS knowledge required',
            'skills': 'python|django|flask|aws|sql|docker',
            'Role Category': 'Software Development',
            'Location': 'San Francisco, CA'
        }
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser is not None
        assert parser.output_dir.exists()
    
    def test_parse_profile_basic(self, parser, sample_profile_text):
        """Test basic profile parsing."""
        profile = parser.parse_profile(sample_profile_text, "test_001")
        
        assert profile['profile_id'] == "test_001"
        assert profile['contact']['email'] == "john.doe@example.com"
        assert len(profile['skills']) > 0
        assert profile['experience_years'] > 0
        assert len(profile['education']) > 0
    
    def test_parse_profile_skills(self, parser, sample_profile_text):
        """Test skill extraction from profile."""
        profile = parser.parse_profile(sample_profile_text, "test_002")
        
        skills = profile['skills']
        assert "python" in skills
        assert "java" in skills
        assert "javascript" in skills
        assert "aws" in skills
    
    def test_parse_profile_experience(self, parser, sample_profile_text):
        """Test experience extraction."""
        profile = parser.parse_profile(sample_profile_text, "test_003")
        
        # Should detect 8 years from summary or calculate from dates
        assert profile['experience_years'] >= 5
    
    def test_parse_profile_education(self, parser, sample_profile_text):
        """Test education extraction."""
        profile = parser.parse_profile(sample_profile_text, "test_004")
        
        education = profile['education']
        assert len(education) > 0
        # Should find Bachelor's and/or Master's
        assert any("bachelor" in e.lower() or "master" in e.lower() for e in education)
    
    def test_parse_profile_seniority(self, parser, sample_profile_text):
        """Test seniority determination."""
        profile = parser.parse_profile(sample_profile_text, "test_005")
        
        # Should be senior based on title and experience
        assert profile['seniority'] in ['senior', 'mid-level']
    
    def test_parse_profile_empty(self, parser):
        """Test parsing empty profile."""
        profile = parser.parse_profile("", "test_empty")
        
        assert profile['profile_id'] == ""
        assert profile['skills'] == []
        assert profile['experience_years'] == 0
    
    def test_parse_job_basic(self, parser, sample_job_data):
        """Test basic job parsing."""
        job = parser.parse_job(sample_job_data)
        
        assert job['job_id'] == '12345'
        assert job['job_title'] == 'Senior Python Developer'
        assert job['role_category'] == 'Software Development'
    
    def test_parse_job_skills(self, parser, sample_job_data):
        """Test skill extraction from job."""
        job = parser.parse_job(sample_job_data)
        
        skills = job['skills']
        assert "python" in skills
        assert "django" in skills
        assert "aws" in skills
    
    def test_parse_job_experience_range(self, parser, sample_job_data):
        """Test experience range parsing."""
        job = parser.parse_job(sample_job_data)
        
        assert job['experience']['min_years'] == 5
        assert job['experience']['max_years'] == 8
        assert job['experience']['range_text'] == '5 - 8 yrs'
    
    def test_parse_experience_range_variations(self, parser):
        """Test various experience range formats."""
        test_cases = [
            ("5 - 10 yrs", (5, 10)),
            ("3 to 7 years", (3, 7)),
            ("5 yrs", (5, 5)),
            ("", (0, 0)),
        ]
        
        for exp_text, expected in test_cases:
            min_exp, max_exp = parser._parse_experience_range(exp_text)
            assert (min_exp, max_exp) == expected, f"Failed for: {exp_text}"
    
    def test_save_parsed_profile(self, parser, sample_profile_text, tmp_path):
        """Test profile saving to file."""
        profile = parser.parse_profile(sample_profile_text, "test_save")
        
        # Check file was created
        output_file = parser.output_dir / "test_save.json"
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_profile = json.load(f)
        
        assert saved_profile['profile_id'] == "test_save"
        assert saved_profile['contact']['email'] == "john.doe@example.com"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def parser(self, tmp_path):
        """Create parser instance."""
        return ProfileJobParser(output_dir=str(tmp_path / "parsed_profiles"))
    
    def test_profile_with_no_contact_info(self, parser):
        """Test profile without email/phone."""
        text = "I am a developer with Python skills"
        profile = parser.parse_profile(text, "test_no_contact")
        
        assert profile['contact']['email'] == ""
        assert profile['contact']['phone'] == ""
    
    def test_profile_with_special_characters(self, parser):
        """Test profile with special characters."""
        text = "Skills: C++, C#, .NET, Node.js"
        profile = parser.parse_profile(text, "test_special")
        
        # Should still extract some skills
        assert len(profile['skills']) > 0
    
    def test_job_with_missing_fields(self, parser):
        """Test job with missing fields."""
        job_data = {
            'Job Id': '999',
            'Job Title': 'Developer',
        }
        
        job = parser.parse_job(job_data)
        
        assert job['job_id'] == '999'
        assert job['skills'] == []
        assert job['experience']['min_years'] == 0
    
    def test_very_long_profile(self, parser):
        """Test with very long profile text."""
        long_text = "Python developer. " * 1000
        profile = parser.parse_profile(long_text, "test_long")
        
        # Should handle without crashing
        assert profile['profile_id'] == "test_long"
        assert "python" in profile['skills']


class TestFileIngestion:
    """Test file ingestion for PDF, DOCX, and TXT files."""
    
    def test_txt_extraction(self, tmp_path):
        """Test TXT file extraction."""
        from src.agents.agent1_parser import RawParser
        
        # Create a test TXT file
        txt_file = tmp_path / "test_resume.txt"
        txt_content = """
        John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        
        Skills:
        Python, Java, JavaScript, SQL
        
        Experience:
        5 years of software development experience
        
        Education:
        Bachelor's in Computer Science
        """
        txt_file.write_text(txt_content, encoding='utf-8')
        
        # Test extraction
        parser = RawParser(output_dir=str(tmp_path / "output"))
        result = parser.parse_file(str(txt_file), "test_txt_001")
        
        assert result['profile_id'] == "test_txt_001"
        assert "john.doe@example.com" in result['raw_text'].lower()
        assert "python" in result['raw_text'].lower()
    
    def test_extract_text_from_txt_directly(self, tmp_path):
        """Test direct TXT extraction method."""
        from src.agents.agent1_parser import RawParser
        
        txt_file = tmp_path / "direct_test.txt"
        txt_file.write_text("Test content for extraction", encoding='utf-8')
        
        parser = RawParser()
        text = parser.extract_text_from_txt(str(txt_file))
        
        assert "Test content for extraction" in text
    
    def test_unsupported_file_format(self):
        """Test that unsupported file formats raise ValueError."""
        from src.agents.agent1_parser import RawParser
        
        parser = RawParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse_file("test.xlsx")
        
        assert "Unsupported file format" in str(exc_info.value)
    
    def test_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        from src.agents.agent1_parser import RawParser
        
        parser = RawParser()
        
        with pytest.raises(FileNotFoundError):
            parser.extract_text_from_txt("nonexistent.txt")


class TestAgent2SkillNormalization:
    """Test skill normalization in Agent 2."""
    
    def test_skill_normalization(self):
        """Test that skills are normalized correctly."""
        from src.agents.agent2_extractor import NLP_Extractor
        
        extractor = NLP_Extractor()
        
        # Test normalization
        raw_skills = ["python", "react.js", "nodejs", "aws ec2", "PostgreSQL"]
        normalized = extractor._normalize_skills(raw_skills)
        
        # Should normalize to canonical forms
        assert "React" in normalized or "Python" in normalized
        # Should deduplicate
        assert len(normalized) == len(set(normalized))
    
    def test_skill_deduplication(self):
        """Test that duplicate skills are removed."""
        from src.agents.agent2_extractor import NLP_Extractor
        
        extractor = NLP_Extractor()
        
        # Test with duplicates
        raw_skills = ["Python", "python", "PYTHON", "py"]
        normalized = extractor._normalize_skills(raw_skills)
        
        # Should result in single canonical form
        assert len(normalized) == 1
        assert "Python" in normalized


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
