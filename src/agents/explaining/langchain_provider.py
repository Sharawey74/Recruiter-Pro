"""
LangChain provider — the optional fourth path.

Kept as *one* provider rather than promoted to *the* abstraction. ADR-2 rejected
building on LangChain wholesale: the deployment target is a 512 MB free tier and
Phase 1 is actively removing unused heavy dependencies to fit it, so taking a
framework dependency to obtain two method calls inverts that work.

ADR-2 also records the condition for deleting this file: if LangChainProvider is
never selected in practice, remove it and the four langchain* pins. It earns its
place only while it is genuinely a fourth option.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from . import prompt
from .protocol import Explanation, ExplanationContext

logger = logging.getLogger(__name__)


class LangChainProvider:
    """Wraps ChatOllama through LangChain."""

    name = "langchain"

    def __init__(self, llm_config):
        self.config = llm_config
        self._llm = None
        self._import_failed = False

    def _get_llm(self):
        if self._llm is not None or self._import_failed:
            return self._llm
        try:
            from langchain_ollama import ChatOllama
        except ImportError as e:
            logger.warning(f"langchain-ollama not installed: {e}")
            self._import_failed = True
            return None
        try:
            self._llm = ChatOllama(
                model=self.config.model,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Could not construct ChatOllama: {e}")
            self._import_failed = True
            return None
        return self._llm

    def is_available(self) -> bool:
        return bool(self.config.enabled) and self._get_llm() is not None

    def explain(self, batch: List[ExplanationContext]) -> List[Explanation]:
        llm = self._get_llm()
        if llm is None:
            return [None] * len(batch)
        return [self._one(llm, c) for c in batch]

    def _one(self, llm, context: ExplanationContext) -> Optional[Explanation]:
        try:
            response = llm.invoke(
                [
                    ("system", prompt.SYSTEM),
                    ("human", prompt.build(context)),
                ]
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"LangChain invocation failed: {e}")
            return None

        # LangChain returns a message object, not a string -- one of the four
        # response shapes ADR-2 flagged as needing normalisation.
        text = (getattr(response, "content", None) or "").strip()
        if len(text) < prompt.MIN_USABLE_LENGTH:
            return None
        return Explanation(text, self.name)
