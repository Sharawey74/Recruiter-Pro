"""
Unit tests for Agent 1 (RawParser) — text extraction and segmentation.

Agent 1 had no unit tests. It was covered only end-to-end through
tests/integration/test_pipeline.py, where a segmentation failure still produces
a plausible-looking downstream score. That is the structural reason A0 survived
to production, and the same gap covers this agent.

Agent 1 is deliberately non-NLP: regex and string handling only. These tests
pin that behaviour at the unit level.
"""
import pytest

from src.agents.agent1_parser import RawParser


@pytest.fixture
def parser(tmp_path):
    """A parser writing to a temp dir, so tests never touch data/processed/."""
    return RawParser(output_dir=str(tmp_path / "raw_profiles"))


CV_TEXT = """Jane Doe
jane.doe@example.com
+44 7700 900123

Summary
Backend engineer with eight years building payment systems.

Work Experience
Senior Engineer, Acme Payments, 2019-2024
Engineer, Bytecorp, 2016-2019

Education
BSc Computer Science, University of Manchester, 2016

Technical Skills
Python, PostgreSQL, Docker, Kubernetes
"""


class TestTextExtraction:
    @pytest.mark.unit
    def test_extracts_text_from_txt(self, parser, tmp_path):
        f = tmp_path / "cv.txt"
        f.write_text(CV_TEXT, encoding="utf-8")
        assert "Jane Doe" in parser.extract_text_from_txt(str(f))

    @pytest.mark.unit
    def test_missing_file_raises_rather_than_returning_empty(self, parser, tmp_path):
        """
        Fails loudly. An empty string here would flow downstream as a CV with no
        skills and score as a poor match, hiding the real cause.
        """
        with pytest.raises(FileNotFoundError):
            parser.extract_text_from_txt(str(tmp_path / "nope.txt"))

    @pytest.mark.unit
    def test_unicode_survives_extraction(self, parser, tmp_path):
        f = tmp_path / "cv.txt"
        f.write_text("Zoë Müller\nSkills: C++, C#\n", encoding="utf-8")
        out = parser.extract_text_from_txt(str(f))
        assert "Zoë Müller" in out
        assert "C++" in out


class TestSegmentation:
    """Segmentation drives everything Agent 2 reads. If a block lands in the
    wrong section the extraction is wrong, silently."""

    @pytest.mark.unit
    def test_finds_the_four_content_sections(self, parser):
        s = parser._segment_text(CV_TEXT)
        assert "Acme Payments" in s["experience_block"]
        assert "University of Manchester" in s["education_block"]
        assert "PostgreSQL" in s["skills_block"]
        assert "payment systems" in s["summary_block"]

    @pytest.mark.unit
    def test_returns_all_expected_keys_even_when_empty(self, parser):
        s = parser._segment_text("just some text with no headers at all")
        assert set(s) == {
            "contact_block", "experience_block", "education_block",
            "skills_block", "summary_block",
        }

    @pytest.mark.unit
    def test_empty_input_does_not_raise(self, parser):
        assert isinstance(parser._segment_text(""), dict)

    @pytest.mark.unit
    @pytest.mark.parametrize("header", [
        "WORK EXPERIENCE", "Employment History", "professional background",
    ])
    def test_experience_header_variants_are_recognised(self, parser, header):
        s = parser._segment_text(f"{header}\nSenior Engineer at Acme\n")
        assert "Acme" in s["experience_block"]


class TestParseProfile:
    @pytest.mark.unit
    def test_returns_segmented_payload(self, parser):
        out = parser.parse_profile(CV_TEXT, profile_id="p1")
        assert isinstance(out, dict)
        assert out.get("profile_id") == "p1"

    @pytest.mark.unit
    def test_is_deterministic(self, parser):
        """Same text in, same structure out -- no ordering or timing drift."""
        a = parser.parse_profile(CV_TEXT, profile_id="p1")
        b = parser.parse_profile(CV_TEXT, profile_id="p1")
        a.pop("parsed_at", None)
        b.pop("parsed_at", None)
        assert a == b
