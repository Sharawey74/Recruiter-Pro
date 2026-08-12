"""
Agent 4: LLM Explanation Agent (Modernized)
Generates human-readable explanations using local Ollama LLM

Integrated with new storage models and configuration system
"""
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

from ..storage.models import MatchResult, ScoreBreakdown, MatchDecision, DecisionType
from ..core.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import LLM dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available. Agent 4 will use mock mode.")


class LLMExplainerAgent:
    """
    Agent 4: LLM-powered explanation generator
    
    Responsibilities:
    - Generate human-readable explanations from scoring data
    - Provide actionable insights for HR teams
    - Suggest interview focus areas
    
    Uses local Ollama for privacy and cost control
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.llm_config = self.config.llm
        
        # Check if LLM is available
        self.llm_available = self._check_llm_availability()
        
        if not self.llm_available:
            logger.warning("[WARN] LLM not available. Using rule-based explanations.")
    
    def _check_llm_availability(self) -> bool:
        """Check if Ollama LLM is available"""
        if not self.llm_config.enabled or not REQUESTS_AVAILABLE:
            return False
        
        try:
            # Ping Ollama
            response = requests.get(
                f"{self.llm_config.base_url}/api/tags",
                timeout=2
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if self.llm_config.model in model_names:
                    logger.info(f"[OK] LLM available: {self.llm_config.model}")
                    return True
                else:
                    logger.warning(f"Model {self.llm_config.model} not found. Available: {model_names}")
                    return False
        except Exception as e:
            logger.warning(f"LLM unavailable: {e}")
            return False
    
    def generate_explanation(self, match_result: MatchResult, use_llm: bool = True) -> str:
        """
        Generate detailed explanation for a match result

        Args:
            match_result: Complete match result with scores and decision
            use_llm: Per-call override. The API used to express "no LLM for this
                request" by assigning False to self.llm_available on the shared
                pipeline singleton and restoring it afterwards, which leaked
                across concurrent requests and stuck permanently if the request
                raised in between. It is an argument now.

        Returns:
            Human-readable explanation text
        """
        if self.llm_available and use_llm:
            try:
                return self._generate_llm_explanation(match_result)
            except Exception as e:
                logger.error(f"LLM explanation failed: {e}")
                return self._generate_rule_based_explanation(match_result)
        else:
            return self._generate_rule_based_explanation(match_result)
    
    def _generate_llm_explanation(self, match_result: MatchResult) -> str:
        """Generate explanation using LLM"""
        # Build prompt
        prompt = self._build_prompt(match_result)
        
        # Call Ollama API
        response = requests.post(
            f"{self.llm_config.base_url}/api/generate",
            json={
                "model": self.llm_config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.llm_config.temperature,
                    "num_predict": self.llm_config.max_tokens
                }
            },
            timeout=self.llm_config.timeout_seconds
        )
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get('response', '').strip()
            
            # Validate and clean
            if len(explanation) > 50:
                return explanation
        
        # Fallback if response invalid
        return self._generate_rule_based_explanation(match_result)
    
    def _build_prompt(self, match_result: MatchResult) -> str:
        """Build LLM prompt from match result"""
        score = match_result.score_breakdown
        decision = match_result.decision
        
        prompt = f"""You are an HR assistant analyzing a candidate-job match. Provide a clear, professional explanation.

**Match Details:**
- Candidate: {match_result.candidate_name or 'Candidate'}
- Position: {match_result.job_title}
- Final Score: {match_result.final_score:.0%}
- Decision: {decision.decision.value.upper()}
- Confidence: {decision.confidence:.0%}

**Score Breakdown:**
- Skill Match: {score.skill_score:.0%} ({len(score.matched_skills)} matched, {len(score.missing_skills)} missing)
- Experience: {score.experience_score:.0%}
- Education: {score.education_score:.0%}
- Keywords: {score.keyword_score:.0%}

**Matched Skills:** {', '.join(score.matched_skills[:5]) if score.matched_skills else 'None'}
**Missing Skills:** {', '.join(score.missing_skills[:5]) if score.missing_skills else 'None'}

**Flags:**
{f"[!] Overqualified: True" if score.overqualified else ""}
{f"[!] Underqualified: True" if score.underqualified else ""}

**Instructions:**
Write a concise 2-3 paragraph explanation that:
1. Summarizes why this decision was made
2. Highlights 2-3 key strengths based on matched skills and scores
3. Notes 1-2 concerns based on missing skills or gaps
4. Provides 1-2 actionable recommendations for HR

