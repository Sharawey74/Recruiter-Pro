"""
The one skill vocabulary, loaded once and shared by every agent.

ADR-003 decided there is a single controlled vocabulary. In practice there were
five: the canonical file, a synonym dict inside Agent 3, a 178-skill
SKILLS_DATABASE plus a 14-entry synonym map inside Agent 2, and the dead
src/utils/skill_extraction.py. Each drifted independently, and A0 -- the worst
bug in this project -- was a vocabulary that resolved every language to its
family name.

This module is the only place the vocabulary file is read and flattened, so
"one vocabulary" is enforced by there being one loader rather than by
convention.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Cached per resolved path: the file is a few hundred KB and is read on every
# agent construction otherwise.
_CACHE: Dict[str, Dict[str, str]] = {}


def build_alias_index(raw: Dict) -> Dict[str, str]:
    """
    Flatten the family-nested vocabulary into {alias_lower: Canonical}.

    This is the A0 fix. The original code iterated the file as if it were flat
    -- {canonical: [aliases]} -- but it is nested by family:

        {"programming_languages": {"Python": ["python", "py"], ...}, ...}

    so `for canonical, aliases in raw.items()` bound `canonical` to the family
    name. Every language resolved to "programming_languages", and a Python CV
    matched a Java job perfectly.

    Handles both the current _meta/families layout and the older one that mixed
    metadata in beside the families. The isinstance guard is what skips
    `comment` / `_meta`, and its absence is what caused the original bug.
    """
    families = raw.get("families")
    if not isinstance(families, dict):
        families = {k: v for k, v in raw.items() if isinstance(v, dict)}

    index: Dict[str, str] = {}
    for _family, entries in families.items():
        if not isinstance(entries, dict):
            continue
        for canonical, aliases in entries.items():
            index[canonical.lower()] = canonical
            if not isinstance(aliases, (list, tuple)):
                continue
            for alias in aliases:
                index[str(alias).lower()] = canonical
    return index


def load_alias_index(path: str | Path, use_cache: bool = True) -> Dict[str, str]:
    """
    Read the vocabulary file and return the flattened alias index.

    Returns an empty index rather than raising if the file is missing, so a
    misconfigured path degrades to "nothing resolves" with a warning instead of
    taking the API down at import time.
    """
    skills_path = Path(path)
    key = str(skills_path.resolve()) if skills_path.exists() else str(skills_path)

    if use_cache and key in _CACHE:
        return _CACHE[key]

    if not skills_path.exists():
        logger.warning(f"Skills vocabulary not found: {skills_path}")
        return {}

    try:
        raw = json.loads(skills_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - a bad file must not kill startup
        logger.error(f"Failed to read skills vocabulary {skills_path}: {exc}", exc_info=True)
        return {}

    index = build_alias_index(raw)
    logger.info(
        f"[OK] Skill vocabulary loaded: {len(set(index.values()))} canonical "
        f"skills, {len(index)} aliases"
    )
    if use_cache:
        _CACHE[key] = index
    return index


def canonical_names(index: Optional[Dict[str, str]] = None) -> set:
    """Every canonical name in an alias index."""
    return set((index or {}).values())


def clear_cache() -> None:
    """Drop the cached indexes. For tests that write a temporary vocabulary."""
    _CACHE.clear()
