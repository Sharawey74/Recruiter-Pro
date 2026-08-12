"""
Ollama provider — local development.

Ported from agent4_llm_explainer, unchanged in behaviour: the same /api/tags
availability ping, the same /api/generate payload, the same minimum-length
check on the response.

What changed is what happens on failure. This returns None for a context it
could not explain and lets the caller decide; it no longer reaches for the
rule-based text itself. The fallback chain lives in one place (ExplainerAgent)
rather than being reimplemented inside every provider.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from . import prompt
from .protocol import Explanation, ExplanationContext

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover - environment-dependent
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed; the Ollama provider is unavailable.")


class OllamaProvider:
    """Talks to a local Ollama server."""

    name = "ollama"

    def __init__(self, llm_config):
        self.config = llm_config

    def is_available(self) -> bool:
        """Ping Ollama and confirm the configured model is actually pulled."""
        if not REQUESTS_AVAILABLE or not self.config.enabled:
            return False

        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=2)
            if response.status_code != 200:
                return False
            names = [m.get("name") for m in response.json().get("models", [])]
            if self.config.model in names:
                return True
            logger.warning(
                f"Ollama model {self.config.model} not found. Available: {names}"
            )
            return False
        except Exception as e:  # noqa: BLE001 - availability must never raise
            logger.warning(f"Ollama unavailable: {e}")
            return False

    def explain(self, batch: List[ExplanationContext]) -> List[Explanation]:
        """Explain each context; drop the ones that fail so the caller can fall back."""
        out = []
        for context in batch:
            text = self._generate(context)
            if text:
                out.append(Explanation(text, self.name))
            else:
                out.append(None)
        return out

    def _generate(self, context: ExplanationContext) -> Optional[str]:
        try:
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": f"{prompt.SYSTEM}\n\n{prompt.build(context)}",
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    },
                },
                timeout=self.config.timeout_seconds,
            )
        except Exception as e:  # noqa: BLE001 - a provider failure is not an outage
            logger.warning(f"Ollama request failed: {e}")
            return None

        if response.status_code != 200:
            logger.warning(f"Ollama returned {response.status_code}")
            return None

        try:
            text = (response.json().get("response") or "").strip()
        except ValueError as e:
            logger.warning(f"Ollama returned malformed JSON: {e}")
            return None

        # Short output means the model produced nothing useful. Treat it as a
        # failure rather than returning a one-line non-answer as an explanation.
        return text if len(text) >= prompt.MIN_USABLE_LENGTH else None
