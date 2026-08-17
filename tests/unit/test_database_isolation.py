"""
The suite must not write to the database the application reads.

This is a regression guard, not a unit test of anything. `pytest` used to insert
its sample candidate into `data/database/match_history.db` on every run, because
`/match` persists and nothing pointed the tests elsewhere. The symptom was a
History page listing dozens of identical matches for a candidate no one had
uploaded -- and it looked like an application bug, not a test one, which is what
made it expensive.

`tests/conftest.py` redirects the path at import time. If that redirection is
removed or stops working, this fails before anything writes.
"""

from pathlib import Path

import pytest

from src.core.config import get_config
from tests.conftest import REPO_DATABASE, TEST_DATABASE


@pytest.mark.unit
def test_the_configured_database_is_not_the_repo_database():
    configured = Path(get_config().database.connection_string).resolve()
    assert configured != REPO_DATABASE


@pytest.mark.unit
def test_the_configured_database_is_the_temporary_one():
    configured = Path(get_config().database.connection_string).resolve()
    assert configured == TEST_DATABASE.resolve()


@pytest.mark.unit
def test_the_repo_database_is_left_alone():
    """
    Its modification time is the check that matters. A run that opens the file
    at all -- even one that inserts nothing -- has already proved the
    redirection is not in force.
    """
    if not REPO_DATABASE.exists():
        pytest.skip("No application database on this machine")

    from src.storage.database import get_database

    # Touching the singleton is what would create or open a file.
    database = get_database()
    assert Path(database.db_path).resolve() != REPO_DATABASE
