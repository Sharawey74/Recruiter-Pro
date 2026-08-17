"""
Database Layer for Recruiter Pro
SQLite wrapper with connection pooling and query helpers
"""

import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager

from .models import JobPosting, MatchHistory, MatchResult, match_result_to_history
from ..core.config import get_config


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file (None = use config)
        """
        if db_path is None:
            config = get_config()
            db_path = config.database.connection_string

        self.db_path = db_path
        self._ensure_db_dir()
        self._initialized = False
        # Schema creation is lazy, and every write path checks the flag first.
        # Without a lock, concurrent first-writers all saw _initialized False
        # and ran CREATE TABLE at once; the losers raised and their writes were
        # dropped. It showed up as the LLM budget recording 11 of 20 concurrent
        # increments -- an undercount, so the instance would overspend.
        self._init_lock = threading.Lock()

    def _ensure_db_dir(self):
        """Ensure database directory exists"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        # WAL lets readers proceed during a write, and synchronous=NORMAL drops
        # the per-commit fsync. Both are per-connection settings; WAL is the one
        # that persists in the database file.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        # Wait for a competing writer instead of failing instantly. SQLite's
        # default busy timeout is 0: a second connection attempting to write
        # raises "database is locked" immediately. That surfaced as the LLM
        # budget losing 9 of 20 concurrent increments -- each failure was
        # caught and logged by CallBudget.record, so the counter simply
        # undercounted and the instance would have overspent its quota.
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self):
        """Create database tables if they don't exist. Safe to call concurrently."""
        with self._init_lock:
            if self._initialized:
                return
            self._create_schema()

    def _create_schema(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Match history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS match_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT UNIQUE NOT NULL,
                    cv_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    
                    -- Candidate info
                    candidate_name TEXT,
                    candidate_email TEXT,
                    candidate_skills TEXT DEFAULT '[]',
                    
                    -- Job info
                    job_title TEXT NOT NULL,
                    required_skills TEXT DEFAULT '[]',
                    
                    -- Scores
                    skill_score REAL NOT NULL,
                    experience_score REAL NOT NULL,
                    education_score REAL NOT NULL,
                    keyword_score REAL NOT NULL,
                    rule_based_score REAL NOT NULL,
                    ml_score REAL,
                    final_score REAL NOT NULL,
                    
                    -- Decision
                    decision TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    explanation TEXT,
                    
                    -- Metadata
                    matched_skills TEXT DEFAULT '[]',
                    missing_skills TEXT DEFAULT '[]',
                    processing_time_ms REAL,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Indexes
                    CHECK(decision IN ('shortlist', 'review', 'reject')),
                    CHECK(final_score BETWEEN 0.0 AND 1.0),
                    CHECK(confidence BETWEEN 0.0 AND 1.0)
                )
            """
            )

            # Create indexes for common queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_cv_id 
                ON match_history(cv_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_job_id 
                ON match_history(job_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_decision 
                ON match_history(decision)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_final_score 
                ON match_history(final_score DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON match_history(created_at DESC)
            """
            )

            # Statistics table for quick lookups
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT UNIQUE NOT NULL,
                    metric_value REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Daily LLM call counter. In the database rather than in memory so
            # the budget survives a restart -- an in-process counter resets to
            # zero every deploy, which on a free tier that restarts on idle
            # means no budget at all.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_usage (
                    day TEXT PRIMARY KEY,
                    calls INTEGER NOT NULL DEFAULT 0
                )
            """
            )

            # The job corpus.
            #
            # It lived in data/json/jobs.json and was read-only: the API had no
            # write path for a job at all, so an applicant tracking system was
            # showing Jobs, Shortlist and History over a dataset nobody could
            # change. Writing back to the JSON file was the obvious alternative
            # and the wrong one -- a 1.5 MB rewrite per edit, no protection
            # against two writers, and on a host with an ephemeral filesystem
            # the edits vanish on the next deploy.
            #
            # So the database is the source of truth and the JSON file is the
            # seed. `seed_jobs_from` loads it once into an empty table; after
            # that the file is only history.
            #
            # Lists are stored as JSON text, matching how match_history already
            # stores skills. It costs a parse on read and keeps one row per job.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    category TEXT,
                    location_city TEXT,
                    location_country TEXT,
                    remote_type TEXT,
                    employment_type TEXT,
                    seniority_level TEXT,
                    min_experience_years REAL,
                    max_experience_years REAL,
                    description TEXT,
                    required_skills TEXT DEFAULT '[]',
                    preferred_skills TEXT DEFAULT '[]',
                    education_level TEXT,
                    salary_range TEXT,
                    posted_date TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # The three columns /jobs filters on.
            for column in ("category", "remote_type", "seniority_level"):
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_jobs_{column} ON jobs({column})")

            conn.commit()
            self._initialized = True

    def record_llm_calls(self, count: int = 1, day: Optional[str] = None) -> int:
        """
        Add to today's LLM call count and return the new total.

        One statement, so two workers incrementing at once cannot lose a count
        the way read-modify-write would.
        """
        if not self._initialized:
            self.initialize_schema()

        day = day or datetime.utcnow().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO llm_usage (day, calls) VALUES (?, ?)
                ON CONFLICT(day) DO UPDATE SET calls = calls + excluded.calls
                """,
                (day, count),
            )
            row = conn.execute("SELECT calls FROM llm_usage WHERE day = ?", (day,)).fetchone()
        return row["calls"] if row else count

    def llm_calls_today(self, day: Optional[str] = None) -> int:
        """How many LLM calls have been made today. 0 if none yet."""
        if not self._initialized:
            self.initialize_schema()

        day = day or datetime.utcnow().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            row = conn.execute("SELECT calls FROM llm_usage WHERE day = ?", (day,)).fetchone()
        return row["calls"] if row else 0

    def save_match(self, match: MatchResult) -> int:
        """
        Save a match result to database

        Args:
            match: MatchResult instance

        Returns:
            Database record ID
        """
        if not self._initialized:
            self.initialize_schema()

        history = match_result_to_history(match)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(self._INSERT_SQL, self._insert_row(history))
            return cursor.lastrowid

    # The column list and placeholders are shared by save_match and
    # save_matches_batch so the two cannot drift apart.
    _INSERT_SQL = """
        INSERT INTO match_history (
            match_id, cv_id, job_id,
            candidate_name, candidate_email, candidate_skills,
            job_title, required_skills,
            skill_score, experience_score, education_score, keyword_score,
            rule_based_score, ml_score, final_score,
            decision, confidence, reason, explanation,
            matched_skills, missing_skills, processing_time_ms,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    @staticmethod
    def _insert_row(history: MatchHistory) -> tuple:
        """Flatten a MatchHistory into the INSERT parameter tuple."""
        return (
            history.match_id,
            history.cv_id,
            history.job_id,
            history.candidate_name,
            history.candidate_email,
            history.candidate_skills,
            history.job_title,
            history.required_skills,
            history.skill_score,
            history.experience_score,
            history.education_score,
            history.keyword_score,
            history.rule_based_score,
            history.ml_score,
            history.final_score,
            history.decision,
            history.confidence,
            history.reason,
            history.explanation,
            history.matched_skills,
            history.missing_skills,
            history.processing_time_ms,
            history.created_at,
        )

    def save_matches_batch(self, matches: List[MatchResult]) -> int:
        """
        Save many match results on one connection, in one transaction.

        The pipeline used to call save_match once per job inside the scoring
        loop, and save_match opens a fresh sqlite3.connect, commits and closes
        every time. Measured at 4.31 ms per row -- 3.45 s of pure SQLite
        overhead on an 800-job upload, which was 43% of the whole request.

        One connection and one executemany does the same work in a single
        commit.

        Returns:
            Number of rows written.
        """
        if not matches:
            return 0

        if not self._initialized:
            self.initialize_schema()

        rows = [self._insert_row(match_result_to_history(m)) for m in matches]

        with self.get_connection() as conn:
            conn.executemany(self._INSERT_SQL, rows)

        return len(rows)

    def get_match_by_id(self, match_id: str) -> Optional[MatchHistory]:
        """Get match by match_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM match_history WHERE match_id = ?", (match_id,))
            row = cursor.fetchone()

            if row:
                return MatchHistory(**dict(row))
            return None

    def get_matches_for_cv(self, cv_id: str, limit: int = 100) -> List[MatchHistory]:
        """Get all matches for a specific CV"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM match_history 
                WHERE cv_id = ?
                ORDER BY final_score DESC, created_at DESC
                LIMIT ?
            """,
                (cv_id, limit),
            )

            return [MatchHistory(**dict(row)) for row in cursor.fetchall()]

    def get_matches_for_job(self, job_id: str, limit: int = 100) -> List[MatchHistory]:
        """Get all matches for a specific job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM match_history 
                WHERE job_id = ?
                ORDER BY final_score DESC, created_at DESC
                LIMIT ?
            """,
                (job_id, limit),
            )

            return [MatchHistory(**dict(row)) for row in cursor.fetchall()]

    def get_top_matches(
        self, decision: Optional[str] = None, min_score: Optional[float] = None, limit: int = 50
    ) -> List[MatchHistory]:
        """
        Get top matches with optional filtering

        Args:
            decision: Filter by decision type (shortlist, review, reject)
            min_score: Minimum final score threshold
            limit: Maximum results to return
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM match_history WHERE 1=1"
            params = []

            if decision:
                query += " AND decision = ?"
                params.append(decision)

            if min_score is not None:
                query += " AND final_score >= ?"
                params.append(min_score)

            query += " ORDER BY final_score DESC, created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            return [MatchHistory(**dict(row)) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Total matches
            cursor.execute("SELECT COUNT(*) as count FROM match_history")
            total_matches = cursor.fetchone()["count"]

            # Decision counts
            cursor.execute(
                """
                SELECT decision, COUNT(*) as count 
                FROM match_history 
                GROUP BY decision
            """
            )
            decision_counts = {row["decision"]: row["count"] for row in cursor.fetchall()}

            # Average scores
            cursor.execute(
                """
                SELECT 
                    AVG(final_score) as avg_score,
                    AVG(skill_score) as avg_skill,
                    AVG(experience_score) as avg_experience,
                    AVG(processing_time_ms) as avg_time
                FROM match_history
            """
            )
            averages = dict(cursor.fetchone())

            # Recent activity
            cursor.execute(
                """
                SELECT COUNT(*) as count 
                FROM match_history 
                WHERE created_at >= datetime('now', '-24 hours')
            """
            )
            recent_24h = cursor.fetchone()["count"]

            return {
                "total_matches": total_matches,
                "decision_counts": decision_counts,
                "averages": averages,
                "recent_24h": recent_24h,
            }

    def delete_match(self, match_id: str) -> bool:
        """Delete a match by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM match_history WHERE match_id = ?", (match_id,))
            return cursor.rowcount > 0

    def clear_all_matches(self) -> int:
        """Clear all match history (DANGER!)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM match_history")
            return cursor.rowcount

    def export_to_json(self, output_file: str):
        """Export all matches to JSON file"""
        matches = self.get_top_matches(limit=1000000)

        data = [
            {
                "match_id": m.match_id,
                "cv_id": m.cv_id,
                "job_id": m.job_id,
                "candidate_name": m.candidate_name,
                "job_title": m.job_title,
                "final_score": m.final_score,
                "decision": m.decision,
                "reason": m.reason,
                "created_at": m.created_at.isoformat(),
            }
            for m in matches
        ]

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

    # ----------------------------------------------------------- jobs --

    def seed_jobs(self, jobs: List["JobPosting"]) -> int:
        """
        Load the starting corpus into an empty table, once.

        Returns the number written, or 0 if the table already has rows. That
        check is what makes this safe to call on every startup: the seed is the
        initial state, not a reset, and re-running it must never overwrite a
        job someone has since edited.
        """
        if not self._initialized:
            self.initialize_schema()

        with self.get_connection() as conn:
            if conn.execute("SELECT 1 FROM jobs LIMIT 1").fetchone():
                return 0
            placeholders = ", ".join("?" for _ in _JOB_COLUMNS)
            conn.executemany(
                f"INSERT INTO jobs ({', '.join(_JOB_COLUMNS)}) VALUES ({placeholders})",
                [_job_to_row(job) for job in jobs],
            )
        return len(jobs)

    def list_jobs(self, include_inactive: bool = False) -> List["JobPosting"]:
        """Every job, oldest first, as the API's in-memory corpus."""
        if not self._initialized:
            self.initialize_schema()

        sql = f"SELECT {', '.join(_JOB_COLUMNS)} FROM jobs"
        if not include_inactive:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY rowid"

        with self.get_connection() as conn:
            return [_row_to_job(row) for row in conn.execute(sql).fetchall()]

    def get_job(self, job_id: str) -> Optional["JobPosting"]:
        if not self._initialized:
            self.initialize_schema()

        with self.get_connection() as conn:
            row = conn.execute(
                f"SELECT {', '.join(_JOB_COLUMNS)} FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return _row_to_job(row) if row else None

    def create_job(self, job: "JobPosting") -> bool:
        """False if the id is taken, rather than raising: the caller turns that
        into a 409, and a duplicate id is a client mistake, not an error."""
        if not self._initialized:
            self.initialize_schema()

        placeholders = ", ".join("?" for _ in _JOB_COLUMNS)
        try:
            with self.get_connection() as conn:
                conn.execute(
                    f"INSERT INTO jobs ({', '.join(_JOB_COLUMNS)}) VALUES ({placeholders})",
                    _job_to_row(job),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def update_job(self, job_id: str, job: "JobPosting") -> bool:
        """Full replace. False if no such job."""
        if not self._initialized:
            self.initialize_schema()

        assignments = ", ".join(f"{c} = ?" for c in _JOB_COLUMNS if c != "job_id")
        values = [v for c, v in zip(_JOB_COLUMNS, _job_to_row(job), strict=True) if c != "job_id"]

        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE jobs SET {assignments}, updated_at = CURRENT_TIMESTAMP "
                f"WHERE job_id = ?",
                (*values, job_id),
            )
            return cursor.rowcount > 0

    def delete_job(self, job_id: str) -> bool:
        if not self._initialized:
            self.initialize_schema()

        with self.get_connection() as conn:
            return conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,)).rowcount > 0


