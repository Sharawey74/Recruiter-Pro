"""
Recruiter Pro: Simple Unified API Server
Clean, straightforward REST API for resume-job matching

Endpoints:
- GET  /              - Welcome message
- GET  /health        - Server health check
- GET  /jobs          - List and filter available jobs
- POST /upload        - Upload and parse CV
- POST /match         - Match CV to all jobs (main endpoint)
- POST /match/single  - Match CV to specific job
- GET  /match/history - View match history
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Request, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import tempfile
import time
from pathlib import Path
import json
import logging
from datetime import datetime

from src.agents.pipeline import MatchingPipeline
from src.core.config import get_config
from src.storage.database import get_database
from src.storage.models import JobPosting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown, as one context manager.

    Replaces @app.on_event("startup"/"shutdown"), deprecated since FastAPI
    0.93 and slated for removal. The startup half also used to reference
    pipeline.agent3.ml_predictor, an attribute that stopped existing when the
    ML scorer was extracted -- so the server raised AttributeError before
    serving a request. See the commit message.
    """
    global jobs_cache

    logger.info("=" * 60)
    logger.info("🚀 Starting Recruiter Pro API server...")
    logger.info("=" * 60)

    logger.info("Loading the job corpus...")
    jobs_cache = load_corpus()
    logger.info(f"✅ Loaded {len(jobs_cache)} jobs")

    # Initialize database
    logger.info("Initializing database...")
    try:
        # Database is auto-initialized when get_database() is called
        logger.info("[OK] Database ready")
    except Exception as e:
        logger.warning(f"[WARN] Database initialization failed: {e}")

    # Check ML model
    if pipeline.agent3.ml_scorer.enabled:
        model_info = pipeline.agent3.ml_scorer.predictor.get_model_info()
        logger.info(f"[OK] ML model loaded: {model_info.get('model_name', 'Unknown')}")
        logger.info(f"   Test Recall: {model_info.get('test_recall', 'N/A')}")
    else:
        # Loud on purpose. The previous single-line warning scrolled past in a
        # wall of startup output, so the project ran without its headline
        # feature for a long time without anyone noticing. State the
        # consequence and the remedy, not just the fact.
        logger.warning("!" * 60)
        logger.warning("[WARN] ML model NOT loaded - scoring is RULE-BASED ONLY")
        logger.warning("       The hybrid ML+rules scoring is not running.")
        logger.warning("       Expected: models/production/ats_model.joblib")
        logger.warning("                 models/production/feature_engineer.joblib")
        logger.warning("       Regenerate with: python -m src.ml_engine.train \\")
        logger.warning("                          --data-path data/AI_Resume_Screening.csv")
        logger.warning("!" * 60)

    # Check Ollama
    if hasattr(pipeline, "config") and pipeline.config.llm.enabled:
        logger.info(f"✅ Ollama enabled: {pipeline.config.llm.model}")
    else:
        logger.info("ℹ️  Ollama disabled (explanations will be basic)")

    logger.info("=" * 60)
    logger.info("✅ API Server Ready!")
    logger.info("📖 API Docs: http://localhost:8000/docs")
    logger.info("📖 ReDoc: http://localhost:8000/redoc")
    logger.info("=" * 60)

    yield

    logger.info("👋 Shutting down API Server...")


# ============================================
# FASTAPI APP SETUP
# ============================================

