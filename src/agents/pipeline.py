"""
Agent Orchestrator - 4-Agent Pipeline Coordinator
Manages the complete CV-Job matching workflow

Pipeline Flow:
1. Agent 1 (Parser) → Extract text from CV files
2. Agent 2 (Extractor) → Parse structured data from text
3. Agent 3 (Scorer) → Calculate hybrid scores (rules + ML)
4. Agent 4 (Explainer) → Generate LLM explanations

Design: Layered pipeline with error handling and logging
"""
import time
import uuid
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from ..storage.models import (
    CVProfile, JobPosting, MatchResult, MatchDecision,
    DecisionType, ScoreBreakdown
)
from ..storage.database import get_database
from ..core.config import get_config

from .agent1_parser import RawParser
from .agent2_extractor import CandidateExtractor
from .agent3_scorer import HybridScoringAgent
from .agent4_factory import get_explainer_agent
from .explaining import ExplanationContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchingPipeline:
    """
    4-Agent Pipeline for CV-Job Matching
    
    Orchestrates the complete workflow from CV file to match decision
    """
    
    def __init__(self, config=None, save_to_db: bool = True):
        """
        Initialize pipeline with all agents
        
        Args:
            config: Application configuration
            save_to_db: Whether to auto-save results to database
        """
        self.config = config or get_config()
        self.save_to_db = save_to_db
        self.db = get_database() if save_to_db else None
        
        # Initialize agents
        logger.info("🚀 Initializing 4-Agent Pipeline...")
        
        self.agent1 = RawParser()
        logger.info("✅ Agent 1 (Parser) ready")
        
        self.agent2 = CandidateExtractor()
        logger.info("✅ Agent 2 (Extractor) ready")
        
        self.agent3 = HybridScoringAgent(config=self.config)
        logger.info("✅ Agent 3 (Scorer) ready")
        
        self.agent4 = get_explainer_agent(config=self.config)
        langchain_mode = getattr(self.config.llm, 'use_langchain', False)
        logger.info(f"✅ Agent 4 (Explainer) ready - LangChain: {langchain_mode}")
        
        logger.info("🎉 Pipeline initialization complete!")
    
    def process_cv_for_job(
        self,
        cv_file_path: str,
        job: JobPosting,
        generate_explanation: bool = True
    ) -> MatchResult:
        """
        Process a single CV against a job posting
        
        Args:
            cv_file_path: Path to CV file (PDF/DOCX/TXT)
            job: Job posting to match against
            generate_explanation: Whether to generate LLM explanation
        
        Returns:
            MatchResult with complete scoring and decision
        """
        start_time = time.time()
        
        try:
            # Step 1: Parse CV file
            logger.info(f"📄 Step 1: Parsing {Path(cv_file_path).name}...")
            result = self.agent1.parse_file(cv_file_path)
            cv_text = result.get('raw_text', '')
            
            if not cv_text or len(cv_text) < 50:
                raise ValueError("CV parsing failed or file too short")
            
            # Step 2: Extract structured data
            logger.info("🔍 Step 2: Extracting structured data...")
            extracted_data = self.agent2.extract(cv_text)
            
            # Normalize extracted data
            education = extracted_data.get('education', '')
            if isinstance(education, list):
                education = ', '.join(education) if education else None
            
            # Build CV profile
            cv = CVProfile(
                cv_id=str(uuid.uuid4()),
                file_name=Path(cv_file_path).name,
                file_path=cv_file_path,
                name=extracted_data.get('name'),
                email=extracted_data.get('email'),
                phone=extracted_data.get('phone'),
                skills=extracted_data.get('skills', []),
                experience_years=extracted_data.get('experience_years'),
                education=education,
                raw_text=cv_text,
                extracted_data=extracted_data
            )
            
            # Step 3: Score match
            logger.info("🎯 Step 3: Calculating hybrid score...")
            score_breakdown = self.agent3.score_match(cv, job)
            
            # Make decision
            decision = self._make_decision(score_breakdown)
            
            # Step 4: Generate explanation (optional)
            explanation = None
            if generate_explanation and self.config.llm.enabled:
                logger.info("💬 Step 4: Generating LLM explanation...")
                
                # Build match result (without explanation first)
                match_result = self._build_match_result(
                    cv, job, score_breakdown, decision, None, start_time
                )
                
                explanation = self.agent4.generate_explanation(match_result)
                
                # Update decision with explanation
                decision = MatchDecision(
                    decision=decision.decision,
                    confidence=decision.confidence,
                    reason=decision.reason,
                    explanation=explanation,
                    recommendations=decision.recommendations,
                    red_flags=decision.red_flags,
                    strengths=decision.strengths
                )
            
            # Build final result
            match_result = self._build_match_result(
                cv, job, score_breakdown, decision, explanation, start_time
            )
            
            # Save to database
            if self.save_to_db and self.db:
                self.db.save_match(match_result)
                logger.info(f"💾 Saved to database: {match_result.match_id}")
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"[OK] Pipeline complete in {processing_time:.0f}ms - Decision: {decision.decision.value.upper()}")
            
            return match_result
            
        except Exception as e:
            logger.error(f"[ERROR] Pipeline failed: {e}")
            raise
    
    # Explanations are LLM calls. On a public URL the number of them per upload
    # has to be bounded by something other than the corpus size.
    MAX_EXPLANATIONS = 3

    def explainer_for(self, use_langchain: bool = False):
        """
        Return the explainer for this request without reconfiguring the shared one.

        The API used to assign a new agent onto pipeline.agent4 for the duration
        of a request and put the old one back afterwards. Two requests with
        different modes raced, and the restore was not in a finally block, so a
        request that raised left the singleton swapped for every later request.

        The LangChain explainer is built once, on first use, and cached. Worst
        case under concurrency is that two get constructed and one is discarded;
        neither request sees the other's mode.
        """
        if not use_langchain:
            return self.agent4

        if getattr(self, '_agent4_langchain', None) is None:
            from src.agents.agent4_factory import get_explainer_agent
            self._agent4_langchain = get_explainer_agent(
                use_langchain=True, config=self.config
            )
            logger.info("LangChain explainer created (cached for later requests)")
        return self._agent4_langchain

    def process_cv_batch(
        self,
        cv_file_path: str,
        jobs: List[JobPosting],
        top_k: int = 10,
        generate_explanations: bool = True,
        use_llm: bool = True,
        use_langchain: bool = False
    ) -> List[MatchResult]:
        """
        Process one CV against multiple jobs
        
        Args:
            cv_file_path: Path to CV file
            jobs: List of job postings
            top_k: Return only top K matches
            generate_explanations: Whether to generate LLM explanations
        
        Returns:
            List of MatchResults, sorted by score (descending)
        """
        logger.info(f"📦 Batch processing: 1 CV vs {len(jobs)} jobs")
        
        # Parse CV once
        result = self.agent1.parse_file(cv_file_path)
        cv_text = result.get('raw_text', '')
        extracted_data = self.agent2.extract(cv_text)
        
        # Normalize extracted data
        education = extracted_data.get('education', '')
        if isinstance(education, list):
            education = ', '.join(education) if education else None
        
        cv = CVProfile(
            cv_id=str(uuid.uuid4()),
            file_name=Path(cv_file_path).name,
            file_path=cv_file_path,
            name=extracted_data.get('name'),
            email=extracted_data.get('email'),
            skills=extracted_data.get('skills', []),
            experience_years=extracted_data.get('experience_years'),
            education=education,
            raw_text=cv_text,
            extracted_data=extracted_data
        )
        
        # Score against all jobs.
        #
        # One call for the whole corpus, not one per job: the model used to be
        # invoked once per job, each time rebuilding a 1-row DataFrame and
        # re-running the fitted transform. That was 8.13 s of an 8.0 s upload
        # against 800 jobs; batched it is 0.033 s. Rule-based scoring is still
        # per job -- it is 0.30 s for the whole corpus and not worth touching.
        breakdowns = self.agent3.score_matches(cv, jobs)

        matches = []
        for job, score_breakdown in zip(jobs, breakdowns):
            start_time = time.time()
            decision = self._make_decision(score_breakdown)
            matches.append(
                self._build_match_result(cv, job, score_breakdown, decision, None, start_time)
            )

        # Sort by score and return top K
        matches.sort(key=lambda m: m.final_score, reverse=True)
        top_matches = matches[:top_k]

        # Explain only after ranking, and only a bounded number.
        #
        # Explanations used to be generated inside the scoring loop for every
        # job scoring >= 0.6 -- one LLM call each, with nothing bounding the
        # count but the size of the corpus. On a public URL that is an
        # unmetered outbound bill triggered by a single upload, and most of
        # those calls were for jobs that never made the returned top-K anyway.
        #
        # Now: rank first, then explain at most MAX_EXPLANATIONS of what is
        # actually being returned.
        if generate_explanations:
            explainer = self.explainer_for(use_langchain)
            eligible = [
                m for m in top_matches[:self.MAX_EXPLANATIONS]
                if m.final_score >= 0.6
            ]
            if eligible:
                # One batched call. The provider owns the fallback chain, so
                # this cannot raise and every match gets an explanation --
                # tagged with what produced it, so a rule-based fallback is
                # visible rather than passed off as model output.
                explanations = explainer.explain(
                    [ExplanationContext.from_match_result(m) for m in eligible],
                    use_llm=use_llm,
                )
                for match, explanation in zip(eligible, explanations):
                    match.decision.explanation = explanation.text
                    match.explanation_source = explanation.source

        # Persist once, after the loop, and only what is returned.
        #
        # This used to be a save_match call inside the loop, and save_match
        # opens a fresh connection, commits and closes per row -- 4.31 ms each,
        # so 3.45 s on an 800-job upload, 43% of the request. It also wrote all
        # 800 rows while returning 10, so 99% of /history was noise nobody
        # asked for and nobody read.
        if self.save_to_db and self.db and top_matches:
            saved = self.db.save_matches_batch(top_matches)
            logger.info(f"💾 Saved {saved} matches to database")

        logger.info(f"[OK] Batch complete: Top {len(top_matches)} matches returned")
        return top_matches
    
    def _make_decision(self, score: ScoreBreakdown) -> MatchDecision:
        """
        Make hiring decision based on score
        
        Uses thresholds from configuration
        """
        final_score = score.hybrid_score
        
        # Get thresholds
        shortlist_threshold = self.config.scoring.shortlist_threshold
        review_threshold = self.config.scoring.review_threshold
        
        # Determine decision
        if final_score >= shortlist_threshold:
            decision_type = DecisionType.SHORTLIST
            confidence = min(0.95, 0.75 + (final_score - shortlist_threshold) * 0.8)
            reason = "Strong overall match with excellent skill alignment"
        elif final_score >= review_threshold:
            decision_type = DecisionType.REVIEW
            confidence = 0.6 + (final_score - review_threshold) * 0.4
            reason = "Moderate match requiring manual review"
        else:
            decision_type = DecisionType.REJECT
            confidence = 0.8
            reason = "Insufficient match for this position"
        
        # Adjust for flags
        if score.overqualified:
            reason += " (note: candidate may be overqualified)"
            confidence = max(0.5, confidence - 0.15)
        
        if score.underqualified:
            if decision_type != DecisionType.REJECT:
                decision_type = DecisionType.REVIEW
                reason = "Underqualified but may have potential"
        
        # Build insights
        strengths = []
        red_flags = []
        recommendations = []
        
        if score.skill_score >= 0.7:
            strengths.append(f"Strong skill match ({len(score.matched_skills)} key skills)")
        if score.experience_score >= 0.8:
            strengths.append("Experience level aligns well")
        
        if len(score.missing_skills) > 3:
            red_flags.append(f"Missing {len(score.missing_skills)} required skills")
        if score.underqualified:
            red_flags.append("Below minimum skill requirements")
        
        if decision_type == DecisionType.SHORTLIST:
            recommendations.append("Proceed with technical interview")
            recommendations.append("Assess cultural fit")
        else:
            recommendations.append("Review work history in detail")
            recommendations.append("Consider for alternative roles")
        
        return MatchDecision(
            decision=decision_type,
            confidence=confidence,
            reason=reason,
            strengths=strengths,
            red_flags=red_flags,
            recommendations=recommendations
        )
    
    def _build_match_result(
        self,
        cv: CVProfile,
        job: JobPosting,
        score: ScoreBreakdown,
        decision: MatchDecision,
        explanation: Optional[str],
        start_time: float
    ) -> MatchResult:
        """Build MatchResult from components"""
        processing_time = (time.time() - start_time) * 1000
        
        return MatchResult(
            match_id=f"match_{uuid.uuid4().hex[:12]}",
            cv_id=cv.cv_id,
            job_id=job.job_id,
            candidate_name=cv.name,
            job_title=job.title,
            score_breakdown=score,
            final_score=score.hybrid_score,
            decision=decision,
            processing_time_ms=processing_time,
            agent_versions={
                "agent1": "1.0",
                "agent2": "1.0",
                "agent3": "2.0-hybrid",
                "agent4": "2.0-llm"
            }
        )


# Singleton instance
_pipeline_instance: Optional[MatchingPipeline] = None


def get_pipeline(reload: bool = False, save_to_db: bool = True) -> MatchingPipeline:
    """Get pipeline singleton"""
    global _pipeline_instance
    
    if _pipeline_instance is None or reload:
        _pipeline_instance = MatchingPipeline(save_to_db=save_to_db)
    
    return _pipeline_instance
