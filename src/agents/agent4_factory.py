"""
Agent 4 factory.

Selection is now `config.llm.provider`, not a `use_langchain` boolean. The
boolean chose between two spellings of the same destination -- both branches
ended at Ollama -- and it does not extend to four options without becoming
`use_langchain`, `use_openrouter`, `use_rules` and an ambiguous set of
combinations. See ADR-2.
"""
from typing import Optional
import logging

from .explaining import ExplainerAgent, build_provider

logger = logging.getLogger(__name__)


def get_explainer_agent(
    use_langchain: Optional[bool] = None,
    config=None,
    provider: Optional[str] = None,
) -> ExplainerAgent:
    """
    Build Agent 4 with the configured provider.

    Args:
        use_langchain: deprecated. True still selects the LangChain provider so
            existing callers keep working; prefer `provider="langchain"`.
        config: application config.
        provider: explicit provider name, overriding config.llm.provider.

    Returns:
        ExplainerAgent, with the provider fixed at construction.
    """
    name = provider
    if name is None and use_langchain:
        name = "langchain"

    chosen = build_provider(config, name)
    logger.info(f"Agent 4 explainer ready: provider={chosen.name}")
    return ExplainerAgent(chosen, config=config)
