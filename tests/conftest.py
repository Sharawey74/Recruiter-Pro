"""
Shared pytest configuration.

**The suite gets its own database, and that has to happen here.**

`src/api.py` builds its pipeline and calls `get_database()` at module scope, and
`src/core/config.py` resolves the database path at *its* module scope. Both run
the moment a test module imports `src.api`, so any redirection has to be in
place before the first import -- which is what a root conftest is for. A fixture
would be too late; the singleton already exists by the time one runs.

Without this, `/match` in the integration tests wrote to
`data/database/match_history.db` -- the same file the running application reads.
Every `pytest` run therefore inserted its sample candidate into the real
history, and the History page filled up with test data that no one had
analysed. 78 of the 81 rows in that file were test output.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
REPO_DATABASE = (PROJECT_ROOT / "data" / "database" / "match_history.db").resolve()

# Outside the repository, not merely outside git's view: a gitignored path in
# the working tree is still the file the developer's own instance opens.
TEST_DATABASE = Path(tempfile.gettempdir()) / "recruiter-pro-tests" / "match_history.db"

# Absolute, because DatabaseConfig joins its path onto PROJECT_ROOT and an
# absolute right-hand side is what makes that join land outside the repo.
os.environ["DATABASE_PATH"] = str(TEST_DATABASE)

# A run should not inherit the previous run's rows. Removing the directory
# rather than the file also clears the journal and WAL files beside it.
#
# Guarded by a marker in the environment because this module can legitimately be
# imported twice -- pytest loads it, and a test that wants these constants
# imports it again. Without the guard the second import would delete the
# database mid-run, while the application under test had it open.
_READY = "_RECRUITER_PRO_TEST_DB_READY"
if os.environ.get(_READY) != str(TEST_DATABASE):
    shutil.rmtree(TEST_DATABASE.parent, ignore_errors=True)
    TEST_DATABASE.parent.mkdir(parents=True, exist_ok=True)
    os.environ[_READY] = str(TEST_DATABASE)

# The same problem one setting along. The per-IP limiter is 5 POSTs to /match a
# minute, and the contract suite makes more than that -- so with a developer's
# .env switching it on, four of those tests failed with 429 on a laptop and
# passed in CI, which sets RATE_LIMIT_ENABLED=false. A suite whose result
# depends on the machine's .env is not a suite. The limiter's own tests skip
# themselves when it is off, and assert its behaviour by enabling it locally.
os.environ["RATE_LIMIT_ENABLED"] = "false"


@pytest.fixture
def project_root():
    return PROJECT_ROOT
