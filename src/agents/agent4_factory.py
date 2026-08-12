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

    config = config or get_config()
    chosen = build_provider(config, name)
    budget = _build_budget(config)

    logger.info(
        f"Agent 4 explainer ready: provider={chosen.name}"
        + (f", daily budget {budget.threshold}/{budget.daily_quota}" if budget.enabled else "")
    )
    return ExplainerAgent(chosen, config=config, budget=budget)