# Singleton instance
_db: Optional[Database] = None


# --------------------------------------------------------------------- jobs --
# The corpus, once it became writable. Kept together at the end of the class's
# module rather than scattered through it, because these are one concern.

_JOB_LIST_FIELDS = ("required_skills", "preferred_skills")

_JOB_COLUMNS = (
    "job_id",
    "title",
    "company_name",
    "category",
    "location_city",
    "location_country",
    "remote_type",
    "employment_type",
    "seniority_level",
    "min_experience_years",
    "max_experience_years",
    "description",
    "required_skills",
    "preferred_skills",
    "education_level",
    "salary_range",
    "posted_date",
    "is_active",
)


def _job_to_row(job: "JobPosting") -> tuple:
    """A JobPosting flattened for storage. Lists become JSON text."""
    values = []
    for column in _JOB_COLUMNS:
        value = getattr(job, column, None)
        if column in _JOB_LIST_FIELDS:
            value = json.dumps(list(value or []))
        elif column == "is_active":
            value = 1 if value in (None, True) else 0
        values.append(value)
    return tuple(values)


def _row_to_job(row) -> "JobPosting":
    """The inverse. Unknown-but-stored columns are ignored by the model."""
    data = {column: row[column] for column in _JOB_COLUMNS}
    for field in _JOB_LIST_FIELDS:
        try:
            data[field] = json.loads(data[field] or "[]")
        except (TypeError, json.JSONDecodeError):
            data[field] = []
    data["is_active"] = bool(data["is_active"])
    return JobPosting(**data)


def get_database(reload: bool = False) -> Database:
    """
    Get database instance (singleton)

    Args:
        reload: Force create new instance

    Returns:
        Database instance
    """
    global _db

    if _db is None or reload:
        _db = Database()
        _db.initialize_schema()

    return _db
