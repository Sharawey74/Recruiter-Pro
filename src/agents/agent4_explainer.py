"""
Agent 4: Interpretation & Explanation Agent
LLM-powered interpreter using Ollama + LangChain + AutoGen
Generates human-readable explanations from Agent 3 and ATS outputs
"""
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

# LangChain imports
try:
    from langchain_community.llms import Ollama
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    LANGCHAIN_AVAILABLE = True
    
    # Suppress langchain warnings
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Agent 4 will use mock mode.")

# AutoGen imports
try:
    from autogen import ConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logging.warning("AutoGen not available. Using single-pass mode.")


class ExplanationAgent:
    """
    Agent 4: LLM-powered explanation generator
    
    Responsibilities:
    - Interpret Agent 3 (rule-based) and ATS Engine outputs
    - Generate structured, human-readable explanations
    - Provide actionable insights for HR
    
    Constraints:
    - Read-only (no scoring, no decision-making)
    - Local-only (Ollama)
    - Deterministic (low temperature)
    """
    
    def __init__(self, use_autogen: bool = True):
        # Initialize standard logging
        self.logger = logging.getLogger("Agent4_Explainer")
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        
        self.use_autogen = use_autogen and AUTOGEN_AVAILABLE
        self.use_mock = not LANGCHAIN_AVAILABLE
        
        if not self.use_mock:
            # Initialize Ollama LLM
            self.llm = Ollama(
                model="llama3.2:3b",
                temperature=0.2,
                base_url="http://localhost:11500"
            )
            
            # Define strict prompt template
            self.prompt_template = PromptTemplate(
                input_variables=[
                    "candidate_name", "job_title", "rule_score", "decision",
                    "matched_skills", "missing_skills", "experience_years",
                    "required_experience", "ats_score"
                ],
                template="""You are an HR assistant analyzing a candidate-job match. Your task is to interpret the scores and provide a professional explanation.

**INPUT DATA:**
- Candidate: {candidate_name}
- Job: {job_title}
- Rule-Based Score: {rule_score}%
- Decision: {decision}
- Matched Skills: {matched_skills}
- Missing Skills: {missing_skills}
- Candidate Experience: {experience_years} years
- Required Experience: {required_experience} years
- ATS Score: {ats_score}%

**INSTRUCTIONS:**
1. Generate a neutral, professional HR summary (2-3 sentences)
2. List 2-4 key strengths based ONLY on matched skills and scores
3. List 1-3 weaknesses based ONLY on missing skills
4. Provide 2-3 actionable recommendations for HR
5. Suggest 2-3 interview focus areas

**CRITICAL RULES:**
- Do NOT invent new facts
- Do NOT recalculate scores
- Do NOT change the decision
- Base ALL statements on the provided data
- Use professional, neutral language

**OUTPUT FORMAT (JSON):**
{{
  "hr_summary": "Brief interpretation of the match",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1"],
  "recommendations": ["action 1", "action 2"],
  "interview_focus": ["topic 1", "topic 2"]
}}

Return ONLY valid JSON, no additional text."""
            )
            
            # Initialize AutoGen agents if enabled
            if self.use_autogen:
                self._init_autogen()
        
        self.logger.info(f"Agent 4 initialized (AutoGen: {self.use_autogen}, Mock: {self.use_mock})")
    
    def _init_autogen(self):
        """Initialize AutoGen agents for explanation generation and review"""
        llm_config = {
            "config_list": [{
                "model": "llama3.2:3b",
                "base_url": "http://localhost:11500/v1",
                "api_key": "ollama",  # Dummy key for Ollama
                "temperature": 0.2
            }]
        }
        
        # Explainer Agent: Generates initial explanation
        self.explainer_agent = ConversableAgent(
            name="ExplainerAgent",
            system_message="""You are an HR explanation specialist. Generate structured JSON explanations 
            from candidate-job match data. Be factual, professional, and concise.""",
            llm_config=llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1
        )
        
        # Reviewer Agent: Validates clarity and alignment
        self.reviewer_agent = ConversableAgent(
            name="ReviewerAgent",
            system_message="""You are a quality reviewer. Check if the explanation:
            1. Aligns with provided scores
            2. Contains no hallucinations
            3. Is clear and actionable
            If issues found, suggest improvements. Otherwise, approve.""",
            llm_config=llm_config,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1
        )
    
    def explain(self, match_result: Dict, ats_score: float) -> Dict:
        """
        Generate explanation from Agent 3 and ATS outputs
        
        Args:
            match_result: Agent 3 output containing:
                - job_title, score, decision, matched_skills, missing_skills, etc.
            ats_score: ATS Engine score (0-100)
        
        Returns:
            {
                "hr_summary": str,
                "strengths": List[str],
                "weaknesses": List[str],
                "recommendations": List[str],
                "interview_focus": List[str]
            }
        """
        # Use mock mode if LangChain unavailable
        if self.use_mock:
            return self._mock_explanation(match_result, ats_score)
        
        # Prepare input data
        input_data = {
            "candidate_name": match_result.get("candidate_name", "Candidate"),
            "job_title": match_result.get("job_title", "Position"),
            "rule_score": match_result.get("score", 0),
            "decision": match_result.get("decision", "REVIEW"),
            "matched_skills": ", ".join(match_result.get("matched_skills", [])),
            "missing_skills": ", ".join(match_result.get("missing_skills", [])),
            "experience_years": match_result.get("experience_years", 0),
            "required_experience": match_result.get("required_experience", 0),
            "ats_score": ats_score
        }
        
        try:
            if self.use_autogen:
                return self._explain_with_autogen(input_data)
            else:
                return self._explain_with_langchain(input_data)
        except Exception as e:
            self.logger.error(f"Explanation generation failed: {e}")
            return self._mock_explanation(match_result, ats_score)
    
    def _explain_with_langchain(self, input_data: Dict) -> Dict:
        """Generate explanation using LangChain only"""
        prompt = self.prompt_template.format(**input_data)
        response = self.llm.invoke(prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            explanation = json.loads(response_text)
            return self._validate_output(explanation)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            return self._mock_explanation(input_data, input_data["ats_score"])
    
    def _explain_with_autogen(self, input_data: Dict) -> Dict:
        """Generate explanation using AutoGen (Explainer + Reviewer)"""
        # Format prompt for explainer
        prompt = self.prompt_template.format(**input_data)
        
        # Single-round conversation: Explainer generates, Reviewer validates
        self.reviewer_agent.initiate_chat(
            self.explainer_agent,
            message=f"Generate an explanation for this candidate-job match:\n\n{prompt}",
            max_turns=2
        )
        
        # Extract JSON from the conversation history
        # We need to find the last message from the ExplainerAgent that contains JSON code blocks
        chat_history = self.reviewer_agent.chat_messages[self.explainer_agent]
        
        json_content = None
        
        # Iterate backwards to find the explanation
        for msg in reversed(chat_history):
            content = msg.get("content", "")
            if "```json" in content or "```" in content:
                # Potential candidate
                json_content = content
                break
                
        if not json_content:
             # If no JSON found in history, try the very last message just in case
            json_content = chat_history[-1]["content"]

        # Parse JSON
        try:
            # Extract JSON from response
            response_text = json_content.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                 # Generic code block
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            explanation = json.loads(response_text)
            return self._validate_output(explanation)
        except Exception as e:
            self.logger.error(f"AutoGen parsing failed: {e}")
            # Fallback to LangChain direct invoke which is more reliable for format
            return self._explain_with_langchain(input_data)
    
    def _validate_output(self, explanation: Dict) -> Dict:
        """Validate and sanitize output schema"""
        required_keys = ["hr_summary", "strengths", "weaknesses", "recommendations", "interview_focus"]
        
        # Ensure all keys exist
        for key in required_keys:
            if key not in explanation:
                explanation[key] = [] if key != "hr_summary" else "No summary available."
        
        # Ensure lists
        for key in ["strengths", "weaknesses", "recommendations", "interview_focus"]:
            if not isinstance(explanation[key], list):
                explanation[key] = [str(explanation[key])]
        
        return explanation
    
    def _mock_explanation(self, match_result: Dict, ats_score: float) -> Dict:
        """Fallback mock explanation when LLM unavailable"""
        decision = match_result.get("decision", "REVIEW")
        score = match_result.get("score", 0)
        matched = match_result.get("matched_skills", [])
        missing = match_result.get("missing_skills", [])
        
        return {
            "hr_summary": f"Candidate received {decision} decision with {score}% match score and {ats_score}% ATS score.",
            "strengths": [
                f"Possesses {len(matched)} required skills" if matched else "Experience in the field",
                f"ATS score of {ats_score}% indicates good resume optimization"
            ],
            "weaknesses": [
                f"Missing {len(missing)} key skills: {', '.join(missing[:3])}" if missing else "Limited skill coverage"
            ],
            "recommendations": [
                "Conduct technical screening to validate skills",
                "Assess cultural fit and soft skills"
            ],
            "interview_focus": [
                "Technical depth in matched skills",
                "Learning approach for missing skills"
            ]
        }


# Singleton instance
_agent_instance = None

def get_agent() -> ExplanationAgent:
    """Get or create Agent 4 singleton"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ExplanationAgent(use_autogen=True)
    return _agent_instance

def explain(match_result: Dict, ats_score: float) -> Dict:
    """
    Public API: Generate explanation
    
    Args:
        match_result: Agent 3 output
        ats_score: ATS Engine score
    
    Returns:
        Structured explanation dict
    """
    agent = get_agent()
    return agent.explain(match_result, ats_score)
