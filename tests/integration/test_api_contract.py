"""
The API, as it actually exists.

This replaces 23 tests that could never have passed. `test_api_endpoints.py`
and `test_e2e_resume_scoring.py` called `/api/v1/health`, `/api/v1/score`,
`/api/v1/batch` and `/api/v1/model-info` -- no version of this repository has
served `/api/v1/*`, so all 19 returned 404 on every run since they were
written. They tested a design that was never built. `test_api_client.py` was a
demo script requiring a live server on :8000, collected as four tests because
of its filename.

**Why this file exists in this shape.** Commit 655bb09 removed
`HybridScoringAgent.ml_predictor` while `api.py` still referenced it in four
places. The server raised AttributeError before serving a request and sat
broken on main for three commits. The verification bar in use -- "no newly
failing tests", compared as sets -- could not see it: those API tests were
already failing, so an already-broken module absorbed a new bug in silence.

`TestClient(app)` as a context manager runs the lifespan, so importing and
starting the application is itself the first assertion. That check is now
enforced by the suite rather than performed by hand.
"""
import pytest
from fastapi.testclient import TestClient

from src.api import app

SAMPLE_CV = (
    b"Jordan Ellis\n"
    b"jordan.ellis@example.com\n"
    b"Backend engineer with 8 years of experience building payment systems.\n"
    b"Python, JavaScript, PostgreSQL, Docker, Kubernetes, AWS\n"
    b"BSc Computer Science, University of Manchester\n"
)

# A Windows executable header. Built with bytes() rather than written as an
# escape inside a string literal, so no tooling in the chain can turn it into a
# real control byte in this source file -- which is exactly how a stray 0x00
# and, earlier, a 0x08 got into this repository.
WINDOWS_EXE = bytes([0x4D, 0x5A, 0x90, 0x00]) + b"payload"


@pytest.fixture(scope="module")
def client():
    """Starting the app is the point. The lifespan runs on __enter__."""
    with TestClient(app) as c:
        yield c


@pytest.mark.integration
class TestTheApplicationStarts:
    def test_root_responds(self, client):
        assert client.get("/").status_code == 200

    def test_health_reports_its_components(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        components = body["components"]
        assert components["jobs_loaded"] > 0
        assert "ml_model_loaded" in components
        assert "database_ready" in components

    def test_the_corpus_is_loaded(self, client):
        """A 503 from /match traces back to here."""
        assert client.get("/health").json()["components"]["jobs_loaded"] == 800


@pytest.mark.integration
class TestJobsEndpoint:
    def test_returns_jobs(self, client):
        body = client.get("/jobs?limit=5").json()
        assert len(body["jobs"]) == 5

    def test_every_job_carries_what_the_ui_renders(self, client):
        for job in client.get("/jobs?limit=10").json()["jobs"]:
            assert job["job_id"] and job["title"]


@pytest.mark.integration
class TestUploadValidation:
    """The guards from 4.2. Each maps to a way the endpoint could be abused."""

    def test_accepts_a_valid_cv(self, client):
        r = client.post("/upload", files={"file": ("cv.txt", SAMPLE_CV, "text/plain")})
        assert r.status_code == 200
        assert r.json()["extracted_data"]["email"] == "jordan.ellis@example.com"

    def test_rejects_an_unsupported_extension(self, client):
        r = client.post(
            "/upload",
            files={"file": ("cv.exe", WINDOWS_EXE, "application/octet-stream")},
        )
        assert r.status_code == 400

    def test_rejects_content_that_contradicts_the_extension(self, client):
        """A .exe renamed .pdf used to go straight to the parser."""
        r = client.post(
            "/upload",
            files={"file": ("cv.pdf", WINDOWS_EXE, "application/pdf")},
        )
        assert r.status_code == 400

    def test_rejects_an_empty_file(self, client):
        r = client.post("/upload", files={"file": ("cv.txt", b"", "text/plain")})
        assert r.status_code == 400

    def test_rejects_an_oversized_upload(self, client):
        """Unbounded read() meant a large POST took the process down."""
        big = b"%PDF-" + b"x" * (11 * 1024 * 1024)
        r = client.post("/upload", files={"file": ("big.pdf", big, "application/pdf")})
        assert r.status_code == 413


@pytest.mark.integration
class TestMatchEndpoint:
    def test_returns_ranked_matches(self, client):
        r = client.post(
            "/match?top_k=5&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        assert r.status_code == 200
        matches = r.json()["matches"]
        assert len(matches) == 5

        scores = [m["final_score"] for m in matches]
        assert scores == sorted(scores, reverse=True), "matches are not ranked"

    def test_every_match_carries_the_fields_the_frontend_reads(self, client):
        r = client.post(
            "/match?top_k=3&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        for match in r.json()["matches"]:
            for field in ("job_id", "job_title", "company_name", "final_score",
                          "matched_skills", "missing_skills", "status"):
                assert field in match, f"{field} missing from the match payload"

    def test_scores_are_percentages(self, client):
        r = client.post(
            "/match?top_k=5&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        for match in r.json()["matches"]:
            for field in ("final_score", "parser_score", "matcher_score", "scorer_score"):
                assert 0.0 <= match[field] <= 100.0, f"{field}={match[field]}"

    def test_single_job_match_returns_the_full_breakdown(self, client):
        """
        /match/single is the only endpoint returning the component scores.
        title_match is 17% of the rule-based total and used to be omitted, so
        the components could not reconstruct it.
        """
        job_id = client.get("/jobs?limit=1").json()["jobs"][0]["job_id"]
        r = client.post(
            f"/match/single?job_id={job_id}&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        assert r.status_code == 200
        breakdown = r.json()["scores_breakdown"]
        for component in ("skill_match", "title_match", "experience_match",
                          "education_match", "keyword_match"):
            assert component in breakdown, f"{component} missing from the breakdown"

    def test_rejects_a_bad_file_before_scoring(self, client):
        r = client.post(
            "/match?top_k=5",
            files={"file": ("cv.exe", WINDOWS_EXE, "application/octet-stream")},
        )
        assert r.status_code == 400


@pytest.mark.integration
class TestHistoryEndpoints:
    """
    Both of these returned 500 on every call they had ever received.

    /history called db.get_all_matches(), a method that does not exist, then
    read score_breakdown, cv_name, a nested decision and timestamp off
    MatchHistory rows that carry none of them. /match/single read
    match.timestamp off a MatchResult, which has created_at.

    Nothing caught it because the only tests covering the API pointed at
    /api/v1/*. A 500 on an endpoint the frontend calls is exactly the class of
    defect a contract test is for.
    """

    def test_history_returns_records(self, client):
        client.post(
            "/match?top_k=3&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        r = client.get("/history?limit=5")
        assert r.status_code == 200
        body = r.json()
        assert "matches" in body and "total" in body

    def test_history_records_carry_their_fields(self, client):
        r = client.get("/history?limit=5")
        for record in r.json()["matches"]:
            for field in ("match_id", "job_title", "score", "decision", "timestamp"):
                assert field in record, f"{field} missing from a history record"

    def test_match_history_alias_also_responds(self, client):
        assert client.get("/match/history?limit=3").status_code == 200

    def test_history_pagination_does_not_error(self, client):
        assert client.get("/history?limit=1&skip=1").status_code == 200
