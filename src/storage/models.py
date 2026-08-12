"""
Data Models for Recruiter-Pro-AI
Pydantic schemas for CV, Job, Match, and Decision entities
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DecisionType(str, Enum):
    """Match decision types"""
    SHORTLIST = "shortlist"
    REVIEW = "review"
    REJECT = "reject"


class CVProfile(BaseModel):
    """Candidate CV profile"""
    cv_id: str = Field(..., description="Unique CV identifier")
    file_name: str = Field(..., description="Original file name")
    file_path: Optional[str] = Field(None, description="File path on disk")
    
    # Extracted information
    name: Optional[str] = Field(None, description="Candidate name")
    email: Optional[str] = Field(None, description="Candidate email")
    phone: Optional[str] = Field(None, description="Candidate phone")
    location: Optional[str] = Field(None, description="Candidate location")
    
    # Skills and experience
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    experience_years: Optional[float] = Field(None, description="Years of experience")
    education: Optional[str] = Field(None, description="Education level")
    
    # Raw data
    raw_text: Optional[str] = Field(None, description="Full CV text")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Raw extraction results")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "cv_id": "cv_12345",
                "file_name": "john_doe_cv.pdf",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "skills": ["Python", "Machine Learning", "FastAPI"],
                "experience_years": 5.0,
                "education": "Bachelor's Degree"
            }
        }


class JobPosting(BaseModel):
    """Job posting/requirement - Enhanced realistic structure"""
    job_id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")

    # Business function this role belongs to - NOT its rank. An Engineering
    # Manager is category "engineering" with seniority_level "manager".
    # Optional so the archived corpus and existing test fixtures still load.
    category: Optional[str] = Field(
        None,
        description="engineering, sales, marketing, accounting, management, "
                    "administrators, maintenance, or operations"
    )
    
    # Location details
    location_city: str = Field(..., description="City where job is located")
    location_country: str = Field(default="India", description="Country")
    remote_type: str = Field(..., description="on-site, hybrid, or remote")
    
    # Job classification
    employment_type: str = Field(..., description="full-time, part-time, contract, or internship")
    seniority_level: str = Field(..., description="entry, mid, senior, lead, manager, or executive")
    
    # Experience requirements
    min_experience_years: float = Field(default=0, description="Minimum years of experience")
    max_experience_years: float = Field(default=0, description="Maximum years of experience")
    
    # Job content
    description: str = Field(..., description="Full job description")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred/nice-to-have skills")
    
    # Metadata
    posted_date: str = Field(..., description="Date job was posted (YYYY-MM-DD)")
    
    # Legacy fields for backward compatibility (will be deprecated)
    company: Optional[str] = Field(None, description="Legacy: use company_name")
    location: Optional[str] = Field(None, description="Legacy: use location_city")
    job_type: Optional[str] = Field(None, description="Legacy: use employment_type")
    education_level: Optional[str] = Field(None, description="Education level")
    salary_range: Optional[str] = Field(None, description="Salary range")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Job is currently active")
    
    @field_validator('remote_type')
    @classmethod
    def validate_remote_type(cls, v):
        allowed = ['on-site', 'hybrid', 'remote']
        if v not in allowed:
            raise ValueError(f"remote_type must be one of {allowed}")
        return v
    
    @field_validator('employment_type')
    @classmethod
    def validate_employment_type(cls, v):
        allowed = ['full-time', 'part-time', 'contract', 'internship']
        if v not in allowed:
            raise ValueError(f"employment_type must be one of {allowed}")
        return v
    
    @field_validator('seniority_level')
    @classmethod
    def validate_seniority_level(cls, v):
        allowed = ['entry', 'mid', 'senior', 'lead', 'manager', 'executive']
        if v not in allowed:
            raise ValueError(f"seniority_level must be one of {allowed}")
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        # None is allowed (archived corpus, existing fixtures). A present but
        # misspelled value is not - a silently wrong category would be
        # invisible, which is the failure mode this field exists to avoid.
        if v is None:
            return v
        allowed = ['engineering', 'sales', 'marketing', 'accounting',
                   'management', 'administrators', 'maintenance', 'operations']
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_67890",
                "title": "Senior Python Developer",
                "company_name": "Tech Solutions Pvt Ltd",
                "location_city": "Bangalore",
                "location_country": "India",
                "remote_type": "hybrid",
                "employment_type": "full-time",
                "seniority_level": "senior",
                "min_experience_years": 3.0,
                "max_experience_years": 5.0,
                "description": "We are seeking a senior-level Python developer...",
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "preferred_skills": ["Docker", "Kubernetes"],
                "posted_date": "2026-01-15"
            }
        }


class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown"""
    # Rule-based scores (0-1)
    skill_score: float = Field(0.0, ge=0.0, le=1.0)
    # Title similarity carries 17% of rule_based_score but was computed and then
    # discarded, so the reported components could not reconstruct the total.
    # Defaults to 0.0 so existing constructions stay valid.
    title_score: float = Field(0.0, ge=0.0, le=1.0)
    experience_score: float = Field(0.0, ge=0.0, le=1.0)
    education_score: float = Field(0.0, ge=0.0, le=1.0)
    keyword_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # Combined scores
    rule_based_score: float = Field(0.0, ge=0.0, le=1.0, description="Weighted rule-based score")
    ml_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="ML model prediction")
    hybrid_score: float = Field(0.0, ge=0.0, le=1.0, description="Final hybrid score")
    
    # Matching details
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    extra_skills: List[str] = Field(default_factory=list)
    
    # Flags
    overqualified: bool = Field(False)
    underqualified: bool = Field(False)
    
    @field_validator('hybrid_score')
    @classmethod
    def validate_hybrid_score(cls, v):
        """Ensure hybrid score is in valid range"""
        return max(0.0, min(1.0, v))


