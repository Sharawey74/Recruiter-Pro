"""
Unit tests for the two LLM limits and the endpoint rate limiter (TASKS.md 4.4).

Three layers solve three different problems and none substitutes for another:

* the **explanation cap** in the pipeline bounds calls per upload,
* the **daily budget** bounds calls per day across all uploads,
* the **endpoint rate limiter** bounds requests per IP.

A rate limiter still permits 5 uploads a minute forever; a daily quota still
permits one client to consume all of it in a burst.
"""

import os
import tempfile
import threading
import time

import pytest

from src.agents.explaining import (
    CallBudget,
    ExplainerAgent,
    Explanation,
    ExplanationContext,
    Throttle,
)
from src.agents.explaining.budget import retry_after_seconds
from src.storage.database import Database


CONTEXT = ExplanationContext(
    candidate_name="Jane Doe",
    job_title="Backend Engineer",
    final_score=0.82,
    decision="shortlist",
    confidence=0.9,
    skill_score=0.8,
    experience_score=0.9,
    education_score=1.0,
    keyword_score=0.6,
    matched_skills=["Python"],
    missing_skills=["Kafka"],
)


class Working:
    name = "working"

    def is_available(self):
        return True

    def explain(self, batch):
        return [Explanation("x" * 100, self.name) for _ in batch]


class AlwaysFails(Working):
    name = "failing"

    def explain(self, batch):
        return [None] * len(batch)


@pytest.fixture
def db():
    return Database(db_path=os.path.join(tempfile.mkdtemp(), "budget.db"))


