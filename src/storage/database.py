"""
Database Layer for Recruiter-Pro-AI
SQLite wrapper with connection pooling and query helpers
"""
import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager

from .models import MatchHistory, MatchResult, match_result_to_history
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
            cursor.execute("""
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
            """)
            
            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cv_id 
                ON match_history(cv_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_id 
                ON match_history(job_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_decision 
                ON match_history(decision)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_final_score 
                ON match_history(final_score DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON match_history(created_at DESC)
            """)
            
            # Statistics table for quick lookups
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT UNIQUE NOT NULL,
                    metric_value REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Daily LLM call counter. In the database rather than in memory so
            # the budget survives a restart -- an in-process counter resets to
            # zero every deploy, which on a free tier that restarts on idle
            # means no budget at all.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    day TEXT PRIMARY KEY,
                    calls INTEGER NOT NULL DEFAULT 0
                )
            """)

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
            row = conn.execute(
                "SELECT calls FROM llm_usage WHERE day = ?", (day,)
            ).fetchone()
        return row["calls"] if row else count

    def llm_calls_today(self, day: Optional[str] = None) -> int:
        """How many LLM calls have been made today. 0 if none yet."""
        if not self._initialized:
            self.initialize_schema()

        day = day or datetime.utcnow().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT calls FROM llm_usage WHERE day = ?", (day,)
            ).fetchone()
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
            history.match_id, history.cv_id, history.job_id,
            history.candidate_name, history.candidate_email, history.candidate_skills,
            history.job_title, history.required_skills,
            history.skill_score, history.experience_score,
            history.education_score, history.keyword_score,
            history.rule_based_score, history.ml_score, history.final_score,
            history.decision, history.confidence, history.reason, history.explanation,
            history.matched_skills, history.missing_skills, history.processing_time_ms,
            history.created_at
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
            cursor.execute(
                "SELECT * FROM match_history WHERE match_id = ?",
                (match_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return MatchHistory(**dict(row))
            return None
    
    def get_matches_for_cv(self, cv_id: str, limit: int = 100) -> List[MatchHistory]:
        """Get all matches for a specific CV"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM match_history 
                WHERE cv_id = ?
                ORDER BY final_score DESC, created_at DESC
                LIMIT ?
            """, (cv_id, limit))
            
            return [MatchHistory(**dict(row)) for row in cursor.fetchall()]
    
    def get_matches_for_job(self, job_id: str, limit: int = 100) -> List[MatchHistory]:
        """Get all matches for a specific job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM match_history 
                WHERE job_id = ?
                ORDER BY final_score DESC, created_at DESC
                LIMIT ?
            """, (job_id, limit))
            
            return [MatchHistory(**dict(row)) for row in cursor.fetchall()]
    
    def get_top_matches(
        self, 
        decision: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 50
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
            total_matches = cursor.fetchone()['count']
            
            # Decision counts
            cursor.execute("""
                SELECT decision, COUNT(*) as count 
                FROM match_history 
                GROUP BY decision
            """)
            decision_counts = {row['decision']: row['count'] for row in cursor.fetchall()}
            
            # Average scores
            cursor.execute("""
                SELECT 
                    AVG(final_score) as avg_score,
                    AVG(skill_score) as avg_skill,
                    AVG(experience_score) as avg_experience,
                    AVG(processing_time_ms) as avg_time
                FROM match_history
            """)
            averages = dict(cursor.fetchone())
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM match_history 
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            recent_24h = cursor.fetchone()['count']
            
            return {
                'total_matches': total_matches,
                'decision_counts': decision_counts,
                'averages': averages,
                'recent_24h': recent_24h
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
                'match_id': m.match_id,
                'cv_id': m.cv_id,
                'job_id': m.job_id,
                'candidate_name': m.candidate_name,
                'job_title': m.job_title,
                'final_score': m.final_score,
                'decision': m.decision,
                'reason': m.reason,
                'created_at': m.created_at.isoformat()
            }
            for m in matches
        ]
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)


# Singleton instance
_db: Optional[Database] = None


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
