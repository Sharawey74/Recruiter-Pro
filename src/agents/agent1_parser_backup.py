"""
Agent 1: Parsing & Raw Extraction
Type: Deterministic, Rule-based
Purpose: Extract raw content from CV/Resume and Job Descriptions without NLP/AI.
Output: Raw unstructured text blocks.
"""
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# File processing imports
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: pdfminer.six not available. PDF parsing disabled.")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. DOCX parsing disabled.")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Arabic support imports
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available. Arabic PDF support limited.")

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # Ensure consistent detection
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("Warning: langdetect not available. Language detection disabled.")

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("Warning: deep-translator not available. Translation disabled.")

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_RESHAPER_AVAILABLE = True
except ImportError:
    ARABIC_RESHAPER_AVAILABLE = False
    print("Warning: arabic-reshaper not available. RTL text fixing disabled.")

# Import parent directories for utility imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RawParser:
    """
    Agent 1: Extracts raw text from files and segments them into raw blocks.
    Strictly NO NLP/AI (No SpaCy, No NLTK).
    """
    
    def __init__(self, output_dir: str = "data/processed/raw_profiles"):
        """
        Initialize the parser with Arabic support.
        
        Args:
            output_dir: Directory to save parsed raw profiles
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize translator if available
        self.translator = None
        if TRANSLATOR_AVAILABLE:
            try:
                self.translator = GoogleTranslator(source='ar', target='en')
            except Exception as e:
                print(f"Warning: Could not initialize translator: {e}")
        
        print(f"✅ Agent 1 (RawParser) initialized. Output dir: {self.output_dir}")
        if PDFPLUMBER_AVAILABLE:
            print("  ✓ Arabic PDF support enabled (pdfplumber)")
        if LANGDETECT_AVAILABLE:
            print("  ✓ Language detection enabled")
        if TRANSLATOR_AVAILABLE:
            print("  ✓ Translation enabled (Arabic → English)")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file with Arabic support.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        text = ""
        
        # Try pdfplumber first (best for Arabic)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    return self._fix_arabic_display(text)
            except Exception as e:
                print(f"pdfplumber extraction failed: {e}, trying fallback...")
        
        # Fallback to PyMuPDF
        if PYMUPDF_AVAILABLE and not text.strip():
            try:
                doc = fitz.open(pdf_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
                if text.strip():
                    return self._fix_arabic_display(text)
            except Exception as e:
                print(f"PyMuPDF extraction failed: {e}")
        
        # Final fallback to pdfminer.six
        if PDF_AVAILABLE and not text.strip():
            try:
                text = pdf_extract_text(pdf_path)
                return self._fix_arabic_display(text)
            except Exception as e:
                raise RuntimeError(f"PDF extraction failed: {e}")
        
        if not text.strip():
            raise RuntimeError("No PDF parsing library available or extraction failed.")
        
        return text
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        if not DOCX_AVAILABLE:
            raise RuntimeError("python-docx not available. Install python-docx to parse DOCX files.")
        
        docx_file = Path(docx_path)
        if not docx_file.exists():
            raise FileNotFoundError(f"DOCX file not found: {docx_path}")
        
        try:
            doc = Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed: {e}")
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """
        Extract text from TXT file.
        
        Args:
            txt_path: Path to TXT file
            
        Returns:
            Text content
        """
        txt_file = Path(txt_path)
        if not txt_file.exists():
            raise FileNotFoundError(f"TXT file not found: {txt_path}")
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            try:
                # Try with different encoding
                with open(txt_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e2:
                raise RuntimeError(f"TXT extraction failed: {e2}")
    
    def parse_file(self, file_path: str, profile_id: Optional[str] = None) -> Dict:
        """
        Parse a file (PDF, DOCX, or TXT) and extract raw text.
        
        Args:
            file_path: Path to file
            profile_id: Optional profile identifier
            
        Returns:
            Dictionary with raw text blocks
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        
        # Extract text based on file type
        if suffix == '.pdf':
            text = self.extract_text_from_pdf(str(file_path))
        elif suffix in ['.docx', '.doc']:
            text = self.extract_text_from_docx(str(file_path))
        elif suffix == '.txt':
            text = self.extract_text_from_txt(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Supported: .pdf, .docx, .txt")
        
        # Use filename as profile_id if not provided
        if not profile_id:
            profile_id = f"profile_{file_path.stem}"
        
        return self.parse_profile(text, profile_id)
    
    def parse_profile(self, profile_text: str, profile_id: Optional[str] = None) -> Dict:
        """
        Parse a profile text into raw sections using Regex/Rule-based logic.
        
        Args:
            profile_text: Raw resume text
            profile_id: Optional profile identifier
            
        Returns:
            Dictionary with raw text blocks
        """
        if not profile_id:
            profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        # 1. Clean basic whitespace
        cleaned_text = self._basic_clean(profile_text)
        
        # 2. Segment into raw sections using Regex keywords
        sections = self._segment_text(cleaned_text)
        
        # 3. Construct RAW output (No structured fields yet)
        profile_data = {
            "profile_id": profile_id,
            "raw_text": cleaned_text,
            "sections": sections,
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "v2.0_raw_only"
        }
        
        # 4. Save to file
        self._save_output(profile_data, profile_id)
        
        return profile_data

    def parse_job(self, job_data: Dict) -> Dict:
        """
        Pass-through for job data to ensure consistent raw output format.
        
        Args:
            job_data: Dictionary containing job information (usually already structured from dataset)
            
        Returns:
            Dictionary with raw job data
        """
        # For jobs, we primarily just pass them through but ensure specific fields exist
        job_id = str(job_data.get('Job Id', 'unknown'))
        
        return {
            "job_id": job_id,
            "raw_text": json.dumps(job_data),  # Raw representation
            "original_data": job_data,         # Keep original for Agent 2 to process
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "v2.0_raw_only"
        }

    def _basic_clean(self, text: str) -> str:
        """Basic whitespace cleanup only."""
        return "\n".join([line.strip() for line in text.split("\n") if line.strip()])

    def _segment_text(self, text: str) -> Dict[str, str]:
        """
        Segment text into broad sections (Experience, Education, Skills) using Regex.
        This is a heuristic approach, not NLP.
        """
        sections = {
            "contact_block": "",
            "experience_block": "",
            "education_block": "",
            "skills_block": "",
            "summary_block": ""
        }
        
        # Define simplistic section headers (case insensitive)
        headers = {
            "experience": r"(work experience|employment history|experience|professional background)",
            "education": r"(education|academic background|qualifications)",
            "skills": r"(skills|technical skills|competencies|expertise)",
            "summary": r"(summary|objective|profile|about me)"
        }
        
        lines = text.split('\n')
        current_section = "contact_block" # Default top section
        
        for line in lines:
            # Check if line is a header
            is_header = False
            for section_name, pattern in headers.items():
                if re.match(f"^{pattern}$", line.lower().strip()):
                    current_section = f"{section_name}_block"
                    is_header = True
                    break
            
            if not is_header:
                sections[current_section] += line + "\n"
                
        return {k: v.strip() for k, v in sections.items()}

    def _save_output(self, data: Dict, profile_id: str):
        """Save raw parsed data to JSON."""
        output_path = self.output_dir / f"{profile_id}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

