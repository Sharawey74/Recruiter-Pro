from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
import streamlit as st

@dataclass
class ResumeData:
    """Structured data for the uploaded/parsed resume"""
    text: str
    source_name: str  # Filename or 'Pasted Text'
    parsed_profile: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MatchData:
    """Results from the matching engine"""
    candidate_name: str
    top_matches: List[Dict]
    total_jobs: int
    processing_time: float
    ats_result: Optional[Dict] = None

class StateManager:
    """
    Central session state manager for RecruitPro AI.
    Enforces the pipeline: Resume -> ATS/Match -> Results
    """
    
    # Keys for Streamlit Session State
    KEY_RESUME = 'pipeline_resume'
    KEY_MATCHES = 'pipeline_matches'
    KEY_STEP = 'pipeline_current_step'
    
    def __init__(self):
        # Initialize default state if missing
        if self.KEY_RESUME not in st.session_state:
            st.session_state[self.KEY_RESUME] = None
        if self.KEY_MATCHES not in st.session_state:
            st.session_state[self.KEY_MATCHES] = None
        if self.KEY_STEP not in st.session_state:
            st.session_state[self.KEY_STEP] = 1

    @property
    def resume(self) -> Optional[ResumeData]:
        return st.session_state[self.KEY_RESUME]

    @resume.setter
    def resume(self, data: ResumeData):
        st.session_state[self.KEY_RESUME] = data
        # Reset downstream data when new resume is loaded
        st.session_state[self.KEY_MATCHES] = None
        self.set_step(2) # Move to next logical step (Analysis)

    @property
    def matches(self) -> Optional[MatchData]:
        return st.session_state[self.KEY_MATCHES]

    @matches.setter
    def matches(self, data: MatchData):
        st.session_state[self.KEY_MATCHES] = data
        self.set_step(3) # Move to Results

    @property
    def current_step(self) -> int:
        return st.session_state[self.KEY_STEP]

    def set_step(self, step: int):
        """Secure step transition logic"""
        # Prevent jumping ahead without data
        if step > 1 and not self.resume:
            st.warning("⚠️ Please import a resume first.")
            return
        
        if step > 2 and not self.matches:
            st.warning("⚠️ Please run the analysis first.")
            return

        st.session_state[self.KEY_STEP] = step

    def clear_session(self):
        """Full reset"""
        st.session_state[self.KEY_RESUME] = None
        st.session_state[self.KEY_MATCHES] = None
        st.session_state[self.KEY_STEP] = 1
