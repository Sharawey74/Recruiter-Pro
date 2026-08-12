"""
Agent 4: LangChain-powered Explainer
Advanced LLM integration with prompt templates, streaming, and structured output
"""
from typing import Dict, Optional
import logging

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..storage.models import MatchResult, DecisionType
from ..core.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LangChainExplainerAgent:
    """
    LangChain-powered explanation generator
    
    Features:
    - Prompt templates for consistency
    - Streaming support for real-time output
    - Structured output parsing
    - Automatic retry logic
    - LangSmith tracing (optional)
    
    Advantages over direct HTTP:
    - Cleaner code with prompt templates
    - Better error handling
    - Easy provider switching (Ollama → OpenAI → Claude)
    - Built-in streaming and async support
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.llm_config = self.config.llm
        
        # Initialize LangChain Ollama
        try:
            self.llm = ChatOllama(
                model=self.llm_config.model,
                base_url=self.llm_config.base_url,
                temperature=self.llm_config.temperature,
                num_predict=self.llm_config.max_tokens,
                timeout=self.llm_config.timeout_seconds
            )
            
            # Define prompt template
            self.prompt = PromptTemplate(
                input_variables=[
                    "candidate_name", "job_title", "final_score", "decision",
                    "skill_score", "experience_score", "education_score",
                    "matched_skills", "missing_skills", "score_category"
                ],
                template=self._get_prompt_template()
            )
            
            # Build LCEL chain (LangChain Expression Language)
            self.chain = (
                RunnablePassthrough()
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
            
            self.llm_available = True
            logger.info(f"✅ LangChain Explainer initialized: {self.llm_config.model}")
            
        except Exception as e:
            self.llm_available = False
            logger.error(f"❌ LangChain initialization failed: {e}")
            logger.warning("Falling back to rule-based explanations")
    
    def _get_prompt_template(self) -> str:
        """Get the prompt template for explanations"""
        return """You are an expert HR assistant analyzing a candidate-job match. Provide a clear, professional explanation.

**Match Details:**
- Candidate: {candidate_name}
- Position: {job_title}
- Overall Score: {final_score}%
- Decision: {decision}

**Score Breakdown:**
- Skills Match: {skill_score}%
- Experience Match: {experience_score}%
- Education Match: {education_score}%

**Matched Skills:** {matched_skills}
**Missing Skills:** {missing_skills}

**Instructions:**
Based on the score category "{score_category}", provide a professional explanation that includes:

1. **Opening** (1-2 sentences): Summarize the overall match quality using varied language
2. **Strengths** (2-3 points): Highlight specific matched skills and qualifications
3. **Gaps** (1-2 points): Mention critical missing skills if any
4. **Recommendation** (1-2 sentences): Provide actionable next steps

