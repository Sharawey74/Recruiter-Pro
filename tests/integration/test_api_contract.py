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

import json

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
            for field in (
                "job_id",
                "job_title",
                "company_name",
                "final_score",
                "matched_skills",
                "missing_skills",
                "status",
            ):
                assert field in match, f"{field} missing from the match payload"

    def test_scores_are_percentages(self, client):
        r = client.post(
            "/match?top_k=5&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        for match in r.json()["matches"]:
            for field in ("final_score", "rule_based_score", "skill_score", "experience_score"):
                assert 0.0 <= match[field] <= 100.0, f"{field}={match[field]}"

    def test_component_scores_are_named_for_what_they_measure(self, client):
        """
        These went out as parser_score, matcher_score and scorer_score --
        named after the agent a reader would assume produced them, which was
        wrong for all three. The UI labelled the skill score "ATS" as a
        result. The old names must not come back. See TASKS.md 5.9.
        """
        r = client.post(
            "/match?top_k=1&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        match = r.json()["matches"][0]
        for gone in ("parser_score", "matcher_score", "scorer_score"):
            assert gone not in match, f"{gone} is back in the match payload"

    def test_the_legacy_field_aliases_are_gone(self, client):
        """
        Four fields went out twice under two names -- title/job_title,
        company_name/company, location_city+country/location,
        employment_type/job_type -- so every consumer wrote `a || b` and
        guessed which was authoritative. See TASKS.md 5.6.
        """
        match = client.post(
            "/match?top_k=1&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        ).json()["matches"][0]
        job = client.get("/jobs?limit=1").json()["jobs"][0]

        for gone in ("company", "location", "job_type"):
            assert gone not in match, f"{gone} is back on the match payload"
            assert gone not in job, f"{gone} is back on the job payload"

        # One name per concept per response: a job is `title`, a match is
        # `job_title`, and neither carries both.
        assert "title" in job and "job_title" not in job
        assert "job_title" in match and "title" not in match

    def test_explanations_say_what_wrote_them(self, client):
        """
        A rule-based explanation and a model-written one are both fluent
        paragraphs. Without provenance a dead key, an exhausted quota or an
        unreachable provider is indistinguishable from a working demo -- the
        same argument as scoring_mode, applied to the prose. The pipeline
        already recorded this; nothing served it. See TASKS.md 6.9.
        """
        matches = client.post(
            "/match?top_k=3&explain=true",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        ).json()["matches"]

        explained = [m for m in matches if m.get("explanation")]
        if not explained:
            pytest.skip("no match scored high enough to be explained")

        for match in explained:
            assert match.get(
                "explanation_source"
            ), "an explanation was returned without saying what produced it"

    def test_processing_time_is_measured(self, client):
        """
        Reported as None on every call while the dashboard sat through 2.5s
        of hardcoded setTimeout to imply the work was still happening.
        """
        r = client.post(
            "/match?top_k=3&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        body = r.json()
        assert body["processing_time"] > 0
        assert body["jobs_evaluated"] > 0

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
        for component in (
            "skill_match",
            "title_match",
            "experience_match",
            "education_match",
            "keyword_match",
        ):
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
    /match/history returned 500 on every call it had ever received, as did the
    /history duplicate that has since been removed: db.get_all_matches() does
    not exist, and the handler read score_breakdown, cv_name, a nested
    decision and timestamp off MatchHistory rows that carry none of them.

    Nothing caught it because the only tests covering the API pointed at
    /api/v1/*. A 500 on an endpoint the frontend calls is exactly the class of
    defect a contract test is for.
    """

    def test_history_returns_records(self, client):
        client.post(
            "/match?top_k=3&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        )
        r = client.get("/match/history?limit=5")
        assert r.status_code == 200
        body = r.json()
        assert "matches" in body and "total" in body

    def test_history_records_carry_the_fields_the_frontend_reads(self, client):
        r = client.get("/match/history?limit=5")
        for record in r.json()["matches"]:
            for field in (
                "match_id",
                "job_title",
                "final_score",
                "status",
                "candidate_name",
                "matched_skills",
                "timestamp",
            ):
                assert field in record, f"{field} missing from a history record"

    def test_a_stored_match_has_the_same_shape_as_a_live_one(self, client):
        """
        One resource, one encoding. The removed /history served these same
        rows as `score`/`cv_name`/`decision`, and the two shapes drifted until
        one of them returned 500 on every call. See TASKS.md 5.8.
        """
        live = client.post(
            "/match?top_k=1&explain=false",
            files={"file": ("cv.txt", SAMPLE_CV, "text/plain")},
        ).json()["matches"][0]
        stored = client.get("/match/history?limit=1").json()["matches"]
        if not stored:
            pytest.skip("nothing persisted to compare against")

        for field in (
            "match_id",
            "job_id",
            "job_title",
            "company_name",
            "final_score",
            "rule_based_score",
            "skill_score",
            "experience_score",
            "status",
            "matched_skills",
        ):
            assert field in live and field in stored[0], f"{field} not on both"

    def test_the_duplicate_history_endpoint_is_gone(self, client):
        assert client.get("/history?limit=5").status_code == 404

    def test_history_pagination_does_not_error(self, client):
        assert client.get("/match/history?limit=1&skip=1").status_code == 200


@pytest.mark.integration
class TestJobFiltering:
    """
    The Jobs search box sent `search` for months and the API silently dropped
    it -- FastAPI ignores unknown query parameters, so the request succeeded
    and returned the unfiltered page. See TASKS.md 5.3.
    """

    def test_search_narrows_the_result_set(self, client):
        everything = client.get("/jobs?limit=1").json()["total"]
        filtered = client.get("/jobs?limit=1&search=engineer").json()

        assert filtered["total"] < everything, "search did not filter anything"
        assert filtered["total"] > 0, "nothing matched a term the corpus contains"

    def test_search_is_case_insensitive(self, client):
        lower = client.get("/jobs?limit=1&search=manager").json()["total"]
        upper = client.get("/jobs?limit=1&search=MANAGER").json()["total"]
        assert lower == upper

    def test_a_search_matching_nothing_is_empty_not_an_error(self, client):
        r = client.get("/jobs?search=zzzznotarealskillzzzz")
        assert r.status_code == 200
        assert r.json()["total"] == 0
        assert r.json()["jobs"] == []

    @pytest.mark.parametrize(
        "param,value",
        [
            ("category", "engineering"),
            ("remote_type", "remote"),
            ("seniority", "senior"),
        ],
    )
    def test_each_facet_filters_and_every_row_honours_it(self, client, param, value):
        body = client.get(f"/jobs?limit=50&{param}={value}").json()
        assert body["total"] > 0, f"{param}={value} matched nothing"

        field = {"seniority": "seniority_level"}.get(param, param)
        for job in body["jobs"]:
            assert job[field] == value

    def test_filters_combine_as_and_not_or(self, client):
        both = client.get("/jobs?limit=1&category=engineering&remote_type=remote").json()
        one = client.get("/jobs?limit=1&category=engineering").json()
        assert both["total"] <= one["total"]

    def test_total_is_the_filtered_count_not_the_corpus_size(self, client):
        """Paging past the end of a filtered set depends on this."""
        body = client.get("/jobs?limit=1&category=engineering").json()
        assert body["total"] < body["corpus_total"]

    def test_facets_come_from_the_corpus(self, client):
        facets = client.get("/jobs/facets").json()
        assert "engineering" in facets["categories"]
        assert set(facets["remote_types"]) <= {"remote", "hybrid", "on-site"}
        assert facets["total"] > 0

    def test_a_single_job_can_be_fetched_by_id(self, client):
        job_id = client.get("/jobs?limit=1").json()["jobs"][0]["job_id"]
        r = client.get(f"/jobs/{job_id}")
        assert r.status_code == 200
        assert r.json()["job_id"] == job_id

    def test_the_detail_view_does_not_truncate_the_requirements(self, client):
        """
        The list view caps required_skills at 10 to keep the grid light. A
        detail page showing a truncated requirement list is misleading.
        """
        listed = client.get("/jobs?limit=200").json()["jobs"]
        capped = next((j for j in listed if len(j["required_skills"]) == 10), None)
        if capped is None:
            pytest.skip("no job in the corpus has 10 or more required skills")

        detail = client.get(f"/jobs/{capped['job_id']}").json()
        assert len(detail["required_skills"]) >= len(capped["required_skills"])

    def test_an_unknown_job_id_is_404(self, client):
        assert client.get("/jobs/NOPE-9999").status_code == 404


@pytest.mark.integration
class TestStatsEndpoint:
    """
    The landing page quotes these. The endpoint exists so that page cannot
    drift from the system, which is the same defect as the "3,000+ jobs" copy
    that sat above a truncated load. See TASKS.md 5.15.
    """

    def test_reports_the_corpus_it_actually_loaded(self, client):
        corpus = client.get("/stats").json()["corpus"]

        assert corpus["jobs"] == client.get("/health").json()["components"]["jobs_loaded"]
        for field in ("countries", "cities", "companies", "distinct_skills"):
            assert corpus[field] > 0, f"{field} is zero"

    def test_geography_is_bounded_by_the_corpus(self, client):
        """More cities than countries, and neither more than the job count."""
        corpus = client.get("/stats").json()["corpus"]

        assert corpus["countries"] <= corpus["cities"] <= corpus["jobs"]
        assert corpus["companies"] <= corpus["jobs"]

    def test_top_countries_are_ranked_and_consistent(self, client):
        corpus = client.get("/stats").json()["corpus"]
        top = corpus["top_countries"]

        assert top, "no countries returned"
        counts = [row["jobs"] for row in top]
        assert counts == sorted(counts, reverse=True), "not ranked"
        assert sum(counts) <= corpus["jobs"]
        assert len(top) <= corpus["countries"]

    def test_engine_reports_the_running_configuration(self, client):
        engine = client.get("/stats").json()["engine"]

        assert engine["agents"] == 4
        assert engine["scoring_mode"] in {"hybrid", "rule_based_only"}
        # The vocabulary Agent 2 is running: aliases always outnumber the
        # canonical names they resolve to, because each name is its own alias.
        assert engine["skill_aliases"] >= engine["canonical_skills"] > 0

    def test_no_accuracy_figure_is_published(self, client):
        """
        Deliberate. The classifier reports 99.3% accuracy and a 1.000 ROC-AUC
        on its test split, and TASKS.md 1.4 records why quoting that would be
        dishonest: the label is a threshold on a column the model does not
        train on, so two ordinary features reproduce it. A landing page
        advertising "99% accurate" would contradict the most careful analysis
        in this repository, so the figure is not served at all.
        """
        body = client.get("/stats").json()
        flat = json.dumps(body)
        for banned in ("accuracy", "roc_auc", "precision", "recall"):
            assert banned not in flat, f"{banned} is being published"
