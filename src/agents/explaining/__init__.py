"""
Agent 4's providers, and the agent that composes them.

Selection is `config.llm.provider` -- the field that has declared
`# ollama, openai, anthropic` since the beginning and that nothing ever read.
It is read here.

    provider: ollama       local development (default)
    provider: openrouter   hosted demo; needs OPENROUTER_API_KEY
    provider: langchain    optional fourth path
    provider: rule_based   offline, CI, and the fallback for all of the above

The provider is chosen once, at construction, and never reassigned. That is what
makes the A7 race structurally impossible rather than merely fixed: there is no
mutable state on the agent for a concurrent request to disturb.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from . import insights
from .langchain_provider import LangChainProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider
from .protocol import (
    SOURCE_RULE_BASED,
    Explanation,
    ExplanationContext,
    LLMProvider,
)
from .rule_based import RuleBasedProvider

logger = logging.getLogger(__name__)

_PROVIDERS = {
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
    "langchain": LangChainProvider,
    "rule_based": RuleBasedProvider,
}


def build_provider(config=None, name: Optional[str] = None) -> LLMProvider:
    """
    Construct the configured provider. Never raises; unknown names and failed
    construction both degrade to rule-based with a warning.
    """
    from ...core.config import get_config

    config = config or get_config()
    name = (name or getattr(config.llm, "provider", None) or "ollama").lower()

    if name in ("rule_based", "rules", "none"):
        return RuleBasedProvider()

    cls = _PROVIDERS.get(name)
    if cls is None:
        logger.warning(
            f"Unknown llm.provider {name!r}; expected one of "
            f"{sorted(_PROVIDERS)}. Using rule-based explanations."
        )
        return RuleBasedProvider()

    try:
        return cls(config.llm)
    except Exception as e:  # noqa: BLE001 - a bad provider must not break startup
        logger.warning(f"Could not construct provider {name!r}: {e}. Using rule-based.")
        return RuleBasedProvider()


class ExplainerAgent:
    """
    Agent 4. Holds a provider, owns the fallback chain, and nothing else.

    Stateless with respect to requests: `use_llm` is an argument, not an
    attribute. The previous implementation expressed "no LLM for this request"
    by writing False to `llm_available` on a shared singleton and restoring it
    afterwards, which leaked between concurrent requests and stuck permanently
    if the request raised in between.
    """

    def __init__(self, provider: Optional[LLMProvider] = None, config=None):
        self.config = config
        self.provider = provider if provider is not None else build_provider(config)
        self.fallback = RuleBasedProvider()

    @property
    def llm_available(self) -> bool:
        """Read-only. Kept because existing callers ask; no longer assignable."""
        return self.provider.name != SOURCE_RULE_BASED and self.provider.is_available()

    def explain(
        self,
        batch: List[ExplanationContext],
        use_llm: bool = True
    ) -> List[Explanation]:
        """
        Explain a batch, falling back per item.

        Falling back is normal operation, not an incident: quota exhausted,
        timeout, malformed output or an unavailable provider all end with the
        user getting an explanation tagged `rule_based`. Fallback is per item,
        so one bad response does not discard the good ones alongside it.
        """
        if not batch:
            return []

        if not use_llm or self.provider.name == SOURCE_RULE_BASED:
            return self.fallback.explain(batch)

        try:
            if not self.provider.is_available():
                logger.info(f"Provider {self.provider.name} unavailable; using rule-based.")
                return self.fallback.explain(batch)
            results = self.provider.explain(batch)
        except Exception as e:  # noqa: BLE001 - a provider bug is not an outage
            logger.warning(f"Provider {self.provider.name} raised: {e}. Using rule-based.")
            return self.fallback.explain(batch)

        # A provider that returns the wrong number of results is broken; do not
        # try to align them by position.
        if len(results) != len(batch):
            logger.warning(
                f"Provider {self.provider.name} returned {len(results)} results "
                f"for {len(batch)} contexts; using rule-based for the batch."
            )
            return self.fallback.explain(batch)

        return [
            item if item is not None else self.fallback.explain([context])[0]
            for item, context in zip(results, batch)
        ]

    def generate_explanation(self, match_result, use_llm: bool = True) -> str:
        """
        Explain one MatchResult and return the text.

        Compatibility surface for callers that hold a MatchResult and want a
        string. The protocol path is `explain`.
        """
        context = ExplanationContext.from_match_result(match_result)
        return self.explain([context], use_llm=use_llm)[0].text

    @staticmethod
    def generate_structured_insights(match_result) -> dict:
        """
        Strengths, weaknesses and recommendations as lists.

        Static because it reaches no provider: these are read straight off the
        score breakdown. See explaining/insights.py for why sending them to a
        model would be a loss.
        """
        return insights.build(ExplanationContext.from_match_result(match_result))


__all__ = [
    "ExplainerAgent",
    "Explanation",
    "ExplanationContext",
    "LLMProvider",
    "LangChainProvider",
    "OllamaProvider",
    "OpenRouterProvider",
    "RuleBasedProvider",
    "build_provider",
    "SOURCE_RULE_BASED",
]
