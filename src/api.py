"""
Recruiter-Pro-AI: Simple Unified API Server
Clean, straightforward REST API for resume-job matching

Endpoints:
- GET  /              - Welcome message
- GET  /health        - Server health check
- GET  /jobs          - List available jobs
- POST /upload        - Upload and parse CV
- POST /match         - Match CV to all jobs (main endpoint)
- POST /match/single  - Match CV to specific job
- GET  /history       - View match history
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import tempfile
from pathlib import Path
import json
import logging
from datetime import datetime

from src.agents.pipeline import MatchingPipeline
from src.storage.database import get_database
from src.storage.models import JobPosting

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# FASTAPI APP SETUP
# ============================================

app = FastAPI(
    title="Recruiter Pro AI",
    description="AI-powered resume matching with 4-agent pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# GLOBAL COMPONENTS
# ============================================

# Initialize pipeline and database
pipeline = MatchingPipeline(save_to_db=True)
db = get_database()

# Jobs cache (loaded on startup)
jobs_cache: List[JobPosting] = []


def load_jobs() -> List[JobPosting]:
    """
    Load the job corpus.

    The corpus is an object with a metadata envelope and a "jobs" array, not a
    bare array - see JOBS_DATASET_SPEC.md. The legacy pipe-separated shape and
    the jobs_cleaned.json fallback were removed when that corpus was archived
    (data/archive/jobs-legacy-2026-08-09/); nothing produces them any more.
    """
    jobs_path = Path("data/json/jobs.json")

    if not jobs_path.exists():
        logger.warning(f"Jobs file not found: {jobs_path}")
        return []

    try:
        with open(jobs_path, 'r', encoding='utf-8') as f:
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
        "message": "🎯 Recruiter Pro AI - API Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "jobs": "/jobs",
            "upload": "/upload",
            "match": "/match"
        }
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
            "ml_model_loaded": pipeline.agent3.ml_predictor is not None,
            "database_ready": db is not None,
            "ollama_enabled": pipeline.config.llm.enabled if hasattr(pipeline, 'config') else False
        }
    }


@app.get("/jobs")
async def get_jobs(
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max jobs to return")
):
    """
    Get list of available jobs
    Returns paginated job listings with new structure
    """
    total_jobs = len(jobs_cache)
    paginated_jobs = jobs_cache[skip:skip+limit]
    
    return {
        "total": total_jobs,
        "skip": skip,
        "limit": limit,
        "count": len(paginated_jobs),
        "jobs": [
            {
                "job_id": job.job_id,
                "title": job.title,
                "job_title": job.title,  # Legacy compatibility
                "company_name": job.company_name,
                "company": job.company_name,  # Legacy compatibility
                "location_city": job.location_city,
                "location_country": job.location_country,
                "location": f"{job.location_city}, {job.location_country}",  # Legacy compatibility
                "remote_type": job.remote_type,
                "employment_type": job.employment_type,
                "job_type": job.employment_type,  # Legacy compatibility
                "seniority_level": job.seniority_level,
                "min_experience_years": job.min_experience_years,
                "max_experience_years": job.max_experience_years,
                "description": job.description,
                "required_skills": job.required_skills[:10] if job.required_skills else [],
                "preferred_skills": job.preferred_skills[:5] if job.preferred_skills else [],
                "posted_date": job.posted_date
            }
            for job in paginated_jobs
        ]
    }


@app.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
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
    
    # Validate file type
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.docx', '.txt']:
        raise HTTPException(400, f"Unsupported file type: {file_ext}. Use PDF, DOCX, or TXT")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Parse with Agent 1
        logger.info("Parsing CV with Agent 1...")
        parse_result = pipeline.agent1.parse_file(tmp_path)
        cv_text = parse_result.get('raw_text', '')
        
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
                "name": extracted.get('name'),
                "email": extracted.get('email'),
                "phone": extracted.get('phone'),
                "skills": extracted.get('skills', []),
                "experience_years": extracted.get('experience_years'),
                "education": extracted.get('education'),
                "certifications": extracted.get('certifications'),
                "projects_count": extracted.get('projects_count', 0)
            },
            "preview": cv_text[:500] + "..." if len(cv_text) > 500 else cv_text
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process CV: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to process CV: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            Path(tmp_path).unlink()
        except:
            pass


@app.post("/match")
async def match_cv(
    file: UploadFile = File(..., description="CV file (PDF, DOCX, or TXT)"),
    top_k: int = Query(10, ge=1, le=50, description="Number of top matches to return"),
    explain: bool = Query(False, description="Generate AI explanations (slower)"),
    use_llm: bool = Query(False, description="Enable Ollama LLM (if false, uses rule-based only)"),
    use_langchain: bool = Query(False, description="Use LangChain for advanced AI features")
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
    logger.info(f"Matching CV: {file.filename} (top_k={top_k}, explain={explain}, use_llm={use_llm})")
    
    if not jobs_cache:
        raise HTTPException(503, "No jobs loaded. Please contact administrator.")
    
    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.docx', '.txt']:
        raise HTTPException(400, f"Unsupported file type: {file_ext}")
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Handle LangChain mode switch if requested
        original_agent = pipeline.agent4
        if use_langchain and not hasattr(pipeline.agent4, 'chain'):
            # Need to swap to LangChain agent
            from src.agents.agent4_factory import get_explainer_agent
            pipeline.agent4 = get_explainer_agent(use_langchain=True, config=pipeline.config)
            logger.info("🔄 Switched to LangChain mode for this request")
        
        # Temporarily disable LLM if use_llm is False
        original_llm_enabled = pipeline.agent4.llm_available
        if not use_llm:
            pipeline.agent4.llm_available = False
            logger.info("⚙️ LLM disabled - using rule-based explanations only")
        
        # Run full 4-agent pipeline on all jobs
        logger.info(f"Running pipeline against {len(jobs_cache)} jobs...")
        
        matches = pipeline.process_cv_batch(
            cv_file_path=tmp_path,
            jobs=jobs_cache,
            top_k=top_k,
            generate_explanations=explain
        )
        
        # Restore original settings
        if not use_llm:
            pipeline.agent4.llm_available = original_llm_enabled
        if use_langchain and not hasattr(original_agent, 'chain'):
            pipeline.agent4 = original_agent  # Restore original agent
        
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
                status = "review"    # Manual review needed
            else:
                status = "rejected"  # Below threshold
            
            result = {
                "match_id": match.match_id,
                "job_id": match.job_id,
                "job_title": match.job_title,
                # New structure fields
                "company_name": job_details.company_name if job_details else 'N/A',
                "company": job_details.company_name if job_details else 'N/A',  # Legacy
                "location_city": job_details.location_city if job_details else 'Unknown',
                "location_country": job_details.location_country if job_details else 'India',
                "location": f"{job_details.location_city}, {job_details.location_country}" if job_details else 'Unknown',  # Legacy
                "remote_type": job_details.remote_type if job_details else 'on-site',
                "employment_type": job_details.employment_type if job_details else 'full-time',
                "job_type": job_details.employment_type if job_details else 'full-time',  # Legacy
                "seniority_level": job_details.seniority_level if job_details else 'mid',
                "min_experience_years": job_details.min_experience_years if job_details else 0,
                "max_experience_years": job_details.max_experience_years if job_details else 0,
                "description": job_details.description if job_details else None,
                "required_skills": job_details.required_skills[:10] if job_details and job_details.required_skills else [],
                "preferred_skills": job_details.preferred_skills[:5] if job_details and job_details.preferred_skills else [],
                "posted_date": job_details.posted_date if job_details else None,
                "candidate_name": match.candidate_name,  # From MatchResult
                "cv_filename": file.filename,
                "final_score": final_score,
                "parser_score": round(match.score_breakdown.rule_based_score * 100, 1),
                "matcher_score": round(match.score_breakdown.skill_score * 100, 1),
                "scorer_score": round(match.score_breakdown.experience_score * 100, 1),
                # MatchCard renders skill badges from these two fields. Only
                # /match/single sent them (nested as skills.matched/.missing),
                # so on this endpoint - the one the UI actually calls - the
                # badges were always empty. Flat names to match what the
                # component and the Match type expect. See TASKS.md 1.5.
                "matched_skills": match.score_breakdown.matched_skills,
                "missing_skills": match.score_breakdown.missing_skills,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add explanation if requested
            if explain and match.decision.explanation:
                result["explanation"] = match.decision.explanation
            
            results.append(result)
        
        logger.info(f"Matching complete. Found {len(results)} matches.")
        
        # Return format matching Next.js frontend MatchResponse interface
        return {
            "matches": results,
            "cv_text": None,  # Optional field
            "processing_time": None,  # Optional field
            # Scoring provenance. Without this, a caller cannot tell whether the
            # scores came from the advertised hybrid ML+rules path or from the
            # rule-based fallback that runs when the model fails to load. Both
            # produce plausible numbers, so the difference is invisible unless
            # it is stated. See TASKS.md 1.1.
            "ml_scoring_enabled": pipeline.agent3.ml_predictor is not None,
            "scoring_mode": (
                "hybrid" if pipeline.agent3.ml_predictor is not None else "rule_based_only"
            )
        }
    
    except Exception as e:
        logger.error(f"Matching failed: {e}", exc_info=True)
        raise HTTPException(500, f"Matching failed: {str(e)}")
    
    finally:
        # Clean up
        try:
            Path(tmp_path).unlink()
        except:
            pass


@app.post("/match/single")
async def match_to_single_job(
    file: UploadFile = File(...),
    job_id: str = Query(..., description="Job ID to match against"),
    explain: bool = Query(True, description="Generate AI explanation")
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
    
    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.docx', '.txt']:
        raise HTTPException(400, f"Unsupported file type: {file_ext}")
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Run full 4-agent pipeline for single job
        logger.info(f"Running full pipeline for job: {job.title}")
        
        match = pipeline.process_cv_for_job(
            cv_file_path=tmp_path,
            job=job,
            generate_explanation=explain
        )
        
        return {
            "success": True,
            "match_id": match.match_id,
            "cv_filename": file.filename,
            "job": {
                "job_id": match.job_id,
                "title": match.job_title,
                "company": getattr(job, 'company', 'N/A'),
                "required_skills": job.required_skills[:10],
                "min_experience": job.min_experience_years
            },
            "result": {
                "score": round(match.score_breakdown.hybrid_score * 100, 1),
                "decision": match.decision.decision.value,
                "confidence": round(match.decision.confidence * 100, 1),
                "reason": match.decision.reason
            },
            "scores_breakdown": {
                "skill_match": round(match.score_breakdown.skill_score * 100, 1),
                "experience_match": round(match.score_breakdown.experience_score * 100, 1),
                "education_match": round(match.score_breakdown.education_score * 100, 1),
                "keyword_match": round(match.score_breakdown.keyword_score * 100, 1),
                "rule_based_score": round(match.score_breakdown.rule_based_score * 100, 1),
                "ml_score": round(match.score_breakdown.ml_score * 100, 1) if match.score_breakdown.ml_score else None,
                "hybrid_score": round(match.score_breakdown.hybrid_score * 100, 1)
            },
            "skills": {
                "matched": match.score_breakdown.matched_skills,
                "missing": match.score_breakdown.missing_skills,
                "extra": match.score_breakdown.extra_skills[:10]
            },
            "insights": {
                "strengths": match.decision.strengths,
                "red_flags": match.decision.red_flags,
                "recommendations": match.decision.recommendations,
                "overqualified": match.score_breakdown.overqualified,
                "underqualified": match.score_breakdown.underqualified
            },
            "explanation": match.decision.explanation if explain else None,
            "timestamp": match.timestamp.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Single job matching failed: {e}", exc_info=True)
        raise HTTPException(500, f"Matching failed: {str(e)}")
    
    finally:
        try:
            Path(tmp_path).unlink()
        except:
            pass


@app.get("/history")
async def get_match_history(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get match history from database (legacy endpoint)
    
    Returns recent CV-job matches stored in the system
    """
    try:
        # Get matches from database
        all_matches = db.get_all_matches()
        
        # Paginate
        total = len(all_matches)
        matches = all_matches[skip:skip+limit]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(matches),
            "matches": [
                {
                    "match_id": m.match_id,
                    "cv_id": m.cv_id,
                    "cv_name": m.cv_name,
                    "job_id": m.job_id,
                    "job_title": m.job_title,
                    "score": round(m.score_breakdown.hybrid_score * 100, 1),
                    "decision": m.decision.decision.value,
                    "confidence": round(m.decision.confidence * 100, 1),
                    "timestamp": m.timestamp.isoformat()
                }
                for m in matches
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(500, f"Failed to get history: {str(e)}")


@app.get("/match/history")
async def get_match_history_v2(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip")
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
        paginated_matches = all_matches[skip:skip+limit]
        
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
                "job_title": m.job_title,
                # New structure fields from job cache
                "company_name": job_details.company_name if job_details else 'N/A',
                "company": job_details.company_name if job_details else 'N/A',  # Legacy
                "location_city": job_details.location_city if job_details else 'Unknown',
                "location_country": job_details.location_country if job_details else 'Unknown',
                "location": f"{job_details.location_city}, {job_details.location_country}" if job_details else 'Unknown',  # Legacy
                "remote_type": job_details.remote_type if job_details else 'on-site',
                "employment_type": job_details.employment_type if job_details else 'full-time',
                "job_type": job_details.employment_type if job_details else 'full-time',  # Legacy
                "seniority_level": job_details.seniority_level if job_details else 'mid',
                "min_experience_years": job_details.min_experience_years if job_details else 0,
                "max_experience_years": job_details.max_experience_years if job_details else 0,
                "description": job_details.description if job_details else None,
                "required_skills": job_details.required_skills[:10] if job_details and job_details.required_skills else [],
                "preferred_skills": job_details.preferred_skills[:5] if job_details and job_details.preferred_skills else [],
                "posted_date": job_details.posted_date if job_details else None,
                "candidate_name": getattr(m, 'candidate_name', None),
                "cv_filename": getattr(m, 'cv_id', None),  # Use cv_id as filename fallback
                # Use individual score fields from MatchHistory
                "final_score": final_score,
                "parser_score": round(m.rule_based_score * 100, 1),
                "matcher_score": round(m.skill_score * 100, 1),
                "scorer_score": round(m.experience_score * 100, 1),
                "status": status,
                "explanation": getattr(m, 'explanation', None),
                "timestamp": m.created_at.isoformat() if hasattr(m, 'created_at') else datetime.now().isoformat()
            }
            formatted_matches.append(formatted_match)
        
        return {
            "matches": formatted_matches,
            "total": total
        }
    
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(500, f"Failed to retrieve history: {str(e)}")


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
            "message": f"Successfully cleared {deleted_count} match records"
        }
    
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        raise HTTPException(500, f"Failed to clear history: {str(e)}")


# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize components when server starts"""
    global jobs_cache
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Recruiter Pro AI API Server...")
    logger.info("=" * 60)
    
    # Load jobs
    logger.info("Loading jobs from database...")
    jobs_cache = load_jobs()
    logger.info(f"✅ Loaded {len(jobs_cache)} jobs")
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        # Database is auto-initialized when get_database() is called
        logger.info("[OK] Database ready")
    except Exception as e:
        logger.warning(f"[WARN] Database initialization failed: {e}")
    
    # Check ML model
    if pipeline.agent3.ml_predictor:
        model_info = pipeline.agent3.ml_predictor.get_model_info()
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
    if hasattr(pipeline, 'config') and pipeline.config.llm.enabled:
        logger.info(f"✅ Ollama enabled: {pipeline.config.llm.model}")
    else:
        logger.info("ℹ️  Ollama disabled (explanations will be basic)")
    
    logger.info("=" * 60)
    logger.info("✅ API Server Ready!")
    logger.info(f"📖 API Docs: http://localhost:8000/docs")
    logger.info(f"📖 ReDoc: http://localhost:8000/redoc")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when server shuts down"""
    logger.info("👋 Shutting down API Server...")
    # Add any cleanup code here if needed


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
        log_level="info"
    )
