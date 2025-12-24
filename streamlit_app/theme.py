# Black & White Glassmorphism Theme CSS - Shared across all pages
BLACK_WHITE_THEME_CSS = """
<style>
    /* === BACKGROUND === */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
        background-attachment: fixed;
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
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 
            0 8px 32px 0 rgba(0, 0, 0, 0.5),
            inset 0 0 40px rgba(255, 255, 255, 0.05),
            0 0 20px rgba(255, 255, 255, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* === HEADER === */
    .page-header {
        text-align: center;
        padding: 1.5rem 0 2rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .page-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 0.5rem;
        text-shadow: 
            0 0 10px rgba(255, 255, 255, 0.4),
            0 0 20px rgba(255, 255, 255, 0.2);
        font-family: 'Courier New', monospace;
    }
    
    /* === BUTTONS === */
    .stButton > button {
        background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
        color: #0a0a0a;
        border: none;
        border-radius: 12px;
        padding: 0.9rem 2.5rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
        font-size: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(255, 255, 255, 0.3);
        background: linear-gradient(135deg, #e0e0e0 0%, #cccccc 100%);
    }
    
    /* === TEXT COLORS === */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
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
    }
    
    [data-testid="stMetricLabel"] {
        color: #999999 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* === INPUT FIELDS === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(26, 29, 29, 0.8);
        border: 1px solid rgba(57, 255, 20, 0.3);
        border-radius: 10px;
        color: #ffffff;
        padding: 0.8rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #39ff14;
        box-shadow: 0 0 0 2px rgba(57, 255, 20, 0.2);
    }
    
    /* === FILE UPLOADER === */
    .stFileUploader {
        background: rgba(26, 29, 29, 0.6);
        border: 2px dashed rgba(57, 255, 20, 0.4);
        border-radius: 16px;
        padding: 2rem;
    }
    
    /* === STATUS BADGES === */
    .status-shortlist {
        background: rgba(57, 255, 20, 0.2);
        color: #39ff14;
        border: 1px solid #39ff14;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .status-review {
        background: rgba(255, 165, 0, 0.2);
        color: #ffa500;
        border: 1px solid #ffa500;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .status-reject {
        background: rgba(255, 0, 0, 0.2);
        color: #ff0000;
        border: 1px solid #ff0000;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: rgba(26, 29, 29, 0.8);
        border-radius: 10px;
        border: 1px solid rgba(57, 255, 20, 0.3);
        color: #39ff14 !important;
        font-weight: 700;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #39ff14;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.3);
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: rgba(26, 29, 29, 0.5);
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        color: #39ff14;
        border: 1px solid transparent;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #39ff14 0%, #00ff7f 100%);
        color: #050505 !important;
        border-color: #39ff14;
        box-shadow: 0 0 20px rgba(57, 255, 20, 0.5);
    }
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(26, 29, 29, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: #39ff14;
        border-radius: 5px;
    }
</style>
"""
