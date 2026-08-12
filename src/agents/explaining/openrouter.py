"""
OpenRouter provider — the hosted demo.

The deployment target is a 512 MB free tier. A 3B model needs several GB of
RAM, so Ollama cannot run there; this is the provider that makes a hosted demo
possible at all, and it is the reason ADR-2 exists.

Uses the `openai` SDK pointed at OpenRouter's OpenAI-compatible endpoint. That
dependency was pinned in requirements.txt with the comment "For
OpenRouter/GPT-OSS-20B access" and imported nowhere; it is re-added by the
commit that introduces this file, per ADR-2 action item 7.

The key comes from OPENROUTER_API_KEY in the environment. It is never logged,
never written to config, and never returned in a response. No key means
is_available() is False and the chain falls through to rule-based -- a missing
secret degrades the demo, it does not break it.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

from . import prompt
from .budget import Throttle, retry_after_seconds
from .protocol import Explanation, ExplanationContext

logger = logging.getLogger(__name__)

BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b:free"
ENV_KEY = "OPENROUTER_API_KEY"


class OpenRouterProvider:
    """Talks to OpenRouter over the OpenAI-compatible API."""

    name = "openrouter"

    def __init__(
        self,
        llm_config,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        throttle: Optional[Throttle] = None,
    ):
        """
        Args:
            llm_config: supplies temperature, max_tokens and timeout_seconds.
            api_key: injected for tests. Defaults to the environment; never
                read from config, so it cannot end up in a YAML file.
            model: overrides the default free model.
        """
        self.config = llm_config
        self._api_key = api_key or os.getenv(ENV_KEY)
        self.model = model or os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL
        self._client = None
        self.throttle = throttle or Throttle(
            getattr(llm_config, "max_concurrent_calls", 2)
        )

    def is_available(self) -> bool:
        """
        True when a key is present and the SDK imports.

        Deliberately does not make a network call. Availability is checked once
        per request batch, and spending a round trip -- plus quota -- to ask
        whether we may spend a round trip is not a good trade. A key that turns
        out to be rejected surfaces as a failed explain() and falls back.
        """
        if not self.config.enabled or not self._api_key:
            return False
        return self._get_client() is not None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ImportError:
            logger.warning(
                "openai SDK not installed; the OpenRouter provider is unavailable. "
                "pip install openai"
            )
            return None
        try:
            self._client = OpenAI(base_url=BASE_URL, api_key=self._api_key)
        except Exception as e:  # noqa: BLE001 - construction must not raise upward
            logger.warning(f"Could not construct the OpenRouter client: {e}")
            return None
        return self._client

    def explain(self, batch: List[ExplanationContext]) -> List[Explanation]:
        client = self._get_client()
        if client is None:
            return [None] * len(batch)
        return [self._one(client, c) for c in batch]

    def _one(self, client, context: ExplanationContext) -> Optional[Explanation]:
        try:
            # Bounded concurrency, and a shared backoff if the provider has
            # told us to wait. Free tiers answer excess concurrency with 429s
            # rather than a queue, so the queue has to be ours.
            with self.throttle:
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": prompt.SYSTEM},
                        {"role": "user", "content": prompt.build(context)},
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout_seconds,
                )
        except Exception as e:  # noqa: BLE001 - quota, timeout, auth, network
            # Honour Retry-After when the provider sends one: guessing a
            # backoff when the server has stated the answer is a slower way to
            # get rate-limited again.
            self.throttle.back_off(retry_after_seconds(e))
            # Never include the exception's request context, which can echo
            # headers. The message alone is enough to diagnose.
            logger.warning(f"OpenRouter request failed: {type(e).__name__}: {e}")
            return None

        text = self._extract(completion)
        if not text or len(text) < prompt.MIN_USABLE_LENGTH:
            return None
        return Explanation(text, self.name)

    @staticmethod
    def _extract(completion) -> Optional[str]:
        """
        Pull the text out of an OpenAI-shaped response.

        Defensive because this is the boundary ADR-2 flagged as where bugs
        appear: a provider that returns no choices, a null message, or a
        content-filtered empty string must not raise into the API handler.
        """
        try:
            choices = completion.choices
            if not choices:
                return None
            message = choices[0].message
            return (getattr(message, "content", None) or "").strip()
        except Exception as e:  # noqa: BLE001 - malformed response
            logger.warning(f"Malformed OpenRouter response: {e}")
            return None
