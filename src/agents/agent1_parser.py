"""
Agent 1: Parsing & Raw Extraction
Type: Deterministic, Rule-based
Purpose: Extract raw content from CV/Resume and Job Descriptions without NLP/AI.
Output: Raw unstructured text blocks.
"""

import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# File processing imports
try:
    from pdfminer.high_level import extract_text as pdf_extract_text

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pdfminer.six not available. PDF parsing disabled.")

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. DOCX parsing disabled.")

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Import parent directories for utility imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class RawParser:
    """
    Agent 1: Extracts raw text from files and segments them into raw blocks.
    Strictly NO NLP/AI (No SpaCy, No NLTK).
    """

    # A CV that extracts fewer characters than this is not a CV we parsed --
    # it is almost always a scanned image PDF with no text layer. Returning the
    # near-empty string produced a profile with no skills, which scored as a
    # poor match rather than as a failed parse.
    MIN_EXTRACTED_CHARS = 50

    def __init__(self, output_dir: str = "data/processed/raw_profiles"):
        """
        Initialize the parser.

        Args:
            output_dir: Where parse_profile(save=True) writes, if used at all.

        Constructing a parser has no side effects: no directory is created and
        nothing is logged. The directory is created lazily on the first actual
        save. Previously __init__ ran mkdir() and printed, so importing the
        module was enough to touch the filesystem.
        """
        self.output_dir = Path(output_dir)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file using available library.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Try PyMuPDF first (faster and more accurate)
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}")

        # Fallback to pdfminer.six
        if PDF_AVAILABLE:
            try:
                return pdf_extract_text(pdf_path)
            except Exception as e:
                raise RuntimeError(f"PDF extraction failed: {e}") from e

        raise RuntimeError("No PDF parsing library available. Install pdfminer.six or PyMuPDF.")

    def extract_text_from_docx(self, docx_path: str) -> str:
        """
        Extract text from DOCX file.

        Args:
            docx_path: Path to DOCX file

        Returns:
            Extracted text content
        """
        if not DOCX_AVAILABLE:
            raise RuntimeError(
                "python-docx not available. Install python-docx to parse DOCX files."
            )

        docx_file = Path(docx_path)
        if not docx_file.exists():
            raise FileNotFoundError(f"DOCX file not found: {docx_path}")

        try:
            doc = Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed: {e}") from e

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
            with open(txt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            try:
                # Try with different encoding
                with open(txt_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e2:
                raise RuntimeError(f"TXT extraction failed: {e2}") from e2

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
        if suffix == ".pdf":
            text = self.extract_text_from_pdf(str(file_path))
        elif suffix in [".docx", ".doc"]:
            text = self.extract_text_from_docx(str(file_path))
        elif suffix == ".txt":
            text = self.extract_text_from_txt(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Supported: .pdf, .docx, .txt")

        # Fail loudly on a document we did not actually read. A scanned image
        # PDF has no text layer, so extraction returns near-nothing; that used
        # to flow through as a CV with no skills and score as a weak match
        # instead of as a parse failure the user could act on.
        if len(text.strip()) < self.MIN_EXTRACTED_CHARS:
            raise ValueError(
                f"Extracted only {len(text.strip())} characters from {file_path.name}. "
                f"The file is probably a scanned image with no text layer, or empty. "
                f"Minimum is {self.MIN_EXTRACTED_CHARS}."
            )

        # Use filename as profile_id if not provided
        if not profile_id:
            profile_id = f"profile_{file_path.stem}"

        return self.parse_profile(text, profile_id)

    def parse_profile(
        self, profile_text: str, profile_id: Optional[str] = None, save: bool = False
    ) -> Dict:
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
            "parser_version": "v2.0_raw_only",
        }

        # Writing is opt-in. Every parse used to drop a JSON into
        # data/processed/raw_profiles/ that nothing ever read -- 66 orphaned
        # files had accumulated, most of them named after pytest temp files.
        if save:
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
        job_id = str(job_data.get("Job Id", "unknown"))

        return {
            "job_id": job_id,
            "raw_text": json.dumps(job_data),  # Raw representation
            "original_data": job_data,  # Keep original for Agent 2 to process
            "parsed_at": datetime.now().isoformat(),
            "parser_version": "v2.0_raw_only",
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
            "summary_block": "",
        }

        # Define simplistic section headers (case insensitive)
        headers = {
            "experience": r"(work experience|employment history|experience|professional background)",
            "education": r"(education|academic background|qualifications)",
            "skills": r"(skills|technical skills|competencies|expertise)",
            "summary": r"(summary|objective|profile|about me)",
        }

        lines = text.split("\n")
        current_section = "contact_block"  # Default top section

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
        """Save raw parsed data to JSON. Creates the directory on first use."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{profile_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