Keep it under 150 words, professional, and fact-based. Use actual skill names provided above.
"""
    
    def _get_score_category(self, score: float) -> str:
        """Get descriptive category for score"""
        if score >= 0.90:
            return "Outstanding Match"
        elif score >= 0.80:
            return "Strong Match"
        elif score >= 0.70:
            return "Good Match"
        elif score >= 0.60:
            return "Moderate Match"
        else:
            return "Below Requirements"
    
    def generate_explanation(self, match_result: MatchResult, use_llm: bool = True) -> str:
        """
        Generate explanation using LangChain

        Falls back to rule-based if the LLM is unavailable or `use_llm` is
        False. See the note in agent4_llm_explainer on why this is a parameter.
        """
        if not self.llm_available or not use_llm:
            return self._generate_rule_based_explanation(match_result)
        
        try:
            # Prepare input data
            score = match_result.score_breakdown
            final_score = match_result.final_score
            
            input_data = {
                "candidate_name": match_result.candidate_name or "This candidate",
                "job_title": match_result.job_title,
                "final_score": int(final_score * 100),
                "decision": match_result.decision.decision.value.upper(),
                "skill_score": int(score.skill_score * 100),
                "experience_score": int(score.experience_score * 100),
                "education_score": int(score.education_score * 100),
                "matched_skills": ", ".join(score.matched_skills[:8]) if score.matched_skills else "None",
                "missing_skills": ", ".join(score.missing_skills[:5]) if score.missing_skills else "None",
                "score_category": self._get_score_category(final_score)
            }
            
            # Invoke chain
            if self.llm_config.streaming:
                # Streaming mode (for real-time UI updates)
                response = ""
                for chunk in self.chain.stream(input_data):
                    response += chunk
                return response.strip()
            else:
                # Batch mode (faster for bulk processing)
                response = self.chain.invoke(input_data)
                return response.strip()
                
        except Exception as e:
            logger.error(f"LangChain explanation failed: {e}")
            logger.warning("Falling back to rule-based explanation")
            return self._generate_rule_based_explanation(match_result)
    
    def _generate_rule_based_explanation(self, match_result: MatchResult) -> str:
        """
        Fallback rule-based explanation (same as original agent4)
        Used when LLM is unavailable
        """
        score = match_result.score_breakdown
        decision = match_result.decision
        candidate = match_result.candidate_name or "This candidate"
        score_val = match_result.final_score
        
        parts = []
        
        # Opening based on score
        if score_val >= 0.90:
            parts.append(f"{candidate} demonstrates outstanding qualifications for the {match_result.job_title} position with a {score_val:.0%} match score.")
        elif score_val >= 0.80:
            parts.append(f"{candidate} presents strong credentials for the {match_result.job_title} position with a {score_val:.0%} match score.")
        elif score_val >= 0.70:
            parts.append(f"{candidate} shows good potential for the {match_result.job_title} position with a {score_val:.0%} match score.")
        else:
            parts.append(f"{candidate} presents a moderate fit for the {match_result.job_title} position with a {score_val:.0%} match score.")
        
        # Strengths
        if score.matched_skills:
            top_skills = ', '.join(score.matched_skills[:6])
            parts.append(f"Strong capabilities in {top_skills} ({len(score.matched_skills)} matched skills).")
        
        # Gaps
        if score.missing_skills:
            missing_sample = ', '.join(score.missing_skills[:4])
            parts.append(f"Gaps in {missing_sample}.")
        
        # Recommendation
        if decision.decision == DecisionType.SHORTLIST:
            focus_skills = ', '.join(score.matched_skills[:3]) if score.matched_skills else "core competencies"
            parts.append(f"Recommend technical interview focusing on {focus_skills}.")
        elif decision.decision == DecisionType.REVIEW:
            parts.append("Recommend detailed manual review of experience and portfolio.")
        else:
            parts.append("Current profile does not meet minimum requirements.")
        
        return " ".join(parts)
    
    def generate_structured_insights(self, match_result: MatchResult) -> Dict[str, list]:
        """
        Generate structured insights (backward compatible)
        """
        score = match_result.score_breakdown
        decision = match_result.decision
        
        # Strengths
        strengths = []
        if score.skill_score >= 0.7:
            strengths.append(f"Strong skill alignment ({len(score.matched_skills)} matched)")
        if score.experience_score >= 0.8:
            strengths.append("Relevant experience level")
        if score.education_score >= 0.8:
            strengths.append("Appropriate educational background")
        
        # Weaknesses
        weaknesses = []
        if len(score.missing_skills) >= 3:
            weaknesses.append(f"Missing {len(score.missing_skills)} required skills")
        if score.underqualified:
            weaknesses.append("Insufficient skill coverage")
        if score.overqualified:
            weaknesses.append("May be overqualified")
        
        # Recommendations
        recommendations = []
        if decision.decision == DecisionType.SHORTLIST:
            recommendations.append("Proceed with technical screening")
            recommendations.append("Validate key skills in interview")
        elif decision.decision == DecisionType.REVIEW:
            recommendations.append("Conduct detailed experience review")
            recommendations.append("Consider training for missing skills")
        else:
            recommendations.append("Consider for alternative roles")
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations
        }
