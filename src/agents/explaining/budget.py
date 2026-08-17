"""
Two limits on outbound LLM calls, solving two different problems.

`CallBudget` is a daily cap for the whole instance. When the day's calls reach
`quota_degrade_at` of `daily_quota`, explanations switch to rule-based for the
rest of the day. Running out of quota then degrades the demo rather than
breaking it -- and it degrades *before* the provider starts returning 429s
rather than after, so the user sees a slightly plainer explanation instead of a
stall followed by an error.

The count lives in SQLite, not in memory. An in-process counter resets to zero
on every restart, and the deployment target is a free tier that restarts on
idle -- which would mean no budget at all.

`Throttle` is a concurrency limit on calls in flight. Free tiers rate-limit
hard and the failure mode of exceeding one is a 429 storm, not a queue, so the
queue has to be ours. It also honours Retry-After when a provider sends one,
because guessing a backoff when the server has told you the answer is just a
slower way to get rate-limited again.

Both are deliberately dumb: a counter and a semaphore. Neither is a scheduler.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class CallBudget:
    """Daily instance-wide cap on LLM calls, persisted."""

    def __init__(self, db=None, daily_quota: int = 200, degrade_at: float = 0.90):
        self.db = db
        self.daily_quota = daily_quota
        self.degrade_at = degrade_at

    @property
    def enabled(self) -> bool:
        return bool(self.db) and self.daily_quota > 0

    @property
    def threshold(self) -> int:
        """The call count at which we stop using the provider."""
        return int(self.daily_quota * self.degrade_at)

    def used_today(self) -> int:
        if not self.enabled:
            return 0
        try:
            return self.db.llm_calls_today()
        except Exception as e:  # noqa: BLE001 - the budget must not break scoring
            logger.warning(f"Could not read the LLM budget: {e}")
            return 0

    def has_headroom(self, wanted: int = 1) -> bool:
        """
        Whether `wanted` more calls fit under the degrade threshold.

        Fails open. If the counter cannot be read, the request proceeds: a
        broken budget should not silently downgrade every explanation on the
        instance with nothing to point at.
        """
        if not self.enabled:
            return True

        used = self.used_today()
        if used + wanted > self.threshold:
            logger.info(
                f"LLM budget reached: {used}/{self.daily_quota} calls used today "
                f"(degrading at {self.threshold}). Using rule-based explanations."
            )
            return False
        return True

    def record(self, count: int = 1) -> None:
        if not self.enabled or count <= 0:
            return
        try:
            self.db.record_llm_calls(count)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Could not record LLM usage: {e}")


class Throttle:
    """Bounded concurrency for outbound calls, with Retry-After support."""

    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max(1, max_concurrent)
        self._semaphore = threading.BoundedSemaphore(self.max_concurrent)
        # When a provider says Retry-After, every caller waits, not just the
        # one that was told.
        self._blocked_until = 0.0
        self._lock = threading.Lock()

    def __enter__(self):
        self._wait_out_any_backoff()
        self._semaphore.acquire()
        return self

    def __exit__(self, *exc):
        self._semaphore.release()
        return False

    def _wait_out_any_backoff(self) -> None:
        with self._lock:
            remaining = self._blocked_until - time.monotonic()
        if remaining > 0:
            logger.info(f"Backing off {remaining:.1f}s on the provider's instruction")
            time.sleep(min(remaining, 30.0))

    def back_off(self, seconds: Optional[float]) -> None:
        """Record a Retry-After. Ignores absent or nonsensical values."""
        if not seconds or seconds <= 0:
            return
        with self._lock:
            self._blocked_until = max(self._blocked_until, time.monotonic() + min(seconds, 300.0))


def retry_after_seconds(exc: Exception) -> Optional[float]:
    """
    Pull Retry-After out of a provider exception, if it carries one.

    Providers differ in how they expose it, so this reads the two shapes the
    openai SDK produces and gives up quietly otherwise -- a missing header is
    normal, not an error.
    """
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    for key in ("retry-after", "Retry-After", "x-ratelimit-reset-requests"):
        try:
            value = headers.get(key)
        except Exception:  # noqa: BLE001 - headers may not be a mapping
            return None
        if value:
            try:
                return float(str(value).rstrip("s"))
            except ValueError:
                continue
    return None
