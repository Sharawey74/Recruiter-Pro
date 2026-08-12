"""
The API's module-level helpers, tested directly.

`load_jobs` decides whether the application has a corpus at all -- every /match
request either finds jobs here or returns 503 -- and its whole job is to
survive a file that is missing, malformed, or partially invalid. None of that
is reachable through an endpoint, because by the time a request arrives the
corpus has already loaded.

`parse_experience` turns free text like "3-5 years" into a range. It is fed
whatever a job posting happens to contain.
"""
import json

import pytest

from src.api import load_jobs, parse_experience


VALID_JOB = {
    "job_id": "ENG-0001",
    "title": "Backend Engineer",
    "company_name": "Acme",
    "location_city": "Cairo",
    "location_country": "Egypt",
    "remote_type": "on-site",
    "employment_type": "full-time",
    "seniority_level": "mid",
    "required_skills": ["Python"],
    "preferred_skills": ["Docker"],
    "min_experience_years": 2,
    "max_experience_years": 6,
    "education_level": "Bachelor",
    "description": "A description long enough to be plausible. " * 5,
    "category": "engineering",
    "posted_date": "2026-01-15",
}


def _corpus(tmp_path, payload):
    path = tmp_path / "jobs.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestLoadJobs:
    @pytest.mark.unit
    def test_loads_a_valid_corpus(self, tmp_path, monkeypatch):
        path = _corpus(tmp_path, {"schema_version": "2.0", "jobs": [VALID_JOB]})
        monkeypatch.setattr("src.api.get_config", lambda: type(
            "C", (), {"jobs_data_path": str(path)})())
        jobs = load_jobs()
        assert len(jobs) == 1
        assert jobs[0].job_id == "ENG-0001"

    @pytest.mark.unit
    def test_a_missing_file_is_an_empty_list_not_a_crash(self, tmp_path, monkeypatch):
        """
        /match turns this into a 503 with a message. An exception here would
        instead kill startup, since load_jobs runs inside the lifespan.
        """
        monkeypatch.setattr("src.api.get_config", lambda: type(
            "C", (), {"jobs_data_path": str(tmp_path / "absent.json")})())
        assert load_jobs() == []

    @pytest.mark.unit
    def test_unparseable_json_is_an_empty_list(self, tmp_path, monkeypatch):
        path = tmp_path / "jobs.json"
        path.write_text("{ not json at all", encoding="utf-8")
        monkeypatch.setattr("src.api.get_config", lambda: type(
            "C", (), {"jobs_data_path": str(path)})())
        assert load_jobs() == []

    @pytest.mark.unit
    @pytest.mark.parametrize("payload", [
        [VALID_JOB],                       # a bare array, the legacy shape
        {"records": [VALID_JOB]},          # right idea, wrong key
        {"schema_version": "2.0"},         # envelope with no jobs
        "a string",
    ])
    def test_the_wrong_shape_is_rejected_wholesale(self, tmp_path, monkeypatch, payload):
        """
        The corpus is an object with a 'jobs' array. A bare array was the
        legacy shape and is no longer produced; accepting it silently would
        let two formats drift again.
        """
        path = _corpus(tmp_path, payload)
        monkeypatch.setattr("src.api.get_config", lambda: type(
            "C", (), {"jobs_data_path": str(path)})())
        assert load_jobs() == []

    @pytest.mark.unit
    def test_invalid_records_are_skipped_not_fatal(self, tmp_path, monkeypatch):
        """
        One malformed record must not cost the other 799. They used to be
        swallowed at DEBUG, so there was no way to know how many were lost.
        """
        path = _corpus(tmp_path, {"jobs": [
            VALID_JOB,
            {"job_id": "BROKEN", "title": "missing everything else"},
            {**VALID_JOB, "job_id": "ENG-0002"},
        ]})
        monkeypatch.setattr("src.api.get_config", lambda: type(
            "C", (), {"jobs_data_path": str(path)})())

        jobs = load_jobs()
        assert [j.job_id for j in jobs] == ["ENG-0001", "ENG-0002"]

    @pytest.mark.unit
    def test_an_empty_jobs_array_is_empty_not_an_error(self, tmp_path, monkeypatch):
        path = _corpus(tmp_path, {"jobs": []})
        monkeypatch.setattr("src.api.get_config", lambda: type(
            "C", (), {"jobs_data_path": str(path)})())
        assert load_jobs() == []

    @pytest.mark.unit
    def test_no_cap_is_applied(self, tmp_path, monkeypatch):
        """
        A [:4000] slice once discarded 2,146 of 6,146 records while /jobs
        still reported the sliced count as the total. Corpus size is a
        deliberate decision now, not a truncation.
        """
        path = _corpus(tmp_path, {"jobs": [
            {**VALID_JOB, "job_id": f"ENG-{i:04d}"} for i in range(50)
        ]})
        monkeypatch.setattr("src.api.get_config", lambda: type(
            "C", (), {"jobs_data_path": str(path)})())
        assert len(load_jobs()) == 50


class TestParseExperience:
    @pytest.mark.unit
    @pytest.mark.parametrize("text,expected", [
        ("3-5 years", (3, 5)),
        ("5 years", (5, 5)),
        ("2 to 7 years", (2, 7)),
        ("10+ years", (10, 10)),
    ])
    def test_reads_the_numbers(self, text, expected):
        assert parse_experience(text) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("text", ["", None])
    def test_absent_input_is_zero_not_a_crash(self, text):
        assert parse_experience(text) == (0, 0)

    @pytest.mark.unit
    @pytest.mark.parametrize("text", ["entry level", "not specified", "junior"])
    def test_text_with_no_numbers_gets_a_junior_default(self, text):
        assert parse_experience(text) == (0, 2)

    @pytest.mark.unit
    def test_extra_numbers_are_ignored(self, text="2-5-9 years"):
        """Takes the first two; a third number is not a third bound."""
        assert parse_experience(text) == (2, 5)

    @pytest.mark.unit
    def test_a_non_string_is_coerced_not_rejected(self):
        assert parse_experience(5) == (5, 5)
