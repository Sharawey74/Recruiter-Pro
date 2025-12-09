"""
Text processing utilities for resume and job description parsing.
"""
import re
import string
from typing import List
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing special characters, extra whitespace, etc.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text string
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters but keep spaces and basic punctuation
    text = re.sub(r'[^\w\s\-\.,;:]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def remove_stopwords(text: str, custom_stopwords: List[str] = None) -> str:
    """
    Remove common stopwords from text.
    
    Args:
        text: Text to process
        custom_stopwords: Additional stopwords to remove
        
    Returns:
        Text with stopwords removed
    """
    if not text:
        return ""
    
    # Get English stopwords
    stop_words = set(stopwords.words('english'))
    
    # Add custom stopwords if provided
    if custom_stopwords:
        stop_words.update(custom_stopwords)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    filtered_tokens = [word for word in tokens if word.lower() not in stop_words]
    
    return ' '.join(filtered_tokens)


def extract_years_of_experience(text: str) -> int:
    """
    Extract years of experience from text using regex patterns.
    
    Args:
        text: Text containing experience information
        
    Returns:
        Number of years (integer), or 0 if not found
    """
    if not text:
        return 0
    
    # Common patterns for experience
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)',
        r'experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    
    return 0


def extract_email(text: str) -> str:
    """
    Extract email address from text.
    
    Args:
        text: Text containing email
        
    Returns:
        Email address or empty string
    """
    if not text:
        return ""
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    """
    Extract phone number from text.
    
    Args:
        text: Text containing phone number
        
    Returns:
        Phone number or empty string
    """
    if not text:
        return ""
    
    # Common phone patterns
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return ""


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    return re.sub(r'\s+', ' ', text).strip()


def extract_section(text: str, section_name: str) -> str:
    """
    Extract a specific section from resume text.
    
    Args:
        text: Full resume text
        section_name: Name of section to extract (e.g., 'experience', 'education')
        
    Returns:
        Section text or empty string
    """
    if not text:
        return ""
    
    # Common section headers
    section_patterns = {
        'experience': r'(?:work\s+)?experience|employment\s+history|professional\s+experience',
        'education': r'education|academic\s+background|qualifications',
        'skills': r'skills|technical\s+skills|core\s+competencies',
        'summary': r'summary|profile|objective|about\s+me',
    }
    
    pattern = section_patterns.get(section_name.lower(), section_name)
    
    # Find section start
    section_start = re.search(rf'\b{pattern}\b', text, re.IGNORECASE)
    if not section_start:
        return ""
    
    # Extract from section start to next section or end
    start_pos = section_start.end()
    
    # Find next section
    next_section = re.search(r'\n\s*[A-Z][A-Za-z\s]+:\s*\n', text[start_pos:])
    if next_section:
        end_pos = start_pos + next_section.start()
    else:
        end_pos = len(text)
    
    return text[start_pos:end_pos].strip()
