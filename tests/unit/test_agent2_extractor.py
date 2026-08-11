"""
Unit tests for Agent 2 (CandidateExtractor) — field extraction.

Agent 2 turns raw CV text into the structured profile every downstream score is
computed from. It had no unit tests: a wrong skill list or a missed experience
figure still produces a plausible number at the end of the pipeline, so
integration tests do not catch it.
"""
import pytest

from src.agents.agent2_extractor import CandidateExtractor


@pytest.fixture(scope="module")
def extractor():
    return CandidateExtractor()


CV = """Jane Doe
jane.doe@example.com
+44 7700 900123

Summary
Backend engineer with 8 years of experience building payment systems.

Technical Skills
Python, JavaScript, PostgreSQL, Docker, Kubernetes, AWS

Education
BSc Computer Science, University of Manchester
"""


class TestContactExtraction:
    @pytest.mark.unit
    def test_extracts_email(self, extractor):
        assert extractor.extract(CV)["email"] == "jane.doe@example.com"

    @pytest.mark.unit
    @pytest.mark.parametrize("text,expected", [
        ("Contact: a.b@example.co.uk", "a.b@example.co.uk"),
        ("EMAIL: UPPER@EXAMPLE.COM", "UPPER@EXAMPLE.COM"),
        ("no address here", ""),
    ])
    def test_email_variants(self, extractor, text, expected):
        assert extractor._extract_email(text) == expected

    @pytest.mark.unit
    def test_extracts_phone(self, extractor):
        assert any(c.isdigit() for c in extractor.extract(CV)["phone"])

    @pytest.mark.unit
    def test_missing_contact_returns_empty_not_none(self, extractor):
        """Downstream code indexes these fields; None would be a crash."""
        out = extractor.extract("nothing useful here")
        assert out["email"] == ""
        assert out["phone"] == ""


class TestSkillExtraction:
    @pytest.mark.unit
    def test_finds_skills_listed_in_the_cv(self, extractor):
        skills = {s.lower() for s in extractor.extract(CV)["skills"]}
        assert "python" in skills
        assert "docker" in skills

    @pytest.mark.unit
    def test_returns_a_list_not_a_string(self, extractor):
        assert isinstance(extractor.extract(CV)["skills"], list)

    @pytest.mark.unit
    def test_no_duplicate_skills(self, extractor):
        skills = extractor.extract(CV + "\nPython Python Python\n")["skills"]
        lowered = [s.lower() for s in skills]
        assert len(lowered) == len(set(lowered))

    @pytest.mark.unit
    def test_empty_text_yields_no_skills(self, extractor):
        assert extractor.extract("")["skills"] == []


class TestExperienceExtraction:
    @pytest.mark.unit
    def test_reads_years_from_a_summary_line(self, extractor):
        assert extractor._extract_experience("8 years of experience in backend") == 8

    @pytest.mark.unit
    @pytest.mark.parametrize("text", ["no numbers here", ""])
    def test_absent_experience_is_zero_not_none(self, extractor, text):
        assert extractor._extract_experience(text) == 0

    @pytest.mark.unit
    def test_experience_is_never_negative(self, extractor):
        assert extractor._extract_experience("-5 years of experience") >= 0


class TestOutputContract:
    """Every consumer indexes these keys. A missing one is an AttributeError
    several layers away from the cause."""

    REQUIRED_KEYS = {"name", "email", "phone", "skills", "experience_years", "education"}

    @pytest.mark.unit
    def test_populated_cv_has_all_keys(self, extractor):
        assert self.REQUIRED_KEYS <= set(extractor.extract(CV))

    @pytest.mark.unit
    def test_empty_input_has_all_keys(self, extractor):
        assert self.REQUIRED_KEYS <= set(extractor.extract(""))

    @pytest.mark.unit
    def test_extraction_is_deterministic(self, extractor):
        """Same CV in, identical profile out -- no set-ordering drift."""
        a, b = extractor.extract(CV), extractor.extract(CV)
        a.pop("extracted_at", None)
        b.pop("extracted_at", None)
        assert a == b
