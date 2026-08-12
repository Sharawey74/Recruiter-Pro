"""
Agent 3: Hybrid Scoring Agent
Combines rule-based scoring with ML predictions for robust matching

Architecture:
- Rule-based scoring: Skill matching, experience, education (60% weight)
- ML scoring: ATS engine predictions (40% weight)
- Hybrid score: Weighted combination of both approaches
"""
import logging
from typing import Dict, Optional

from ..storage.models import ScoreBreakdown, CVProfile, JobPosting
from ..core.config import get_config
from ..core.vocabulary import load_alias_index
from ..ml_engine.ats_predictor import ATSPredictor
from .scoring import components
from .scoring.skill_matcher import SkillMatch, SkillMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Re-exported: SkillMatch was defined here before the split.
__all__ = ["HybridScoringAgent", "SkillMatch"]


class HybridScoringAgent:
    """
    Agent 3: Hybrid Scorer
    
    Combines rule-based and ML approaches for robust scoring:
    1. Rule-based: Skills (60%), Experience (25%), Education (10%), Keywords (5%)
    2. ML-based: ATS Engine prediction (optional)
    3. Hybrid: Weighted combination based on configuration
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.scoring_config = self.config.scoring
        
        # Initialize ML predictor if enabled
        self.ml_predictor = None
        if self.scoring_config.ml_enabled:
            try:
                self.ml_predictor = ATSPredictor(model_dir="models/production")
                if self.ml_predictor.load_model():
                    logger.info("[OK] ML Predictor initialized for hybrid scoring")
                    model_info = self.ml_predictor.get_model_info()
                    logger.info(f"   Model: {model_info.get('model_name', 'Unknown')}")
                    logger.info(f"   Test Recall: {model_info.get('test_metrics', {}).get('recall', 'N/A')}")
                else:
                    logger.warning("[WARN] Failed to load ML model. Using rule-based only.")
                    self.ml_predictor = None
            except Exception as e:
                logger.warning(f"[WARN] ML Predictor unavailable: {e}. Using rule-based only.")
                self.ml_predictor = None
        
        # The vocabulary is read once, here, and handed to the matcher that
        # owns it. Nothing else in this class needs it.
        self.skill_matcher = SkillMatcher(
            load_alias_index(self.config.skills_database_path)
        )

    def score_match(
        self, 
        cv: CVProfile, 
        job: JobPosting,
        include_ml: bool = True
    ) -> ScoreBreakdown:
        """
        Score CV-Job match using hybrid approach
        
        Args:
            cv: Candidate CV profile
            job: Job posting requirements
            include_ml: Whether to include ML scoring
        
        Returns:
            ScoreBreakdown with all scoring components
        """
        # 1. Rule-based scoring
        skill_match = self.skill_matcher.match(
            cv.skills, job.required_skills, job.preferred_skills
        )
        experience_score = components.score_experience(cv, job)
        education_score = components.score_education(cv, job)
        keyword_score = components.score_keywords(cv, job)
        title_score = components.score_title_similarity(cv, job)
        
        # Weighted rule-based score. The weights live in config/agents.yaml and
        # nowhere else -- they used to be hardcoded here while config declared a
        # different set that nothing read, so retuning the YAML did nothing.
        weights = self.scoring_config
        rule_based_score = (
            skill_match.match_ratio * weights.skill_weight +
            title_score * weights.title_weight +
            experience_score * weights.experience_weight +
            education_score * weights.education_weight +
            keyword_score * weights.keyword_weight
        )
        
        # 2. ML-based scoring (if enabled)
        ml_score = None
        ml_probability = None
        if include_ml and self.ml_predictor:
            ml_result = self._get_ml_score(cv, job)
            if ml_result:
                # Convert ml_score from 0-100 to 0-1 scale
                ml_score = ml_result['ml_score'] / 100.0 if ml_result['ml_score'] > 1 else ml_result['ml_score']
                ml_probability = ml_result['probability']
        
        # 3. Calculate hybrid score
        if ml_score is not None:
            hybrid_score = (
                rule_based_score * self.scoring_config.rule_weight +
                ml_score * self.scoring_config.ml_weight
            )
        else:
            hybrid_score = rule_based_score
        
        # 4. Detect over/under qualification
        overqualified = components.is_overqualified(cv, job, experience_score)
        underqualified = components.is_underqualified(cv, job, skill_match.match_ratio)
        
        # 5. Build score breakdown
        return ScoreBreakdown(
            skill_score=skill_match.match_ratio,
            title_score=title_score,
            experience_score=experience_score,
            education_score=education_score,
            keyword_score=keyword_score,
            rule_based_score=rule_based_score,
            ml_score=ml_score,
            hybrid_score=hybrid_score,
            matched_skills=skill_match.matched_skills,
            missing_skills=skill_match.missing_skills,
            extra_skills=skill_match.extra_skills,
            overqualified=overqualified,
            underqualified=underqualified
        )
    
    def _get_ml_score(self, cv: CVProfile, job: JobPosting) -> Optional[Dict]:
        """Get ML model prediction score"""
        if not self.ml_predictor:
            return None
        
        try:
            # Prepare CV data for ML predictor
            cv_data = {
                'Skills': ', '.join(cv.skills),
                'Experience': cv.experience_years or 0,
                'Education': cv.education or 'Bachelor',
                'Certifications': cv.extracted_data.get('certifications', 'None'),
                'Job Role': job.title,
                'Projects Count': cv.extracted_data.get('projects_count', 0),
                'Salary': cv.extracted_data.get('expected_salary', 50000)
            }
            
            # Get prediction from ML predictor
            result = self.ml_predictor.predict(cv_data, use_optimal_threshold=True)
            
            return result
            
        except Exception as e:
            logger.error(f"ML scoring failed: {e}")
            return None
    