app = FastAPI(
    title="Recruiter Pro",
    description="AI-powered resume matching with 4-agent pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS (allow frontend to call API)
#
# allow_origins=["*"] with allow_credentials=True is not a permissive setting --
# it is a broken one. The CORS spec forbids the combination, so browsers reject
# the response outright and every credentialed cross-origin call fails. It also
# ignored config.api.cors_origins and the CORS_ORIGINS env var, both of which
# already existed.
_cors_origins = get_config().api.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
logger.info(f"CORS restricted to: {', '.join(_cors_origins)}")

# ============================================
# RATE LIMITING
# ============================================
#
# Per-IP limits on the two endpoints that do real work. This protects the
# instance from abuse on a public URL; it is not what protects the LLM quota --
# that is the explanation cap in the pipeline plus the daily budget in
# explaining/budget.py. Both layers are needed: a rate limiter still permits
# 5 uploads a minute forever, and a quota still permits one client to consume
# all of it.
#
# slowapi is optional. If it is not installed the app runs unlimited with a
# warning rather than failing to start, because a missing rate limiter should
# not take down a local dev server.
_api_config = get_config().api
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    def client_address(request: Request) -> str:
        """
        Who to charge this request to.

        `get_remote_address` reads the socket address, which behind a proxy is
        the *proxy's* -- so on a hosted deployment every visitor lands in one
        bucket and ordinary traffic starts collecting 429s while an attacker is
        no more limited than before.

        X-Forwarded-For is a client-supplied header, so it is only believed
        when `trust_proxy_headers` says something in front is setting it. The
        leftmost entry is the original client; the rest are the proxies it
        passed through.
        """
        if _api_config.trust_proxy_headers:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return get_remote_address(request)

    limiter = Limiter(
        key_func=client_address,
        enabled=_api_config.rate_limit_enabled,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    RATE_LIMITING = True
    if _api_config.rate_limit_enabled:
        logger.info(
            f"Rate limits: /match {_api_config.match_rate_limit}, "
            f"/upload {_api_config.upload_rate_limit} (per IP)"
        )
    else:
        logger.warning("Rate limiting is DISABLED by config")
except ImportError:
    RATE_LIMITING = False
    logger.warning(
        "slowapi not installed - endpoints are UNLIMITED. "
        "This is unsafe on a public URL. pip install slowapi"
    )

    class _NoLimiter:
        """No-op stand-in so the decorators below are always valid."""

        @staticmethod
        def limit(_spec):
            def decorator(fn):
                return fn

            return decorator

    limiter = _NoLimiter()

# ============================================
# GLOBAL COMPONENTS
# ============================================

# Initialize pipeline and database
pipeline = MatchingPipeline(save_to_db=True)
db = get_database()

# Jobs cache (loaded on startup)
jobs_cache: List[JobPosting] = []

# Upload guards
ALLOWED_UPLOAD_SUFFIXES = (".pdf", ".docx", ".txt")

# What the bytes must actually start with, regardless of what the name claims.
# PDF is %PDF-, DOCX is a zip (PK\x03\x04). TXT has no signature, so it is
# checked by decoding instead.
_MAGIC = {
    ".pdf": b"%PDF-",
    ".docx": b"PK\x03\x04",
}


async def read_upload(file: UploadFile) -> tuple[bytes, str]:
    """
    Validate an upload and return (content, suffix).

    Three checks the API did not previously make, in the order that matters:

    1. **Size, before reading.** `await file.read()` pulled the whole body into
       memory with no cap at three separate endpoints, so a 500 MB POST took the
       process down. config.api.max_upload_size_mb (10) existed and was never
       consulted. Checked against the declared size first, then against the
       bytes actually read -- a client controls the Content-Length header, so
       the declared size is a hint, not a guarantee.
    2. **Extension.** Unchanged, but now in one place instead of three.
    3. **Content.** The extension was previously trusted outright: a .exe
       renamed to .pdf was handed straight to the parser. The magic bytes are
       cheap to check and catch the accidental case as well as the deliberate
       one.

    Raises HTTPException on any failure; callers get bytes or an error.
    """
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type: {suffix}. Use PDF, DOCX, or TXT")

    max_bytes = get_config().api.max_upload_size_mb * 1024 * 1024

    # Reject on the declared size before reading anything.
    if file.size is not None and file.size > max_bytes:
        raise HTTPException(
            413,
            f"File too large: {file.size / 1024 / 1024:.1f} MB. "
            f"Maximum is {get_config().api.max_upload_size_mb} MB",
        )

    content = await file.read()

    # And again on what actually arrived.
    if len(content) > max_bytes:
        raise HTTPException(
            413,
            f"File too large: {len(content) / 1024 / 1024:.1f} MB. "
            f"Maximum is {get_config().api.max_upload_size_mb} MB",
        )

    if not content:
        raise HTTPException(400, "Uploaded file is empty")

    expected = _MAGIC.get(suffix)
    if expected and not content.startswith(expected):
        raise HTTPException(400, f"File content does not match its {suffix} extension")
    if suffix == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(400, "Text file is not valid UTF-8") from None

    return content, suffix


def load_jobs() -> List[JobPosting]:
    """
    Load the job corpus.

    The corpus is an object with a metadata envelope and a "jobs" array, not a
    bare array - see JOBS_DATASET_SPEC.md. The legacy pipe-separated shape and
    the jobs_cleaned.json fallback were removed when that corpus was archived
    (data/archive/jobs-legacy-2026-08-09/); nothing produces them any more.

    The path comes from config rather than being hardcoded here, so the corpus
    and the vocabulary it was generated against are configured in one place.
    """
    jobs_path = Path(get_config().jobs_data_path)

    if not jobs_path.exists():
        logger.warning(f"Jobs file not found: {jobs_path}")
        return []

    try:
        with open(jobs_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if not isinstance(payload, dict) or "jobs" not in payload:
            logger.error(
                f"{jobs_path} is not in the expected format: expected an object with a "
                f"'jobs' key, got {type(payload).__name__}. See JOBS_DATASET_SPEC.md."
            )
            return []

        jobs = []
        skipped = 0
        for job_dict in payload["jobs"]:
            try:
                jobs.append(JobPosting(**job_dict))
            except Exception as e:
                # Count these. Previously they were swallowed at DEBUG, so there
                # was no way to know how many records silently failed to parse.
                skipped += 1
                if skipped <= 3:
                    logger.warning(f"Skipping invalid job {job_dict.get('job_id')}: {e}")
                continue

        # No [:4000] cap. The old corpus held 6,146 records and this silently
        # discarded 2,146 of them (34.9%) while /jobs still reported the sliced
        # count as the total. The corpus is now sized deliberately instead.
        if skipped:
            logger.warning(f"Loaded {len(jobs)} jobs, skipped {skipped} malformed")
        else:
            logger.info(
                f"Loaded {len(jobs)} jobs from {jobs_path} "
                f"(schema {payload.get('schema_version', '?')}, "
                f"generated {payload.get('generated_at', '?')})"
            )
        return jobs

    except Exception as e:
        logger.error(f"Failed to load jobs: {e}", exc_info=True)
        return []


def load_corpus() -> List[JobPosting]:
    """
    The corpus the application serves, read from the database.

    `load_jobs()` above reads the seed *file*. This reads the *table*, seeding it
    from that file the first time it is empty. The two are deliberately separate:
    the file is the starting state and is still validated on its own terms, while
    the table is what the API answers from and what `POST /jobs` writes to.

    Falling back to the file when the database is unavailable is intentional. A
    read-only corpus is a degraded service; no corpus at all is a 503 on every
    /match, and the file is right there.
    """
    try:
        db = get_database()
        seeded = db.seed_jobs(load_jobs())
        if seeded:
            logger.info(f"Seeded the jobs table with {seeded} roles from the corpus file")
        return db.list_jobs()
    except Exception as e:  # noqa: BLE001 - a read-only corpus beats none
        logger.error(f"Could not read jobs from the database ({e}); using the file", exc_info=True)
        return load_jobs()


def refresh_corpus() -> int:
    """
    Re-read the corpus into memory after a write.

    `jobs_cache` is the in-memory working set every read path and the scorer use;
    it is what makes scoring 800 roles take 0.74 s rather than 800 queries. A
    write therefore has to invalidate it, and reassignment is the whole
    invalidation: readers either see the old list or the new one, never a
    half-updated one.

    This is correct for one worker, which is what the deployment runs and why
    (each worker holds its own 215 MB copy of corpus and model). With several
    workers, a write served by one would leave the others stale until restart,
    and the cache would need to move out of process.
    """
    global jobs_cache
    jobs_cache = get_database().list_jobs()
    return len(jobs_cache)


def parse_experience(exp_str: str) -> tuple:
    """Parse experience string into (min, max) years tuple"""
    if not exp_str:
        return (0, 0)

    import re

    numbers = re.findall(r"\d+", str(exp_str))

    if not numbers:
        return (0, 2)
    if len(numbers) == 1:
        return (int(numbers[0]), int(numbers[0]))

    return (int(numbers[0]), int(numbers[1]))


# ============================================
# API ENDPOINTS
# ============================================


@app.get("/")
async def root():
    """Welcome message and API info"""
    return {
        "message": "Recruiter Pro - API Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "jobs": "/jobs",
            "job_facets": "/jobs/facets",
            "upload": "/upload",
            "match": "/match",
            "match_single": "/match/single",
            "history": "/match/history",
        },
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns server status and component availability
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "agents_loaded": True,
            "jobs_loaded": len(jobs_cache),
            "ml_model_loaded": pipeline.agent3.ml_scorer.enabled,
            "database_ready": db is not None,
            "ollama_enabled": pipeline.config.llm.enabled if hasattr(pipeline, "config") else False,
        },
    }


def job_payload(job: JobPosting) -> dict:
    """
    One job, in the shape the frontend consumes. One name per concept.

    /jobs, /match and /match/history all embed the same job fields. They were
    written out three times and had already drifted -- /match defaulted a
    missing country to 'India' while /match/history used 'Unknown'.

    There are no legacy aliases here any more. Four fields were emitted twice
    under two names -- title/job_title, company_name/company,
    location_city+location_country/location, employment_type/job_type -- which
    is not free: every consumer had to write `a || b` and guess which one was
    authoritative, and a component that read only the alias silently displayed
    nothing once the alias stopped being populated. See TASKS.md 5.6.
    """
    return {
        "job_id": job.job_id,
        "title": job.title,
        "company_name": job.company_name,
        "location_city": job.location_city,
        "location_country": job.location_country,
        "remote_type": job.remote_type,
        "employment_type": job.employment_type,
        "seniority_level": job.seniority_level,
        "min_experience_years": job.min_experience_years,
        "max_experience_years": job.max_experience_years,
        "description": job.description,
        "required_skills": job.required_skills[:10] if job.required_skills else [],
        "preferred_skills": job.preferred_skills[:5] if job.preferred_skills else [],
        "posted_date": job.posted_date,
        "category": getattr(job, "category", None),
        # Present on all 800 corpus records. It was loaded and then dropped
        # before serialisation, so the UI had no salary to show.
        "salary_range": getattr(job, "salary_range", None),
    }


# A job the cache has no record of. Every field the frontend reads is present
# with a neutral value, so a missing job renders as blanks rather than
# throwing on an attribute of None.
MISSING_JOB_PAYLOAD = {
    "title": "Unknown role",
    "company_name": "N/A",
    "location_city": "Unknown",
    "location_country": "Unknown",
    "remote_type": "on-site",
    "employment_type": "full-time",
    "seniority_level": "mid",
    "min_experience_years": 0,
    "max_experience_years": 0,
    "description": None,
    "required_skills": [],
    "preferred_skills": [],
    "posted_date": None,
    "category": None,
    "salary_range": None,
}


def match_job_fields(job: Optional[JobPosting]) -> dict:
    """
    The job half of a match payload.

    A match carries the role's name as `job_title`, which is what MatchResult
    and the frontend's Match type both call it, so `title` is renamed rather
    than sent alongside -- one name per concept in this response too.
    """
    fields = dict(job_payload(job)) if job else dict(MISSING_JOB_PAYLOAD)
    fields["job_title"] = fields.pop("title")
    return fields


def job_matches_filters(
    job: JobPosting,
    search: Optional[str],
    category: Optional[str],
    remote_type: Optional[str],
    seniority: Optional[str],
) -> bool:
    """
    Whether one job survives the /jobs filter set. All filters are AND-ed;
    an unset filter matches everything.
    """
    if search:
        needle = search.lower()
        haystack = " ".join(
            filter(
                None,
                [
                    job.title,
                    job.company_name,
                    job.location_city,
                    job.description,
                    " ".join(job.required_skills or []),
                    " ".join(job.preferred_skills or []),
                ],
            )
        ).lower()
        if needle not in haystack:
            return False

    if category and (getattr(job, "category", "") or "").lower() != category.lower():
        return False
    if remote_type and (job.remote_type or "").lower() != remote_type.lower():
        return False
    if seniority and (job.seniority_level or "").lower() != seniority.lower():
        return False
    return True


@app.get("/jobs")
async def get_jobs(
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max jobs to return"),
    search: Optional[str] = Query(
        None, description="Free text over title, company, city, skills and description"
    ),
    category: Optional[str] = Query(None, description="Exact job category"),
    remote_type: Optional[str] = Query(None, description="remote | hybrid | on-site"),
    seniority: Optional[str] = Query(
        None, description="entry | mid | senior | lead | manager | executive"
    ),
):
    """
    List available jobs, optionally filtered.

    Filtering happens here rather than in the browser. The corpus is 800 jobs
    and the page requests 12 at a time, so a client-side filter can only ever
    search the current page -- which is why the Jobs search box did nothing:
    the parameter was sent and silently dropped.
    """
    matching = [
        job
        for job in jobs_cache
        if job_matches_filters(job, search, category, remote_type, seniority)
    ]

    paginated_jobs = matching[skip : skip + limit]

    return {
        # The count of jobs that matched the filters, not the corpus size.
        # Paging past the end of a filtered result set depends on this.
        "total": len(matching),
        "corpus_total": len(jobs_cache),
        "skip": skip,
        "limit": limit,
        "count": len(paginated_jobs),
        "filters": {
            "search": search,
            "category": category,
            "remote_type": remote_type,
            "seniority": seniority,
        },
        "jobs": [job_payload(job) for job in paginated_jobs],
    }


@app.get("/stats")
async def get_stats():
    """
    The figures the landing page quotes, measured from the running system.

    This endpoint exists so that page cannot drift from reality. Marketing
    numbers written into markup are the same defect as the "3,000+ jobs" copy
    that sat above a 4,000-row load of a 6,146-row file, and the "45 technical
    skills" the pipeline panel claimed on every run -- both were true once, or
    never, and neither could be checked by looking at them.

    Deliberately absent: a model accuracy figure. The classifier reports 99.3%
    accuracy and a 1.000 ROC-AUC on its test split, and TASKS.md 1.4 records
    why quoting that would be dishonest -- the label is a threshold on a column
    the model does not even train on, so two ordinary features reproduce it. A
    headline "99% accurate" would contradict the most careful piece of analysis
    in this repository.
    """
    countries = {job.location_country for job in jobs_cache if job.location_country}
    cities = {job.location_city for job in jobs_cache if job.location_city}
    companies = {job.company_name for job in jobs_cache if job.company_name}

    skills = set()
    for job in jobs_cache:
        skills.update(job.required_skills or [])
        skills.update(job.preferred_skills or [])

    # Roles per country, largest first -- what the map plots.
    per_country: dict[str, int] = {}
    for job in jobs_cache:
        if job.location_country:
            per_country[job.location_country] = per_country.get(job.location_country, 0) + 1

    ml_enabled = pipeline.agent3.ml_scorer.enabled
    model_info = pipeline.agent3.ml_scorer.predictor.get_model_info() if ml_enabled else {}

    # The vocabulary Agent 2 is actually running, not the file on disk: those
    # differ whenever a caller injects one, and it is the loaded index that
    # decides what gets extracted.
    alias_index = getattr(pipeline.agent2, "skills_index", {}) or {}

    return {
        "corpus": {
            "jobs": len(jobs_cache),
            "countries": len(countries),
            "cities": len(cities),
            "companies": len(companies),
            "distinct_skills": len(skills),
            # Every country, ranked -- not a top-N slice. The landing map
            # plots one node per market and the headline says how many there
            # are, so a truncated list would draw 12 nodes under a sentence
            # claiming 27. Callers that want fewer can slice; a caller cannot
            # un-truncate.
            "top_countries": sorted(
                ({"country": c, "jobs": n} for c, n in per_country.items()),
                key=lambda row: row["jobs"],
                reverse=True,
            ),
        },
        "engine": {
            "agents": 4,
            "ml_model_loaded": ml_enabled,
            "model_name": model_info.get("model_name") if ml_enabled else None,
            "scoring_mode": "hybrid" if ml_enabled else "rule_based_only",
            "canonical_skills": len(set(alias_index.values())),
            "skill_aliases": len(alias_index),
            "explanation_provider": get_config().llm.provider,
        },
    }


@app.get("/jobs/facets")
async def get_job_facets():
    """
    The distinct values behind the Jobs filter dropdowns.

    Hardcoding the options in the UI means the dropdown and the corpus drift
    apart, and a user can select a value that matches nothing.
    """

    def distinct(attr: str) -> List[str]:
        return sorted({value for job in jobs_cache if (value := getattr(job, attr, None))})

    return {
        "categories": distinct("category"),
        "remote_types": distinct("remote_type"),
        "seniority_levels": distinct("seniority_level"),
        "employment_types": distinct("employment_type"),
        "total": len(jobs_cache),
    }


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """One job in full. Backs the job detail page."""
    job = next((j for j in jobs_cache if j.job_id == job_id), None)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    payload = job_payload(job)
    # The list view truncates skills to keep the grid light. A detail page
    # showing a truncated requirement list would be actively misleading.
    payload["required_skills"] = job.required_skills or []
    payload["preferred_skills"] = job.preferred_skills or []
    payload["education_level"] = getattr(job, "education_level", None)
    return payload


@app.get("/jobs/{job_id}/candidates")
async def candidates_for_job(job_id: str, limit: int = Query(20, ge=1, le=100)):
    """
    The matcher run backwards: for this role, who has scored well.

    Every other view starts from a CV and ranks roles. A recruiter works the
    other way round, and the data for it was already there -- `/match` writes a
    row per returned match, so a job accumulates the candidates it ranked highly
    for.

    Two things this is not, stated because the difference matters:

    - It is not a fresh scoring pass. These are the numbers the pipeline
      produced from complete profiles. `match_history` does not store enough of
      a candidate to recompute them, and a recomputed number wearing the same
      name would be worse than no number.
    - It is not every candidate. `/match` persists the top matches per upload,
      so a candidate appears here when this role was among their best -- which
      is the useful set anyway, and `scored_against` says how many that is.
    """
    if not any(j.job_id == job_id for j in jobs_cache):
        raise HTTPException(404, f"Job {job_id} not found")

    rows = get_database().get_candidates_for_job(job_id, limit=limit)

    return {
        "job_id": job_id,
        "scored_against": len(rows),
        "candidates": [
            {
                "cv_id": row.cv_id,
                "match_id": row.match_id,
                "candidate_name": row.candidate_name,
                "candidate_email": row.candidate_email,
                "final_score": round(row.final_score * 100, 1),
                "skill_score": round(row.skill_score * 100, 1),
                "experience_score": round(row.experience_score * 100, 1),
                "status": row.decision,
                "matched_skills": _decode_skill_list(row.matched_skills),
                "missing_skills": _decode_skill_list(row.missing_skills),
                "analysed_at": row.created_at,
            }
            for row in rows
        ],
    }


# ------------------------------------------------------------- job writes --
#
# Until now every write endpoint concerned a CV. The corpus was a JSON file read
# at startup, so an applicant tracking system presented Jobs, Shortlist, History
# and Results over a dataset nobody could change. These three close that.
#
# `JobPosting` is the request body as well as the storage model, so validation is
# the same rules the scorer already relies on -- a job that cannot be scored
# cannot be created either.
#
# All three are rate limited. There is no authentication in this system -- that
# was considered and deliberately deferred -- so on a public URL these are open
# write endpoints, and the per-IP limit is the only thing standing between the
# corpus and whoever finds them. It is not a substitute for auth; it is what
# keeps the gap from being unbounded until auth exists.


@app.post("/jobs", status_code=201)
@limiter.limit(_api_config.upload_rate_limit)
async def create_job(request: Request, job: JobPosting):
    """
    Add a role to the corpus.

    409 rather than an overwrite when the id is taken: silently replacing a job
    someone else created is worse than refusing.
    """
    if not get_database().create_job(job):
        raise HTTPException(409, f"Job {job.job_id} already exists")

    total = refresh_corpus()
    logger.info(f"Created job {job.job_id}; corpus now {total}")
    return job_payload(job)


@app.put("/jobs/{job_id}")
@limiter.limit(_api_config.upload_rate_limit)
async def update_job(request: Request, job_id: str, job: JobPosting):
    """
    Replace a role.

    The id in the path wins. Allowing the body to rename a job would make this
    endpoint a create-and-delete wearing an update's clothes, and the caller
    would have no way to tell which record it had actually touched.
    """
    if job.job_id != job_id:
        job = job.model_copy(update={"job_id": job_id})

    if not get_database().update_job(job_id, job):
        raise HTTPException(404, f"Job {job_id} not found")

    refresh_corpus()
    logger.info(f"Updated job {job_id}")
    return job_payload(job)


@app.delete("/jobs/{job_id}")
@limiter.limit(_api_config.upload_rate_limit)
async def delete_job(request: Request, job_id: str):
    """
    Remove a role from the corpus.

    Match history is deliberately left alone. Those rows record what was scored
    at the time, and deleting a job does not make yesterday's match untrue --
    rewriting history to match the present is how an audit trail stops being one.
    """
    if not get_database().delete_job(job_id):
        raise HTTPException(404, f"Job {job_id} not found")

    total = refresh_corpus()
    logger.info(f"Deleted job {job_id}; corpus now {total}")
    return {"deleted": job_id, "corpus_total": total}


@app.post("/upload")
@limiter.limit(_api_config.upload_rate_limit)
async def upload_cv(request: Request, file: UploadFile = File(...)):
    """
    Upload and parse CV file

    Extracts basic information:
    - Name, email, phone
    - Skills list
    - Years of experience
    - Education level

    Returns extracted data without matching
    """
    logger.info(f"Uploading file: {file.filename}")

    content, file_ext = await read_upload(file)

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Parse with Agent 1
        logger.info("Parsing CV with Agent 1...")
        parse_result = pipeline.agent1.parse_file(tmp_path)
        cv_text = parse_result.get("raw_text", "")

        if not cv_text or len(cv_text) < 50:
            raise HTTPException(400, "Could not extract meaningful text from CV")

        # Extract structured data with Agent 2
        logger.info("Extracting data with Agent 2...")
        extracted = pipeline.agent2.extract(cv_text)

        return {
            "success": True,
            "filename": file.filename,
            "file_type": file_ext,
            "text_length": len(cv_text),
            "extracted_data": {
                "name": extracted.get("name"),
                "email": extracted.get("email"),
                "phone": extracted.get("phone"),
                "skills": extracted.get("skills", []),
                "experience_years": extracted.get("experience_years"),
                "education": extracted.get("education"),
                "certifications": extracted.get("certifications"),
                "projects_count": extracted.get("projects_count", 0),
            },
            "preview": cv_text[:500] + "..." if len(cv_text) > 500 else cv_text,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process CV: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to process CV: {str(e)}") from e

    finally:
        # Clean up temporary file. Narrow: a bare except here would also
        # swallow KeyboardInterrupt and SystemExit, and would hide a genuine
        # permission problem that leaks a temp file on every request.
        try:
            Path(tmp_path).unlink()
        except OSError as e:
            logger.warning(f"Could not remove temp file {tmp_path}: {e}")


@app.post("/match")
@limiter.limit(_api_config.match_rate_limit)
async def match_cv(
    request: Request,
    file: UploadFile = File(..., description="CV file (PDF, DOCX, or TXT)"),
    top_k: int = Query(10, ge=1, le=50, description="Number of top matches to return"),
    explain: bool = Query(False, description="Generate AI explanations (slower)"),
    use_llm: bool = Query(False, description="Enable Ollama LLM (if false, uses rule-based only)"),
    use_langchain: bool = Query(False, description="Use LangChain for advanced AI features"),
):
    """
    Match CV to all jobs and return top K matches

    This is the MAIN endpoint for resume-job matching!

    Process:
    1. Parse CV file (Agent 1)
    2. Extract structured data (Agent 2)
    3. Score against all jobs (Agent 3)
    4. Optionally generate explanations (Agent 4)

    Returns top K matches sorted by score
    """
    logger.info(
        f"Matching CV: {file.filename} (top_k={top_k}, explain={explain}, use_llm={use_llm})"
    )

    if not jobs_cache:
        raise HTTPException(503, "No jobs loaded. Please contact administrator.")

    content, file_ext = await read_upload(file)

    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Per-request options are arguments, not mutations of the shared
        # pipeline.
        #
        # This block used to reassign pipeline.agent4 and flip
        # pipeline.agent4.llm_available for the duration of the request, then
        # put them back. The pipeline is a module-level singleton, so two
        # concurrent requests with different settings saw each other's; and the
        # restore was not in a finally block, so any request that raised in
        # between left the singleton altered for every request after it.
        logger.info(f"Running pipeline against {len(jobs_cache)} jobs...")

        started = time.perf_counter()
        matches = pipeline.process_cv_batch(
            cv_file_path=tmp_path,
            jobs=jobs_cache,
            top_k=top_k,
            generate_explanations=explain,
            use_llm=use_llm,
            use_langchain=use_langchain,
        )
        elapsed = time.perf_counter() - started

        # Format results for Next.js frontend
        results = []
        for match in matches:
            # Get job details from cache
            job_details = next((j for j in jobs_cache if j.job_id == match.job_id), None)

            # Calculate final score
            final_score = round(match.score_breakdown.hybrid_score * 100, 1)

            # Auto-assign status based on score
            if final_score >= 75:
                status = "accepted"  # Shortlist
            elif final_score >= 50:
                status = "review"  # Manual review needed
            else:
                status = "rejected"  # Below threshold

            result = {
                "match_id": match.match_id,
                "job_id": match.job_id,
                **match_job_fields(job_details),
                "candidate_name": match.candidate_name,  # From MatchResult
                "cv_filename": file.filename,
                "final_score": final_score,
                # Named for what they measure. These went out as parser_score,
                # matcher_score and scorer_score -- named after the agent the
                # caller assumed produced them, which is wrong for all three.
                # The UI accordingly labelled the skill score "ATS" and the
                # experience score "Matching". See TASKS.md 5.9.
                "rule_based_score": round(match.score_breakdown.rule_based_score * 100, 1),
                "skill_score": round(match.score_breakdown.skill_score * 100, 1),
                "experience_score": round(match.score_breakdown.experience_score * 100, 1),
                # The remaining three weighted components. /match/single already
                # returned all five; /match returned two of them, so a client
                # could show a rule-based total it had no way to decompose --
                # which is the one thing this payload exists to make possible.
                "title_score": round(match.score_breakdown.title_score * 100, 1),
                "education_score": round(match.score_breakdown.education_score * 100, 1),
                "keyword_score": round(match.score_breakdown.keyword_score * 100, 1),
                "ml_score": (
                    round(match.score_breakdown.ml_score * 100, 1)
                    if match.score_breakdown.ml_score is not None
                    else None
                ),
                # MatchCard renders skill badges from these two fields. Only
                # /match/single sent them (nested as skills.matched/.missing),
                # so on this endpoint - the one the UI actually calls - the
                # badges were always empty. Flat names to match what the
                # component and the Match type expect. See TASKS.md 1.5.
                "matched_skills": match.score_breakdown.matched_skills,
                "missing_skills": match.score_breakdown.missing_skills,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            }

            # Add explanation if requested, with what produced it.
            #
            # The provenance is the point. A rule-based fallback -- after a
            # connection failure, an exhausted quota, or no key at all --
            # produces prose just as plausible as the model's, so without this
            # field a degraded demo is indistinguishable from a working one.
            # The pipeline already recorded it; nothing served it.
            if explain and match.decision.explanation:
                result["explanation"] = match.decision.explanation
                result["explanation_source"] = match.explanation_source

            results.append(result)

        logger.info(f"Matching complete. Found {len(results)} matches in {elapsed:.2f}s.")

        # Return format matching Next.js frontend MatchResponse interface
        return {
            "matches": results,
            "cv_text": None,  # Optional field
            # Measured, not None. The dashboard used to sit through 2.5s of
            # hardcoded setTimeout to imply work that had already finished,
            # then report no duration at all.
            "processing_time": round(elapsed, 3),
            "jobs_evaluated": len(jobs_cache),
            # Scoring provenance. Without this, a caller cannot tell whether the
            # scores came from the advertised hybrid ML+rules path or from the
            # rule-based fallback that runs when the model fails to load. Both
            # produce plausible numbers, so the difference is invisible unless
            # it is stated. See TASKS.md 1.1.
            "ml_scoring_enabled": pipeline.agent3.ml_scorer.enabled,
            "scoring_mode": ("hybrid" if pipeline.agent3.ml_scorer.enabled else "rule_based_only"),
        }

    except Exception as e:
        logger.error(f"Matching failed: {e}", exc_info=True)
        raise HTTPException(500, f"Matching failed: {str(e)}") from e

    finally:
        # Clean up temporary file. Narrow: a bare except here would also
        # swallow KeyboardInterrupt and SystemExit, and would hide a genuine
        # permission problem that leaks a temp file on every request.
        try:
            Path(tmp_path).unlink()
        except OSError as e:
            logger.warning(f"Could not remove temp file {tmp_path}: {e}")


@app.post("/match/single")
@limiter.limit(_api_config.match_rate_limit)
async def match_to_single_job(
    request: Request,
    file: UploadFile = File(...),
    job_id: str = Query(..., description="Job ID to match against"),
    explain: bool = Query(True, description="Generate AI explanation"),
):
    """
    Match CV to a specific job

    More detailed than batch matching, includes full explanation
    """
    logger.info(f"Matching {file.filename} to job {job_id}")

    # Find the job
    job = next((j for j in jobs_cache if j.job_id == job_id), None)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    content, file_ext = await read_upload(file)

    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Run full 4-agent pipeline for single job
        logger.info(f"Running full pipeline for job: {job.title}")

        match = pipeline.process_cv_for_job(
            cv_file_path=tmp_path, job=job, generate_explanation=explain
        )

        return {
            "success": True,
            "match_id": match.match_id,
            "cv_filename": file.filename,
            "job": {
                "job_id": match.job_id,
                "title": match.job_title,
                "company": getattr(job, "company", "N/A"),
                "required_skills": job.required_skills[:10],
                "min_experience": job.min_experience_years,
            },
            "result": {
                "score": round(match.score_breakdown.hybrid_score * 100, 1),
                "decision": match.decision.decision.value,
                "confidence": round(match.decision.confidence * 100, 1),
                "reason": match.decision.reason,
            },
            "scores_breakdown": {
                "skill_match": round(match.score_breakdown.skill_score * 100, 1),
                "title_match": round(match.score_breakdown.title_score * 100, 1),
                "experience_match": round(match.score_breakdown.experience_score * 100, 1),
                "education_match": round(match.score_breakdown.education_score * 100, 1),
                "keyword_match": round(match.score_breakdown.keyword_score * 100, 1),
                "rule_based_score": round(match.score_breakdown.rule_based_score * 100, 1),
                "ml_score": (
                    round(match.score_breakdown.ml_score * 100, 1)
                    if match.score_breakdown.ml_score
                    else None
                ),
                "hybrid_score": round(match.score_breakdown.hybrid_score * 100, 1),
            },
            "skills": {
                "matched": match.score_breakdown.matched_skills,
                "missing": match.score_breakdown.missing_skills,
                "extra": match.score_breakdown.extra_skills[:10],
            },
            "insights": {
                "strengths": match.decision.strengths,
                "red_flags": match.decision.red_flags,
                "recommendations": match.decision.recommendations,
                "overqualified": match.score_breakdown.overqualified,
                "underqualified": match.score_breakdown.underqualified,
            },
            "explanation": match.decision.explanation if explain else None,
            "explanation_source": match.explanation_source,
            # MatchResult has created_at, not timestamp. This raised
            # AttributeError on every call, so /match/single always 500'd.
            "timestamp": match.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Single job matching failed: {e}", exc_info=True)
        raise HTTPException(500, f"Matching failed: {str(e)}") from e

    finally:
        # Clean up temporary file. Narrow: a bare except here would also
        # swallow KeyboardInterrupt and SystemExit, and would hide a genuine
        # permission problem that leaks a temp file on every request.
        try:
            Path(tmp_path).unlink()
        except OSError as e:
            logger.warning(f"Could not remove temp file {tmp_path}: {e}")


# GET /history is gone.
#
# It served the same rows as /match/history under a different, incompatible
# shape -- `score` instead of `final_score`, `cv_name` instead of
# `candidate_name`, a flat `decision` string where the other returns a status.
# No client called it: the frontend has only ever used /match/history. Two
# encodings of one resource is how the two drifted far enough apart that one
# of them could return 500 on every call for months without anyone noticing.
# See TASKS.md 5.8.


def _decode_skill_list(raw) -> List[str]:
    """
    MatchHistory stores skills as a JSON string. Rows written before that
    column existed hold None, and a hand-edited database can hold anything.
    """
    if isinstance(raw, list):
        return raw
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return decoded if isinstance(decoded, list) else []


@app.get("/match/history")
async def get_match_history_v2(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
):
    """
    Get match history from database (Next.js frontend compatible)

    Returns recent CV-job matches with format matching frontend TypeScript types
    """
    try:
        # Get matches from database using correct method
        all_matches = db.get_top_matches(limit=1000)  # Get recent matches

        # Paginate
        total = len(all_matches)
        paginated_matches = all_matches[skip : skip + limit]

        # Format for Next.js frontend
        formatted_matches = []
        for m in paginated_matches:
            # Get full job details from cache using job_id
            job_details = next((j for j in jobs_cache if j.job_id == m.job_id), None)

            # Calculate final score
            final_score = round(m.final_score * 100, 1)

            # Auto-assign status based on score
            if final_score >= 75:
                status = "accepted"
            elif final_score >= 50:
                status = "review"
            else:
                status = "rejected"

            formatted_match = {
                "match_id": m.match_id,
                "job_id": m.job_id,
                **match_job_fields(job_details),
                # The stored title wins when the job has since left the corpus,
                # so a history row still names the role it was scored against.
                "job_title": m.job_title,
                "candidate_name": getattr(m, "candidate_name", None),
                # cv_id is a UUID. It went out as `cv_filename`, so the history
                # table printed a raw UUID under every candidate's name as
                # though it were the document they uploaded. The filename is
                # not stored, so the honest answer is null.
                "cv_id": getattr(m, "cv_id", None),
                "cv_filename": None,
                # Use individual score fields from MatchHistory. Same names as
                # /match: one match shape, whether it arrived from a live run
                # or from storage.
                "final_score": final_score,
                "rule_based_score": round(m.rule_based_score * 100, 1),
                "skill_score": round(m.skill_score * 100, 1),
                "experience_score": round(m.experience_score * 100, 1),
                "ml_score": (round(m.ml_score * 100, 1) if m.ml_score is not None else None),
                # Stored on every row and never served, so History and
                # Shortlist rendered no skill badges at all.
                "matched_skills": _decode_skill_list(getattr(m, "matched_skills", None)),
                "missing_skills": _decode_skill_list(getattr(m, "missing_skills", None)),
                "status": status,
                "explanation": getattr(m, "explanation", None),
                # Null, not guessed. MatchHistory has no column for the
                # provider, so a stored explanation cannot say what wrote it;
                # claiming a source here would be worse than admitting the gap.
                "explanation_source": None,
                "timestamp": (
                    m.created_at.isoformat()
                    if hasattr(m, "created_at")
                    else datetime.now().isoformat()
                ),
            }
            formatted_matches.append(formatted_match)

        return {"matches": formatted_matches, "total": total}

    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(500, f"Failed to retrieve history: {str(e)}") from e


@app.delete("/match/history")
async def clear_match_history():
    """
    Clear all match history from database

    WARNING: This permanently deletes all match records!
    """
    try:
        deleted_count = db.clear_all_matches()
        logger.info(f"Cleared {deleted_count} matches from database")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully cleared {deleted_count} match records",
        }

    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        raise HTTPException(500, f"Failed to clear history: {str(e)}") from e


# ============================================
# STARTUP & SHUTDOWN
# ============================================

# ============================================
# RUN SERVER (for development)
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
    )
