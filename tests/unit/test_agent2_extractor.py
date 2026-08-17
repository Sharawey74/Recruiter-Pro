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
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Contact: a.b@example.co.uk", "a.b@example.co.uk"),
            ("EMAIL: UPPER@EXAMPLE.COM", "UPPER@EXAMPLE.COM"),
            ("no address here", ""),
        ],
    )
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


class TestSharedVocabulary:
    """
    Agent 2 used to own a private 178-skill SKILLS_DATABASE and a 14-entry
    synonym map, making it the fourth competing vocabulary in a codebase whose
    ADR-003 says there is one. It now reads the same index Agent 3 scores
    against, so anything Agent 2 extracts is by construction something Agent 3
    can match.
    """

    @pytest.mark.unit
    def test_extracted_skills_are_canonical(self, extractor):
        canonical = set(extractor.skills_index.values())
        for skill in extractor.extract(CV)["skills"]:
            assert skill in canonical, f"{skill!r} is not a canonical name"

    @pytest.mark.unit
    def test_uses_the_shared_index_not_a_private_table(self, extractor):
        """The shared vocabulary is far larger than the old private one."""
        assert len(extractor.skills_index) > 1000

    @pytest.mark.unit
    def test_vocabulary_can_be_injected(self):
        """Constructor injection, so tests need no vocabulary file."""
        tiny = {"python": "Python", "widgetry": "Widgetry"}
        e = CandidateExtractor(skills_index=tiny)
        assert e._extract_skills("I know python and widgetry") == ["Python", "Widgetry"]

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("experienced in .NET development", ".NET"),
            ("wrote T-SQL queries", "T-SQL"),
            ("node.js backend", "Node.js"),
            ("c++ and c#", "C++"),
        ],
    )
    def test_punctuated_skills_survive_tokenisation(self, extractor, text, expected):
        assert expected in extractor._extract_skills(text)

    @pytest.mark.unit
    def test_multiword_skills_beat_their_parts(self, extractor):
        """'machine learning' must not be reduced to 'learning'."""
        assert "Machine Learning" in extractor._extract_skills("strong machine learning background")
