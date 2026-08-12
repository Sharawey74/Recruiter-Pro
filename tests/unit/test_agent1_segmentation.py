"""
Agent 1's segmentation, job pass-through and opt-in writing.

`test_agent1_parser.py` covers construction and file reading. This covers what
happens to the text afterwards: the heuristic section split, the job
pass-through, and the write path that used to fire on every parse.

The segmentation is deliberately a regex heuristic rather than NLP, so the
tests pin what it does rather than what a reader might hope it does -- a
section header has to be a line on its own, and anything before the first
header belongs to the contact block.
"""
import json

import pytest

from src.agents.agent1_parser import RawParser


@pytest.fixture(scope="module")
def parser():
    return RawParser()


RESUME = """Jordan Ellis
jordan@example.com

Summary
Backend engineer with 8 years building payment systems.

Experience
Senior Engineer, Northbank (2019 - present)
Engineer, Griffin Analytics (2016 - 2019)

Skills
Python, Docker, PostgreSQL

Education
BSc Computer Science
"""


class TestBasicCleaning:
    @pytest.mark.unit
    def test_blank_lines_are_dropped(self, parser):
        assert parser._basic_clean("a\n\n\nb") == "a\nb"

    @pytest.mark.unit
    def test_surrounding_whitespace_is_stripped_per_line(self, parser):
        assert parser._basic_clean("   a   \n\t b \t") == "a\nb"

    @pytest.mark.unit
    def test_empty_input_stays_empty(self, parser):
        assert parser._basic_clean("") == ""

    @pytest.mark.unit
    def test_whitespace_only_input_collapses_to_empty(self, parser):
        assert parser._basic_clean("   \n\t\n   ") == ""


class TestSegmentation:
    @pytest.mark.unit
    def test_every_block_is_present_even_when_empty(self, parser):
        """Consumers index these keys; a missing one is a KeyError elsewhere."""
        sections = parser._segment_text("just some text")
        assert set(sections) == {
            "contact_block", "experience_block", "education_block",
            "skills_block", "summary_block",
        }

    @pytest.mark.unit
    def test_content_lands_in_the_right_block(self, parser):
        sections = parser._segment_text(parser._basic_clean(RESUME))
        assert "Northbank" in sections["experience_block"]
        assert "Python" in sections["skills_block"]
        assert "BSc" in sections["education_block"]
        assert "payment systems" in sections["summary_block"]

    @pytest.mark.unit
    def test_text_before_the_first_header_is_contact(self, parser):
        sections = parser._segment_text(parser._basic_clean(RESUME))
        assert "jordan@example.com" in sections["contact_block"]

    @pytest.mark.unit
    def test_headers_are_case_insensitive(self, parser):
        sections = parser._segment_text("SKILLS\nPython")
        assert "Python" in sections["skills_block"]

    @pytest.mark.unit
    @pytest.mark.parametrize("header,block", [
        ("Work Experience", "experience_block"),
        ("Employment History", "experience_block"),
        ("Professional Background", "experience_block"),
        ("Academic Background", "education_block"),
        ("Qualifications", "education_block"),
        ("Technical Skills", "skills_block"),
        ("Competencies", "skills_block"),
        ("Expertise", "skills_block"),
        ("Objective", "summary_block"),
        ("About Me", "summary_block"),
    ])
    def test_header_synonyms(self, parser, header, block):
        sections = parser._segment_text(f"{header}\nMARKER")
        assert "MARKER" in sections[block]

    @pytest.mark.unit
    def test_a_header_must_be_a_line_of_its_own(self, parser):
        """
        The rule is `^header$`, so a sentence mentioning "experience" does not
        open a section. This is a heuristic and the boundary is worth pinning:
        loosening it would silently reshuffle every CV's sections.
        """
        sections = parser._segment_text("I have experience with Python")
        assert sections["experience_block"] == ""
        assert "experience" in sections["contact_block"]

    @pytest.mark.unit
    def test_the_header_line_itself_is_not_kept(self, parser):
        assert "skills" not in parser._segment_text("Skills\nPython")["skills_block"].lower()

    @pytest.mark.unit
    def test_empty_text_gives_empty_blocks(self, parser):
        assert all(v == "" for v in parser._segment_text("").values())


class TestParseProfile:
    @pytest.mark.unit
    def test_returns_the_expected_keys(self, parser):
        out = parser.parse_profile(RESUME)
        for key in ("profile_id", "raw_text", "sections", "parsed_at", "parser_version"):
            assert key in out

    @pytest.mark.unit
    def test_an_explicit_id_is_used(self, parser):
        assert parser.parse_profile(RESUME, profile_id="abc-123")["profile_id"] == "abc-123"

    @pytest.mark.unit
    def test_an_id_is_generated_when_absent(self, parser):
        assert parser.parse_profile(RESUME)["profile_id"].startswith("profile_")

    @pytest.mark.unit
    def test_writing_is_opt_in(self, tmp_path):
        """
        Every parse used to drop a JSON into data/processed/raw_profiles/ that
        nothing read -- 66 orphaned files had accumulated, most named after
        pytest temp files.
        """
        parser = RawParser(output_dir=str(tmp_path / "out"))
        parser.parse_profile(RESUME, profile_id="not-saved")
        assert not (tmp_path / "out").exists()

    @pytest.mark.unit
    def test_saving_writes_readable_json(self, tmp_path):
        parser = RawParser(output_dir=str(tmp_path / "out"))
        parser.parse_profile(RESUME, profile_id="saved", save=True)

        written = tmp_path / "out" / "saved.json"
        assert written.exists()
        payload = json.loads(written.read_text(encoding="utf-8"))
        assert payload["profile_id"] == "saved"
        assert "Northbank" in payload["raw_text"]

    @pytest.mark.unit
    def test_construction_creates_no_directory(self, tmp_path):
        """2.7: constructing an agent must not touch the filesystem."""
        target = tmp_path / "never-made"
        RawParser(output_dir=str(target))
        assert not target.exists()


class TestParseJob:
    @pytest.mark.unit
    def test_passes_the_original_through(self, parser):
        job = {"Job Id": 42, "Job Title": "Engineer"}
        out = parser.parse_job(job)
        assert out["original_data"] == job
        assert out["job_id"] == "42"

    @pytest.mark.unit
    def test_raw_text_is_the_serialised_job(self, parser):
        out = parser.parse_job({"Job Id": 1, "Job Title": "Engineer"})
        assert json.loads(out["raw_text"])["Job Title"] == "Engineer"

    @pytest.mark.unit
    def test_a_missing_id_becomes_unknown_not_a_crash(self, parser):
        assert parser.parse_job({"Job Title": "Engineer"})["job_id"] == "unknown"