class TestDailyBudget:
    @pytest.mark.unit
    def test_degrades_to_rule_based_at_the_threshold(self, db):
        """quota 10 at 90% -> the 9th call is where it switches."""
        budget = CallBudget(db=db, daily_quota=10, degrade_at=0.90)
        agent = ExplainerAgent(Working(), budget=budget)

        assert agent.explain([CONTEXT] * 8)[0].source == "working"
        assert agent.explain([CONTEXT] * 2)[0].source == "rule_based"

    @pytest.mark.unit
    def test_degrading_still_returns_an_explanation(self, db):
        """Running out of quota degrades the demo; it does not break it."""
        budget = CallBudget(db=db, daily_quota=1, degrade_at=0.5)
        out = ExplainerAgent(Working(), budget=budget).explain([CONTEXT, CONTEXT])
        assert len(out) == 2
        assert all(len(e.text) > 50 for e in out)

    @pytest.mark.unit
    def test_failed_calls_are_not_charged(self, db):
        """
        A call that failed and fell back cost nothing. Charging for it would
        degrade the instance early on the strength of the provider's own errors.
        """
        budget = CallBudget(db=db, daily_quota=10)
        ExplainerAgent(AlwaysFails(), budget=budget).explain([CONTEXT, CONTEXT])
        assert budget.used_today() == 0

    @pytest.mark.unit
    def test_the_count_survives_a_restart(self, db):
        """
        In SQLite, not memory. The deployment target restarts on idle, and an
        in-process counter would reset the budget on every wake -- which is the
        same as having no budget.
        """
        CallBudget(db=db, daily_quota=100).record(5)
        assert Database(db_path=db.db_path).llm_calls_today() == 5

    @pytest.mark.unit
    def test_concurrent_increments_are_not_lost(self, db):
        """One UPDATE, not read-modify-write."""
        budget = CallBudget(db=db, daily_quota=1000)
        threads = [threading.Thread(target=budget.record, args=(1,)) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert budget.used_today() == 20

    @pytest.mark.unit
    @pytest.mark.parametrize("quota", [0, None])
    def test_zero_quota_disables_the_budget(self, db, quota):
        budget = CallBudget(db=db, daily_quota=quota or 0)
        assert budget.enabled is False
        assert budget.has_headroom(10_000) is True

    @pytest.mark.unit
    def test_no_database_disables_the_budget(self):
        assert CallBudget(db=None, daily_quota=100).enabled is False

    @pytest.mark.unit
    def test_a_broken_counter_fails_open(self):
        """
        A budget that cannot be read must not silently downgrade every
        explanation on the instance with nothing to point at.
        """

        class Broken:
            def llm_calls_today(self, day=None):
                raise RuntimeError("disk gone")

            def record_llm_calls(self, count=1, day=None):
                raise RuntimeError("disk gone")

        budget = CallBudget(db=Broken(), daily_quota=10)
        assert budget.has_headroom(1) is True
        budget.record(1)  # must not raise


class TestThrottle:
    @pytest.mark.unit
    def test_bounds_concurrency(self):
        throttle = Throttle(max_concurrent=2)
        live = peak = 0
        lock = threading.Lock()

        def work():
            nonlocal live, peak
            with throttle:
                with lock:
                    live += 1
                    peak = max(peak, live)
                time.sleep(0.02)
                with lock:
                    live -= 1

        threads = [threading.Thread(target=work) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert peak <= 2

    @pytest.mark.unit
    def test_releases_on_exception(self):
        """A raising call must not leak a permit and deadlock the next one."""
        throttle = Throttle(max_concurrent=1)
        with pytest.raises(ValueError):
            with throttle:
                raise ValueError("boom")
        with throttle:
            pass  # would block forever if the permit leaked

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "headers,expected",
        [
            ({"retry-after": "12"}, 12.0),
            ({"Retry-After": "3.5s"}, 3.5),
            ({"retry-after": "not-a-number"}, None),
            ({}, None),
            (None, None),
        ],
    )
    def test_retry_after_parsing(self, headers, expected):
        exc = RuntimeError("429")
        exc.response = type("R", (), {"headers": headers})()
        assert retry_after_seconds(exc) == expected

    @pytest.mark.unit
    def test_retry_after_on_a_plain_exception_is_none(self):
        assert retry_after_seconds(RuntimeError("no response attribute")) is None

    @pytest.mark.unit
    @pytest.mark.parametrize("seconds", [0, -5, None])
    def test_nonsense_backoff_is_ignored(self, seconds):
        throttle = Throttle(1)
        throttle.back_off(seconds)
        start = time.monotonic()
        with throttle:
            pass
        assert time.monotonic() - start < 0.5


class TestEndpointRateLimit:
    @pytest.mark.unit
    def test_upload_is_limited_per_ip(self):
        """
        Ten pass, the eleventh is refused. Verified against the real app, since
        the decorator and the limiter state are what could be misconfigured --
        not the library.
        """
        from fastapi.testclient import TestClient
        from src.api import RATE_LIMITING, app, limiter

        if not RATE_LIMITING:
            pytest.skip("slowapi not installed")

        # The suite runs with the limiter off, or every other test that posts
        # more than five times a minute is throttled. This test switches it on
        # for its own duration instead of skipping itself.
        #
        # It used to skip whenever configuration disabled the limiter, which
        # meant it skipped in CI -- where RATE_LIMIT_ENABLED=false -- and only
        # ran on a laptop whose .env happened to leave it on. The one assertion
        # covering the limiter was therefore not running anywhere it mattered.
        cv = b"Jane Doe\njane@example.com\nPython, Docker\nBSc Computer Science\n"
        was_enabled = limiter.enabled
        limiter.enabled = True
        # Counters are per key and survive between tests; an earlier upload
        # would otherwise be counted against this test's twelve.
        limiter.reset()
        try:
            with TestClient(app) as client:
                codes = [
                    client.post("/upload", files={"file": ("cv.txt", cv, "text/plain")}).status_code
                    for _ in range(12)
                ]
        finally:
            limiter.enabled = was_enabled
            limiter.reset()

        assert 429 in codes, "rate limit never triggered"
        assert codes.count(200) == 10, f"expected 10 accepted, got {codes.count(200)}"

    @pytest.mark.unit
    def test_get_endpoints_are_not_limited(self):
        """Reads are cheap; limiting them would break the frontend's polling."""
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app) as client:
            codes = {client.get("/health").status_code for _ in range(15)}
        assert codes == {200}
