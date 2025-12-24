"""
AI Resume Matcher - Black & White Glassmorphism Theme
Tabbed Dashboard Interface
"""
import streamlit as st
from pathlib import Path
import sys
import os
import tempfile
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page config - NO SIDEBAR
st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# BLACK & WHITE GLASSMORPHISM THEME
st.markdown("""
<style>
    /* === BACKGROUND === */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
        background-attachment: fixed;
    }
    
    /* HIDE SIDEBAR COMPLETELY */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* === GLASSMORPHISM CONTAINERS === */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 
            0 8px 32px 0 rgba(0, 0, 0, 0.7),
            inset 0 0 60px rgba(255, 255, 255, 0.02);
        margin-bottom: 1.5rem;
    }
    
    /* === HEADER === */
    .main-header {
        text-align: center;
        padding: 2rem 0 2rem 0;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 900;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-bottom: 0.5rem;
        text-shadow: 
            0 0 20px rgba(255, 255, 255, 0.3),
            0 0 40px rgba(255, 255, 255, 0.2);
        font-family: 'Inter', sans-serif;
    }
    
    .main-subtitle {
        font-size: 0.9rem;
        color: #999999;
        font-weight: 400;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* === BUTTONS === */
    .stButton > button {
        background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
        color: #0a0a0a;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
        font-size: 0.95rem;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #e0e0e0 0%, #cccccc 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.3);
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        padding: 1rem 2rem;
        color: #999999;
        border: 1px solid transparent;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.9rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
        color: #0a0a0a !important;
        border-color: #ffffff;
        box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
    }
    
    /* === TEXT COLORS === */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
    }
    
    p, span, div {
        color: #cccccc !important;
    }
    
    label {
        color: #999999 !important;
        font-weight: 600;
    }
    
    /* === METRICS === */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 900;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        font-size: 2rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #999999 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* === FILE UPLOADER === */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.05);
        border: 2px dashed rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 2rem;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(255, 255, 255, 0.4);
        background: rgba(255, 255, 255, 0.08);
    }
    
    /* === MATCH CARDS === */
    .match-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .match-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateX(8px);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    .match-high { border-left: 4px solid #ffffff; }
    .match-medium { border-left: 4px solid #cccccc; }
    .match-low { border-left: 4px solid #999999; }
    
    /* === EXPANDERS === */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff !important;
        font-weight: 700;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.08);
    }
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Backend
@st.cache_resource
def get_backend():
    from src.backend import HRBackend
    backend = HRBackend()
    backend.initialize()
    return backend

# Load sample profiles
@st.cache_data
def load_sample_profiles():
    sample_path = Path(__file__).parent.parent / "data" / "json" / "sample_profiles.json"
    if sample_path.exists():
        with open(sample_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

bk = get_backend()
sample_profiles = load_sample_profiles()

# Header
st.markdown("""
<div class="main-header">
    <div class="main-title">AI RESUME MATCHER</div>
    <div class="main-subtitle">Advanced AI-Powered Talent Acquisition System</div>
</div>
""", unsafe_allow_html=True)

# TABBED INTERFACE
tab1, tab2, tab3 = st.tabs(["UPLOAD & MATCH", "MATCH RESULTS", "JOB MANAGEMENT"])

# ==================== TAB 1: UPLOAD & MATCH ====================
with tab1:
    st.markdown("### Upload Resume")
    st.markdown("**Get top 5 job matches instantly**")
    
    # Create two columns: File upload and Sample CVs
    col_upload, col_sample = st.columns([1, 1])
    
    with col_upload:
        st.markdown("#### Upload Resume File")
        
        uploaded_file = st.file_uploader(
            "Drag and drop or click to browse",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Supported: PDF, DOCX, DOC, TXT",
            key="cv_uploader"
        )
        
        if uploaded_file is not None:
            st.success(f"File uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            
            if st.button("Find Top 5 Jobs", type="primary", use_container_width=True, key="process_file"):
                with st.spinner("Processing resume..."):
                    try:
                        from src.agents.agent1_parser import RawParser
                        
                        file_type = uploaded_file.name.split('.')[-1].upper()
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type.lower()}') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        parser = RawParser()
                        try:
                            if file_type == 'PDF':
                                cv_text = parser.extract_text_from_pdf(tmp_path)
                            elif file_type in ['DOCX', 'DOC']:
                                cv_text = parser.extract_text_from_docx(tmp_path)
                            elif file_type == 'TXT':
                                cv_text = parser.extract_text_from_txt(tmp_path)
                            else:
                                raise ValueError(f"Unsupported file type: {file_type}")
                            
                            os.unlink(tmp_path)
                            
                            if not cv_text.strip():
                                st.error("Could not extract text. Try a different format.")
                            else:
                                result = bk.process_match(profile_text=cv_text, top_k=5)
                                
                                st.session_state['match_results'] = result
                                st.session_state['last_match_time'] = datetime.now()
                                
                                st.success(f"Found top 5 matches in {result['processing_time_seconds']:.1f} seconds!")
                                
                                st.markdown("### Top 5 Matches")
                                for i, match in enumerate(result['top_matches'][:5], 1):
                                    match_class = f"match-{match['match_label'].lower()}"
                                    icon = "[H]" if match['match_label'] == 'High' else "[M]" if match['match_label'] == 'Medium' else "[L]"
                                    st.markdown(f"""
                                    <div class='match-card {match_class}'>
                                        <h4>{icon} #{i} - {match['job_title']}</h4>
                                        <p><strong>Match:</strong> {match['match_label']} | <strong>Confidence:</strong> {match['confidence']:.0%}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        except Exception as parse_error:
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                            st.error(f"Error parsing file: {str(parse_error)}")
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with col_sample:
        st.markdown("#### Or Try Sample CVs")
        
        if sample_profiles:
            sample_names = [p['name'] for p in sample_profiles]
            selected_sample = st.selectbox("Select a sample CV:", ["Choose a sample..."] + sample_names, key="sample_selector")
            
            if selected_sample != "Choose a sample...":
                sample_data = next((p for p in sample_profiles if p['name'] == selected_sample), None)
                
                if sample_data:
                    st.info(f"Selected: **{sample_data['name']}**")
                    
                    with st.expander("View Sample CV", expanded=False):
                        st.text_area("CV Content", sample_data['text'], height=200, disabled=True, key="sample_preview")
                    
                    if st.button("Find Matches for Sample", type="primary", use_container_width=True, key="process_sample"):
                        with st.spinner("Processing sample CV..."):
                            try:
                                result = bk.process_match(profile_text=sample_data['text'], top_k=5)
                                
                                st.session_state['match_results'] = result
                                st.session_state['last_match_time'] = datetime.now()
                                
                                st.success(f"Found top 5 matches in {result['processing_time_seconds']:.1f} seconds!")
                                
                                st.markdown("### Top 5 Matches")
                                for i, match in enumerate(result['top_matches'][:5], 1):
                                    match_class = f"match-{match['match_label'].lower()}"
                                    icon = "[H]" if match['match_label'] == 'High' else "[M]" if match['match_label'] == 'Medium' else "[L]"
                                    st.markdown(f"""
                                    <div class='match-card {match_class}'>
                                        <h4>{icon} #{i} - {match['job_title']}</h4>
                                        <p><strong>Match:</strong> {match['match_label']} | <strong>Confidence:</strong> {match['confidence']:.0%}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        else:
            st.warning("No sample CVs available")
    
    # Text paste option
    st.markdown("---")
    st.markdown("#### Or Paste Resume Text")
    
    cv_text = st.text_area(
        "Paste resume content:",
        height=200,
        placeholder="Paste full resume text here...",
        help="Paste full resume text",
        key="paste_text"
    )
    
    if st.button("Find Top 5 Jobs", type="primary", key="process_text"):
        if not cv_text.strip():
            st.error("Please paste a resume first")
        else:
            with st.spinner("Processing..."):
                try:
                    result = bk.process_match(profile_text=cv_text, top_k=5)
                    
                    st.session_state['match_results'] = result
                    st.session_state['last_match_time'] = datetime.now()
                    
                    st.success(f"Found top 5 matches in {result['processing_time_seconds']:.1f} seconds!")
                    
                    st.markdown("### Top 5 Matches")
                    for i, match in enumerate(result['top_matches'][:5], 1):
                        match_class = f"match-{match['match_label'].lower()}"
                        icon = "[H]" if match['match_label'] == 'High' else "[M]" if match['match_label'] == 'Medium' else "[L]"
                        st.markdown(f"""
                        <div class='match-card {match_class}'>
                            <h4>{icon} #{i} - {match['job_title']}</h4>
                            <p><strong>Match:</strong> {match['match_label']} | <strong>Confidence:</strong> {match['confidence']:.0%}</p>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ==================== TAB 2: MATCH RESULTS ====================
with tab2:
    st.markdown("### Match Results")
    
    if 'match_results' not in st.session_state:
        st.info("No match results yet. Go to UPLOAD & MATCH tab to find matches!")
    else:
        results = st.session_state['match_results']
        
        st.markdown(f"#### Candidate: **{results['candidate_name']}**")
        st.markdown(f"**Total Jobs Scored:** {results['total_jobs_scored']} | **Processing Time:** {results['processing_time_seconds']:.2f}s")
        
        st.markdown("---")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        matches = results['top_matches']
        
        shortlist_count = sum(1 for m in matches if m.get('decision') == 'SHORTLIST')
        review_count = sum(1 for m in matches if m.get('decision') == 'REVIEW')
        reject_count = sum(1 for m in matches if m.get('decision') == 'REJECT')
        
        with col1:
            st.metric("SHORTLIST", shortlist_count, "Strong Matches")
        with col2:
            st.metric("REVIEW", review_count, "Moderate Matches")
        with col3:
            st.metric("REJECT", reject_count, "Weak Matches")
        with col4:
            st.metric("Total", len(matches))
        
        st.markdown("---")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_match = st.multiselect(
                "Filter by Match Quality:",
                options=["High", "Medium", "Low"],
                default=["High", "Medium", "Low"]
            )
        
        with col2:
            min_confidence = st.slider(
                "Minimum Confidence:",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1
            )
        
        # Apply filters
        filtered_matches = [m for m in matches if m.get('match_label') in filter_match]
        filtered_matches = [m for m in filtered_matches if m.get('confidence', 0) >= min_confidence]
        
        st.markdown(f"### Showing {len(filtered_matches)} of {len(matches)} matches")
        
        # Display matches
        for i, match in enumerate(filtered_matches, 1):
            if match['match_label'] == 'High':
                border_color = "#ffffff"
                icon = "[H]"
            elif match['match_label'] == 'Medium':
                border_color = "#cccccc"
                icon = "[M]"
            else:
                border_color = "#999999"
                icon = "[L]"
            
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); 
                     border: 1px solid rgba(255, 255, 255, 0.1); border-left: 4px solid {border_color}; 
                     border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
                """, unsafe_allow_html=True)
                
                st.markdown(f"### {icon} #{match.get('ranking', i)} - {match['job_title']}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Match Quality", match['match_label'])
                
                with col2:
                    st.metric("Confidence", f"{match['confidence']:.0%}")
                
                with col3:
                    st.metric("Skill Match", f"{match['skill_match']['skill_match_score']:.0%}")
                
                with col4:
                    st.metric("Experience Match", f"{match['experience_match_score']:.0%}")
                
                if match.get('explanation'):
                    st.markdown("**Explanation:**")
                    st.info(match['explanation'])
                
                with st.expander("Skills Breakdown"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Matched Skills:**")
                        if match['skill_match']['matched_skills']:
                            for skill in match['skill_match']['matched_skills']:
                                st.markdown(f"- {skill}")
                        else:
                            st.markdown("_None_")
                    
                    with col2:
                        st.markdown("**Missing Skills:**")
                        if match['skill_match']['missing_skills']:
                            for skill in match['skill_match']['missing_skills']:
                                st.markdown(f"- {skill}")
                        else:
                            st.markdown("_None_")
                
                st.markdown("</div>", unsafe_allow_html=True)

# ==================== TAB 3: JOB MANAGEMENT ====================
with tab3:
    st.markdown("### Job Management")
    st.markdown("Browse and explore available job postings")
    
    # Get jobs (limit to 200)
    try:
        all_jobs = bk.get_jobs(limit=200)
    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        all_jobs = []
    
    if not all_jobs:
        st.warning("No jobs loaded. Check if jobs data is available.")
    else:
        # Filters
        st.markdown("### Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categories = list(set(job.get('role_category', 'General') for job in all_jobs))
            categories.sort()
            
            selected_categories = st.multiselect(
                "Role Category:",
                options=categories,
                default=categories[:3] if len(categories) >= 3 else categories
            )
        
        with col2:
            min_exp = st.slider("Minimum Experience (years):", 0, 20, 0)
        
        with col3:
            search_term = st.text_input("Search jobs:", placeholder="Enter keyword...")
        
        # Filter jobs
        filtered_jobs = all_jobs
        
        if selected_categories:
            filtered_jobs = [j for j in filtered_jobs if j.get('role_category', 'General') in selected_categories]
        
        if min_exp > 0:
            filtered_jobs = [j for j in filtered_jobs if j.get('min_experience_years', 0) >= min_exp]
        
        if search_term:
            search_lower = search_term.lower()
            filtered_jobs = [
                j for j in filtered_jobs 
                if search_lower in j.get('title', '').lower() or 
                   search_lower in ' '.join(j.get('required_skills', [])).lower()
            ]
        
        st.markdown(f"### Showing {len(filtered_jobs)} jobs")
        
        # Display jobs
        for i, job in enumerate(filtered_jobs[:50], 1):  # Show max 50
            with st.expander(f"#{i} - {job.get('title', 'N/A')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Job ID:** {job.get('job_id', 'N/A')}")
                    st.markdown(f"**Category:** {job.get('role_category', 'General')}")
                    min_exp = job.get('min_experience_years', 0)
                    st.markdown(f"**Experience:** {min_exp}+ years")
                
                with col2:
                    skills = job.get('skills_required', job.get('required_skills', []))
                    if skills:
                        st.markdown("**Required Skills:**")
                        for skill in skills[:10]:
                            st.markdown(f"- {skill}")
                        if len(skills) > 10:
                            st.caption(f"... and {len(skills) - 10} more")
                    else:
                        st.markdown("**Required Skills:** None specified")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999999; font-size: 0.9rem;">
    <p>AI RESUME MATCHER v2.0 | Rule-Based ML Pipeline | Zero External APIs</p>
    <p style="color: #ffffff; font-weight: 700;">SYSTEM OPERATIONAL • 3 AGENTS ACTIVE</p>
</div>
""", unsafe_allow_html=True)