Keep it professional, factual, and under 200 words. Do NOT invent facts not in the data above."""
        
        return prompt
    
    def _generate_rule_based_explanation(self, match_result: MatchResult) -> str:
        """Generate detailed, varied rule-based explanation with actual skill names"""
        score = match_result.score_breakdown
        decision = match_result.decision
        candidate = match_result.candidate_name or "This candidate"
        score_val = match_result.final_score
        
        parts = []
        
        # 1. Score-based opening with variety (avoid repetition)
        if score_val >= 0.90:
            openings = [
                f"{candidate} demonstrates outstanding qualifications for the {match_result.job_title} position with a {score_val:.0%} match score.",
                f"Exceptional match: {candidate} achieves a {score_val:.0%} alignment score for the {match_result.job_title} role.",
                f"{candidate} presents an excellent profile scoring {score_val:.0%} for this {match_result.job_title} opportunity."
            ]
            parts.append(openings[hash(candidate) % 3])
        elif score_val >= 0.80:
            openings = [
                f"{candidate} presents strong credentials for the {match_result.job_title} position with a {score_val:.0%} match score.",
                f"Strong candidate: {candidate} scores {score_val:.0%} for the {match_result.job_title} role.",
                f"{candidate} demonstrates solid qualifications with a {score_val:.0%} match for this {match_result.job_title} position."
            ]
            parts.append(openings[hash(candidate) % 3])
        elif score_val >= 0.70:
            openings = [
                f"{candidate} shows good potential for the {match_result.job_title} position with a {score_val:.0%} match score.",
                f"Promising candidate: {candidate} achieves a {score_val:.0%} alignment for the {match_result.job_title} role.",
                f"{candidate} presents a viable profile scoring {score_val:.0%} for this {match_result.job_title} opportunity."
            ]
            parts.append(openings[hash(candidate) % 3])
        elif score_val >= 0.60:
            openings = [
                f"{candidate} presents a moderate fit for the {match_result.job_title} position with a {score_val:.0%} match score.",
                f"Borderline candidate: {candidate} scores {score_val:.0%} for the {match_result.job_title} role.",
                f"{candidate} shows potential but has gaps, scoring {score_val:.0%} for this {match_result.job_title} position."
            ]
            parts.append(openings[hash(candidate) % 3])
        else:
            openings = [
                f"{candidate} falls below requirements for the {match_result.job_title} position with a {score_val:.0%} match score.",
                f"Limited alignment: {candidate} achieves only a {score_val:.0%} match for the {match_result.job_title} role.",
                f"{candidate} shows significant gaps with a {score_val:.0%} score for this {match_result.job_title} opportunity."
            ]
            parts.append(openings[hash(candidate) % 3])
        
        # 2. Detailed Strengths with actual skill names
        strength_details = []
        
        # Skills - Show actual matched skills (KEY IMPROVEMENT)
        if score.matched_skills:
            skill_count = len(score.matched_skills)
            top_skills = ', '.join(score.matched_skills[:6])  # Show top 6 skills
            
            if score.skill_score >= 0.85:
                strength_details.append(f"Excellent technical proficiency demonstrated in {top_skills} ({skill_count} matched skills).")
            elif score.skill_score >= 0.70:
                strength_details.append(f"Strong capabilities in {top_skills} with {skill_count} matched skills.")
            else:
                strength_details.append(f"Proficient in {top_skills}, covering {skill_count} required areas.")
        
        # Experience
        if score.experience_score >= 0.85:
            strength_details.append("Experience level aligns perfectly with role requirements.")
        elif score.experience_score >= 0.70:
            strength_details.append("Relevant experience level for this position.")
        
        # Education
        if score.education_score >= 0.90:
            strength_details.append("Educational background exceeds role requirements.")
        elif score.education_score >= 0.75:
            strength_details.append("Appropriate educational qualifications.")
        
        # Additional strengths
        if score.keyword_score >= 0.80:
            strength_details.append("Resume demonstrates relevant domain expertise and terminology.")
        
        if strength_details:
            parts.append(" ".join(strength_details))
        
        # 3. Concerns and Gaps with specific skill names
        concern_details = []
        
        # Missing skills - Show actual missing skills (KEY IMPROVEMENT)
        if score.missing_skills:
            missing_count = len(score.missing_skills)
            missing_sample = ', '.join(score.missing_skills[:5])  # Show up to 5 missing skills
            
            if missing_count >= 5:
                concern_details.append(f"Notable gaps in {missing_sample} and {missing_count - 5} other areas.")
            elif missing_count >= 3:
                concern_details.append(f"Missing key competencies: {missing_sample}.")
            else:
                concern_details.append(f"Minor gaps in {missing_sample}.")
        
        # Experience concerns
        if score.experience_score < 0.50:
            concern_details.append("Experience level may be insufficient for role demands.")
        
        # Qualification flags
        if score.underqualified:
            concern_details.append("Overall skill coverage falls short of requirements.")
        if score.overqualified:
            concern_details.append("Candidate may be overqualified, consider retention risk.")
        
        if concern_details:
            parts.append(" ".join(concern_details))
        
        # 4. Decision-specific recommendations with actionable details
        if decision.decision == DecisionType.SHORTLIST:
            rec_parts = []
            
            # Interview focus areas (show actual skills)
            if score.matched_skills:
                focus_skills = ', '.join(score.matched_skills[:3])
                rec_parts.append(f"Proceed with technical interview focusing on {focus_skills}.")
            else:
                rec_parts.append("Proceed with technical screening to validate qualifications.")
            
            # Cultural fit
            if score_val >= 0.85:
                rec_parts.append("Assess cultural fit and discuss role expectations.")
            else:
                rec_parts.append("Verify proficiency in matched skills and assess learning agility for gaps.")
            
            parts.append(" ".join(rec_parts))
            
        elif decision.decision == DecisionType.REVIEW:
            rec_parts = []
            rec_parts.append("Recommend detailed manual review of experience and portfolio.")
            
            # Training considerations (show actual missing skills)
            if score.missing_skills:
                training_skills = ', '.join(score.missing_skills[:3])
                rec_parts.append(f"Evaluate training potential for {training_skills}.")
            
            # Alternative fit
            if score.skill_score < 0.65:
                rec_parts.append("Consider alternative roles better matching candidate's skill profile.")
            
            parts.append(" ".join(rec_parts))
            
        else:  # REJECT
            rec_parts = []
            
            if score_val < 0.50:
                rec_parts.append("Candidate does not meet minimum requirements for this position.")
            else:
                rec_parts.append("Current profile does not align with role needs.")
            
            # Constructive guidance
            if score.missing_skills:
                critical_gaps = ', '.join(score.missing_skills[:3])
                rec_parts.append(f"Suggest developing competencies in {critical_gaps} for future consideration.")
            else:
                rec_parts.append("Consider for alternative roles or revisit if requirements evolve.")
            
            parts.append(" ".join(rec_parts))
        
        return " ".join(parts)
    
    def generate_structured_insights(self, match_result: MatchResult) -> Dict[str, List[str]]:
        """
        Generate structured insights (strengths, weaknesses, recommendations)
        
        Returns:
            {
                'strengths': [...],
                'weaknesses': [...],
                'recommendations': [...]
            }
        """
        score = match_result.score_breakdown
        decision = match_result.decision
        
        insights = {
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Strengths
        if score.matched_skills:
            insights['strengths'].append(
                f"Proficient in {len(score.matched_skills)} key skills: {', '.join(score.matched_skills[:4])}"
            )
        
        if score.experience_score >= 0.8:
            insights['strengths'].append("Experience level aligns well with job requirements")
        
        if score.education_score >= 0.9:
            insights['strengths'].append("Educational qualifications meet or exceed requirements")
        
        if score.ml_score and score.ml_score >= 0.75:
            insights['strengths'].append(f"Strong ATS compatibility score ({score.ml_score:.0%})")
        
        # Weaknesses
        if score.missing_skills:
            insights['weaknesses'].append(
                f"Lacks {len(score.missing_skills)} required skills: {', '.join(score.missing_skills[:4])}"
            )
        
        if score.experience_score < 0.5:
            insights['weaknesses'].append("Experience level below job requirements")
        
        if score.underqualified:
            insights['weaknesses'].append("Insufficient overall skill coverage for this role")
        
        if score.overqualified:
            insights['weaknesses'].append("May be overqualified; risk of low retention")
        
        # Recommendations
        if decision.decision == DecisionType.SHORTLIST:
            insights['recommendations'].extend([
                "Schedule technical interview to validate key skills",
                "Assess cultural fit and team dynamics",
                "Verify depth of experience in matched skills"
            ])
        elif decision.decision == DecisionType.REVIEW:
            insights['recommendations'].extend([
                "Deep-dive review of work history and projects",
                f"Assess learning potential for missing skills: {', '.join(score.missing_skills[:3])}",
                "Consider alternative roles that better match skill set"
            ])
        else:
            insights['recommendations'].extend([
                "Keep profile for future positions with different requirements",
                "Consider for junior roles if experience is the main gap"
            ])
        
        return insights


# Singleton instance
_agent4_instance: Optional[LLMExplainerAgent] = None


def get_explainer_agent(reload: bool = False) -> LLMExplainerAgent:
    """Get Agent 4 singleton instance"""
    global _agent4_instance
    
    if _agent4_instance is None or reload:
        _agent4_instance = LLMExplainerAgent()
    
    return _agent4_instance
