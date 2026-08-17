"""
Agent 4 factory.

Selection is `config.llm.provider`, not a `use_langchain` boolean. The boolean
chose between two spellings of the same destination -- both branches ended at
Ollama -- and it did not extend to more options without becoming
`use_langchain`, `use_openrouter`, `use_rules` and an ambiguous set of
combinations. See ADR-2. The LangChain provider itself is gone; the boolean
went with it.
"""

from typing import Optional
import logging

from ..core.config import get_config
from .explaining import CallBudget, ExplainerAgent, build_provider

logger = logging.getLogger(__name__)


def _build_budget(config) -> CallBudget:
    """
    The daily LLM budget, backed by the match database.

    Constructed here rather than inside ExplainerAgent so that tests get an
    inert budget by default and never touch a database to check a fallback.
    """
    llm = config.llm
    quota = getattr(llm, "daily_quota", 0)
    if not quota:
        return CallBudget()

    try:
        from ..storage.database import get_database

        db = get_database()
    except Exception as e:  # noqa: BLE001 - no budget is better than no service
        logger.warning(f"LLM budget unavailable ({e}); explanations are uncapped.")
        return CallBudget()

    return CallBudget(
        db=db,
        daily_quota=quota,
        degrade_at=getattr(llm, "quota_degrade_at", 0.90),
    )


def get_explainer_agent(
    config=None,
    provider: Optional[str] = None,
) -> ExplainerAgent:
    """
    Build Agent 4 with the configured provider.

    Args:
        config: application config.
        provider: explicit provider name, overriding config.llm.provider.

    Returns:
        ExplainerAgent, with the provider fixed at construction.
    """
    config = config or get_config()
    chosen = build_provider(config, provider)
    budget = _build_budget(config)

    logger.info(
        f"Agent 4 explainer ready: provider={chosen.name}"
        + (f", daily budget {budget.threshold}/{budget.daily_quota}" if budget.enabled else "")
    )
    return ExplainerAgent(chosen, config=config, budget=budget)
