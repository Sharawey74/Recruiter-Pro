"""
Agent 1: Profile & Job Parser
Handles parsing of resumes/profiles and job descriptions using NLP.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# NLP imports with fallback
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Warning: spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
        SPACY_AVAILABLE = False
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not installed. Using NLTK fallback.")

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag

# Import utilities
from src.utils.text_processing import (
    clean_text,
    extract_years_of_experience,
    extract_email,
    extract_phone,
    extract_section,
    normalize_whitespace
)
from src.utils.skill_extraction import (
    extract_skills,
    extract_skills_from_list,
    categorize_skills
)


class ProfileJobParser:
    """
    Agent 1: Parses resumes/profiles and job descriptions.
    Uses spaCy for NLP with NLTK fallback.
    """
    
    def __init__(self, output_dir: str = "data/json/parsed_profiles"):
        """
        Initialize the parser.
        
        Args:
            output_dir: Directory to save parsed profiles
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize NLP
        self.use_spacy = SPACY_AVAILABLE
        if self.use_spacy:
            self.nlp = nlp
        
        print(f"ProfileJobParser initialized (using {'spaCy' if self.use_spacy else 'NLTK'})")
    
    def parse_profile(self, profile_text: str, profile_id: Optional[str] = None) -> Dict:
        """
        Parse a resume/profile text and extract structured information.
        
        Args:
            profile_text: Raw resume text
            profile_id: Optional profile identifier
            
        Returns:
            Dictionary with parsed profile data
        """
        if not profile_text:
            return self._empty_profile()
        
        # Generate profile ID if not provided
        if not profile_id:
            profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Clean text
        cleaned_text = clean_text(profile_text)
        
        # Extract basic information
        email = extract_email(profile_text)
        phone = extract_phone(profile_text)
        
        # Extract skills
        skills = self._extract_skills_from_profile(profile_text)
        
        # Extract experience
        experience_years = self._extract_experience(profile_text)
        
        # Extract education
        education = self._extract_education(profile_text)
        
        # Extract job titles
        job_titles = self._extract_job_titles(profile_text)
        
        # Determine seniority level
        seniority = self._determine_seniority(experience_years, job_titles)
        
        # Extract summary/objective
        summary = self._extract_summary(profile_text)
        
        # Build profile dictionary
        profile = {
            'profile_id': profile_id,
            'raw_text': profile_text[:500],  # Store first 500 chars
            'cleaned_text': cleaned_text[:500],
            'contact': {
                'email': email,
                'phone': phone
            },
            'skills': skills,
            'experience_years': experience_years,
            'education': education,
            'job_titles': job_titles,
            'seniority': seniority,
            'summary': summary,
            'parsed_at': datetime.now().isoformat(),
            'parser_version': 'v1.0',
            'nlp_engine': 'spacy' if self.use_spacy else 'nltk'
        }
        
        # Save to file
        self._save_parsed_profile(profile, profile_id)
        
        return profile
    
    def parse_job(self, job_data: Dict) -> Dict:
        """
        Parse a job description and extract structured information.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Dictionary with parsed job data
        """
        # Extract fields
        job_id = job_data.get('Job Id', '')
        job_title = job_data.get('Job Title', '')
        experience_range = job_data.get('Experience', '')
        qualifications = job_data.get('Qualifications', '')
        skills_str = job_data.get('skills', '')
        role_category = job_data.get('Role Category', '')
        location = job_data.get('Location', '')
        
        # Parse skills (pipe-separated)
        if skills_str:
            skills = extract_skills_from_list(skills_str, delimiter='|')
        else:
            # Fallback: extract from qualifications
            skills = extract_skills(qualifications)
        
        # Parse experience range (e.g., "5 - 10 yrs")
        min_exp, max_exp = self._parse_experience_range(experience_range)
        
        # Clean job description
        cleaned_qualifications = clean_text(qualifications)
        
        # Build job dictionary
        job = {
            'job_id': str(job_id),
            'job_title': job_title,
            'role_category': role_category,
            'location': location,
            'experience': {
                'min_years': min_exp,
                'max_years': max_exp,
                'range_text': experience_range
            },
            'skills': skills,
            'qualifications': cleaned_qualifications,
            'parsed_at': datetime.now().isoformat()
        }
        
        return job
    
    def _extract_skills_from_profile(self, text: str) -> List[str]:
        """Extract skills from profile text."""
        # Try to find skills section first
        skills_section = extract_section(text, 'skills')
        
        if skills_section:
            skills = extract_skills(skills_section)
        else:
            # Extract from full text
            skills = extract_skills(text)
        
        return skills
    
    def _extract_experience(self, text: str) -> int:
        """Extract years of experience from profile."""
        # Try experience section first
        exp_section = extract_section(text, 'experience')
        
        if exp_section:
            years = extract_years_of_experience(exp_section)
        else:
            years = extract_years_of_experience(text)
        
        # If not found, try to count job positions
        if years == 0:
            years = self._estimate_experience_from_positions(text)
        
        return years
    
    def _estimate_experience_from_positions(self, text: str) -> int:
        """Estimate experience by counting years in job positions."""
        # Look for date ranges (e.g., "2018-2020", "Jan 2018 - Dec 2020")
        date_patterns = [
            r'(\d{4})\s*-\s*(\d{4})',
            r'(\d{4})\s*–\s*(\d{4})',
            r'(\d{4})\s*to\s*(\d{4})',
        ]
        
        total_years = 0
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                start_year = int(match[0])
                end_year = int(match[1])
                total_years += max(0, end_year - start_year)
        
        return min(total_years, 50)  # Cap at 50 years
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education information."""
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'\b(ph\.?d\.?|doctorate)\b',
            r'\b(master|m\.?s\.?|m\.?a\.?|mba)\b',
            r'\b(bachelor|b\.?s\.?|b\.?a\.?|b\.?tech|b\.?e\.?)\b',
            r'\b(associate|a\.?s\.?|a\.?a\.?)\b',
            r'\b(diploma|certificate)\b',
        ]
        
        text_lower = text.lower()
        for pattern in degree_patterns:
            if re.search(pattern, text_lower):
                matches = re.findall(pattern, text_lower)
                education.extend(matches)
        
        # Remove duplicates and normalize
        education = list(set([self._normalize_degree(d) for d in education]))
        
        return education
    
    def _normalize_degree(self, degree: str) -> str:
        """Normalize degree names."""
        degree = degree.lower().strip()
        
        normalizations = {
            'ph.d': 'PhD',
            'phd': 'PhD',
            'doctorate': 'PhD',
            'master': "Master's",
            'm.s': "Master's",
            'ms': "Master's",
            'm.a': "Master's",
            'ma': "Master's",
            'mba': 'MBA',
            'bachelor': "Bachelor's",
            'b.s': "Bachelor's",
            'bs': "Bachelor's",
            'b.a': "Bachelor's",
            'ba': "Bachelor's",
            'b.tech': "Bachelor's",
            'btech': "Bachelor's",
            'b.e': "Bachelor's",
            'be': "Bachelor's",
        }
        
        return normalizations.get(degree, degree.title())
    
    def _extract_job_titles(self, text: str) -> List[str]:
        """Extract job titles from profile."""
        job_titles = []
        
        # Common title patterns
        title_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'scientist', 'architect',
            'consultant', 'specialist', 'lead', 'senior', 'junior', 'director',
            'designer', 'administrator', 'coordinator', 'associate', 'executive'
        ]
        
        # Use spaCy if available
        if self.use_spacy:
            doc = self.nlp(text[:5000])  # Limit text length
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    continue
                # Check if entity contains title keywords
                for keyword in title_keywords:
                    if keyword in ent.text.lower():
                        job_titles.append(ent.text)
                        break
        else:
            # NLTK fallback: look for capitalized phrases with title keywords
            sentences = sent_tokenize(text)
            for sent in sentences[:20]:  # Check first 20 sentences
                for keyword in title_keywords:
                    if keyword in sent.lower():
                        # Extract capitalized phrases
                        matches = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', sent)
                        job_titles.extend(matches)
        
        # Remove duplicates
        job_titles = list(set(job_titles))[:5]  # Keep top 5
        
        return job_titles
    
    def _determine_seniority(self, experience_years: int, job_titles: List[str]) -> str:
        """Determine seniority level based on experience and titles."""
        # Check titles for seniority keywords
        title_text = ' '.join(job_titles).lower()
        
        if 'senior' in title_text or 'lead' in title_text or 'principal' in title_text:
            return 'senior'
        elif 'junior' in title_text or 'associate' in title_text:
            return 'junior'
        elif 'director' in title_text or 'vp' in title_text or 'head' in title_text:
            return 'executive'
        
        # Determine by experience years
        if experience_years >= 10:
            return 'senior'
        elif experience_years >= 5:
            return 'mid-level'
        elif experience_years >= 2:
            return 'junior'
        else:
            return 'entry-level'
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or objective."""
        summary_section = extract_section(text, 'summary')
        
        if summary_section:
            # Take first 200 characters
            return normalize_whitespace(summary_section[:200])
        
        # Fallback: take first few sentences
        sentences = sent_tokenize(text)
        if sentences:
            return normalize_whitespace(' '.join(sentences[:2])[:200])
        
        return ""
    
    def _parse_experience_range(self, exp_range: str) -> tuple:
        """
        Parse experience range string (e.g., "5 - 10 yrs").
        
        Returns:
            Tuple of (min_years, max_years)
        """
        if not exp_range:
            return (0, 0)
        
        # Pattern: "X - Y yrs" or "X to Y years"
        pattern = r'(\d+)\s*[-–to]+\s*(\d+)'
        match = re.search(pattern, exp_range)
        
        if match:
            return (int(match.group(1)), int(match.group(2)))
        
        # Single number pattern: "5 yrs"
        pattern = r'(\d+)'
        match = re.search(pattern, exp_range)
        if match:
            years = int(match.group(1))
            return (years, years)
        
        return (0, 0)
    
    def _save_parsed_profile(self, profile: Dict, profile_id: str):
        """Save parsed profile to JSON file."""
        output_path = self.output_dir / f"{profile_id}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        print(f"Saved parsed profile to: {output_path}")
    
    def _empty_profile(self) -> Dict:
        """Return empty profile structure."""
        return {
            'profile_id': '',
            'raw_text': '',
            'cleaned_text': '',
            'contact': {'email': '', 'phone': ''},
            'skills': [],
            'experience_years': 0,
            'education': [],
            'job_titles': [],
            'seniority': 'unknown',
            'summary': '',
            'parsed_at': datetime.now().isoformat(),
            'parser_version': 'v1.0'
        }