class MatchDecision(BaseModel):
    """Complete match decision with explanation"""
    decision: DecisionType = Field(..., description="Final decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence")
    reason: str = Field(..., description="Short decision reason")
    explanation: Optional[str] = Field(None, description="LLM-generated detailed explanation")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    red_flags: List[str] = Field(default_factory=list, description="Identified concerns")
    strengths: List[str] = Field(default_factory=list, description="Candidate strengths")


class MatchResult(BaseModel):
    """Complete CV-Job match result"""
    match_id: str = Field(..., description="Unique match identifier")
    cv_id: str = Field(..., description="CV identifier")
    job_id: str = Field(..., description="Job identifier")
    
    # Candidate and job info
    candidate_name: Optional[str] = None
    job_title: str
    
    # Scoring
    score_breakdown: ScoreBreakdown
    final_score: float = Field(..., ge=0.0, le=1.0)
    
    # Decision
    decision: MatchDecision

    # What produced the explanation: "ollama", "openrouter", "langchain" or
    # "rule_based". ADR-2 requires this be surfaced rather than hidden -- a
    # rule-based fallback after a quota failure must be distinguishable from
    # model output, both in the UI and when debugging a bad explanation.
    explanation_source: Optional[str] = Field(
        None, description="Provider that generated the explanation"
    )

    # Processing metadata
    processing_time_ms: Optional[float] = Field(None, description="Time taken to process")
    agent_versions: Dict[str, str] = Field(default_factory=dict, description="Agent versions used")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "match_abc123",
                "cv_id": "cv_12345",
                "job_id": "job_67890",
                "candidate_name": "John Doe",
                "job_title": "Senior Python Developer",
                "final_score": 0.85,
                "decision": {
                    "decision": "shortlist",
                    "confidence": 0.9,
                    "reason": "Strong skill match with relevant experience"
                }
            }
        }


class MatchHistory(BaseModel):
    """Historical match record for database storage"""
    id: Optional[int] = Field(None, description="Database ID")
    match_id: str
    cv_id: str
    job_id: str
    
    # Candidate info
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_skills: str = Field("[]", description="JSON string of skills")
    
    # Job info
    job_title: str
    required_skills: str = Field("[]", description="JSON string of required skills")
    
    # Scores
    skill_score: float
    experience_score: float
    education_score: float
    keyword_score: float
    rule_based_score: float
    ml_score: Optional[float] = None
    final_score: float
    
    # Decision
    decision: str  # shortlist, review, reject
    confidence: float
    reason: str
    explanation: Optional[str] = None
    
    # Metadata
    matched_skills: str = Field("[]", description="JSON string")
    missing_skills: str = Field("[]", description="JSON string")
    processing_time_ms: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy


class BatchMatchRequest(BaseModel):
    """Request to match a CV against multiple jobs"""
    cv_id: str
    job_ids: List[str] = Field(..., min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="Return top K matches")
    include_explanation: bool = Field(True, description="Generate LLM explanations")


class BatchMatchResponse(BaseModel):
    """Response from batch matching"""
    cv_id: str
    total_jobs_processed: int
    matches: List[MatchResult]
    processing_time_ms: float
    errors: List[str] = Field(default_factory=list)


class SystemHealth(BaseModel):
    """System health check response"""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Component health
    database_connected: bool
    llm_available: bool
    ml_model_loaded: bool
    
    # Statistics
    total_matches_processed: int = 0
    avg_processing_time_ms: Optional[float] = None
    
    # Errors
    errors: List[str] = Field(default_factory=list)


# Utility functions
def match_result_to_history(match: MatchResult) -> MatchHistory:
    """Convert MatchResult to MatchHistory for database storage"""
    import json
    
    return MatchHistory(
        match_id=match.match_id,
        cv_id=match.cv_id,
        job_id=match.job_id,
        candidate_name=match.candidate_name,
        job_title=match.job_title,
        candidate_skills=json.dumps(match.score_breakdown.matched_skills + 
                                   match.score_breakdown.extra_skills),
        required_skills=json.dumps(match.score_breakdown.matched_skills + 
                                  match.score_breakdown.missing_skills),
        skill_score=match.score_breakdown.skill_score,
        experience_score=match.score_breakdown.experience_score,
        education_score=match.score_breakdown.education_score,
        keyword_score=match.score_breakdown.keyword_score,
        rule_based_score=match.score_breakdown.rule_based_score,
        ml_score=match.score_breakdown.ml_score,
        final_score=match.final_score,
        decision=match.decision.decision.value,
        confidence=match.decision.confidence,
        reason=match.decision.reason,
        explanation=match.decision.explanation,
        matched_skills=json.dumps(match.score_breakdown.matched_skills),
        missing_skills=json.dumps(match.score_breakdown.missing_skills),
        processing_time_ms=match.processing_time_ms,
        created_at=match.created_at
    )