# Test function
if __name__ == "__main__":
    # Test the parser
    parser = ProfileJobParser()
    
    # Test profile parsing
    sample_profile = """
    John Doe
    Email: john.doe@example.com
    Phone: +1-555-123-4567
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 8 years of experience in full-stack development.
    
    SKILLS
    Python, Java, JavaScript, React, Node.js, SQL, AWS, Docker, Kubernetes
    
    EXPERIENCE
    Senior Software Engineer - Tech Corp (2018-2023)
    - Led development of microservices architecture
    - Managed team of 5 developers
    
    Software Engineer - StartupXYZ (2015-2018)
    - Developed web applications using React and Node.js
    
    EDUCATION
    Bachelor of Science in Computer Science - MIT (2015)
    """
    
    print("Testing profile parsing...")
    parsed_profile = parser.parse_profile(sample_profile, "test_profile_001")
    print(json.dumps(parsed_profile, indent=2))
    
    # Test job parsing
    sample_job = {
        'Job Id': '12345',
        'Job Title': 'Senior Python Developer',
        'Experience': '5 - 8 yrs',
        'Qualifications': 'Strong Python skills, experience with Django/Flask, AWS knowledge required',
        'skills': 'python|django|flask|aws|sql|docker',
        'Role Category': 'Software Development',
        'Location': 'San Francisco, CA'
    }
    
    print("\nTesting job parsing...")
    parsed_job = parser.parse_job(sample_job)
    print(json.dumps(parsed_job, indent=2))
