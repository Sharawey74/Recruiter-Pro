"""
Agent 2: Candidate Data Extractor
Pure rule-based extraction using regex, pattern matching, and dictionary lookup
Maximized efficiency with comprehensive skill database and intelligent parsing
"""
import re
import logging
from typing import Dict, List, Optional, Set
from pathlib import Path

class CandidateExtractor:
    """
    Deterministic Candidate Extractor - Agent 2
    Extraction Priority: Explicit Headers > Regex Patterns > Heuristics
    100% reproducible, no ML/AI dependencies
    """
    
    # Comprehensive address blocklist
    ADDRESS_TOKENS = {
        'street', 'st', 'road', 'rd', 'avenue', 'ave', 'city', 'town',
        'sheikh', 'zayed', 'district', 'governorate', 'postal', 'zip',
        'apartment', 'apt', 'building', 'floor', 'block', 'suite',
        'cairo', 'giza', 'alex', 'alexandria', 'maadi', 'nasr', 'new',
        'downtown', 'heliopolis', 'mohandessin', 'dokki', 'zamalek'
    }
    
    # Name header blocklist
    NAME_BLOCKLIST = {
        'curriculum', 'vitae', 'resume', 'cv', 'profile', 'contact',
        'information', 'details', 'personal', 'data', 'document'
    }
    
    # Comprehensive technical skills database (100+ skills)
    SKILLS_DATABASE = {
        # Programming Languages
        'python', 'java', 'javascript', 'js', 'typescript', 'ts', 'c++', 'cpp',
        'c#', 'csharp', 'ruby', 'php', 'swift', 'kotlin', 'go', 'golang', 'rust',
        'scala', 'r', 'perl', 'shell', 'bash', 'powershell', 'vba',
        
        # Web Frontend
        'html', 'html5', 'css', 'css3', 'sass', 'scss', 'less', 'react', 'reactjs',
        'angular', 'angularjs', 'vue', 'vuejs', 'svelte', 'jquery', 'bootstrap',
        'tailwind', 'webpack', 'vite', 'nextjs', 'gatsby', 'redux', 'mobx',
        
        # Web Backend
        'nodejs', 'node.js', 'node', 'express', 'expressjs', 'django', 'flask',
        'fastapi', 'spring', 'springboot', 'asp.net', 'laravel', 'rails', 'nestjs',
        
        # Databases
        'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'mongo', 'redis',
        'oracle', 'sqlite', 'dynamodb', 'cassandra', 'couchdb', 'elasticsearch',
        'neo4j', 'mariadb', 'mssql', 'sqlserver', 'firebase',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
        'jenkins', 'terraform', 'ansible', 'git', 'github', 'gitlab', 'bitbucket',
        'linux', 'unix', 'ubuntu', 'centos', 'debian', 'ci/cd', 'cicd',
        
        # Data Science & ML
        'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'tensorflow',
        'pytorch', 'keras', 'scikit-learn', 'sklearn', 'machine learning', 'ml',
        'deep learning', 'ai', 'artificial intelligence', 'data science',
        'big data', 'hadoop', 'spark', 'pyspark', 'airflow', 'kafka',
        
        # Mobile
        'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
        
        # Testing & Quality
        'selenium', 'pytest', 'junit', 'jest', 'mocha', 'chai', 'cypress',
        'testing', 'unit testing', 'integration testing', 'tdd', 'bdd',
        
        # Design & Tools
        'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd', 'indesign',
        'ui/ux', 'ui', 'ux', 'design', 'graphic design', 'web design',
        
        # Soft Skills
        'communication', 'leadership', 'management', 'teamwork', 'collaboration',
        'problem solving', 'analytical', 'critical thinking', 'agile', 'scrum',
        'project management', 'time management', 'presentation',
        
        # Other Technical
        'rest', 'restful', 'api', 'graphql', 'soap', 'microservices',
        'websocket', 'json', 'xml', 'yaml', 'oauth', 'jwt', 'saml'
    }
    
    # Skill synonyms for normalization
    SKILL_SYNONYMS = {
        'js': 'javascript',
        'ts': 'typescript',
        'nodejs': 'node.js',
        'node': 'node.js',
        'reactjs': 'react',
        'vuejs': 'vue',
        'angularjs': 'angular',
        'mongo': 'mongodb',
        'postgres': 'postgresql',
        'k8s': 'kubernetes',
        'sklearn': 'scikit-learn',
        'cpp': 'c++',
        'csharp': 'c#',
        'golang': 'go'
    }
    
    def __init__(self):
        self.logger = logging.getLogger("Agent2_Extractor")
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    def extract(self, text: str) -> Dict:
        """
        Main extraction pipeline - fully deterministic
        
        Args:
            text: Raw CV text from Agent 1
            
        Returns:
            Structured candidate profile
        """
        if not text or len(text.strip()) < 10:
            self.logger.warning("Empty or too short text provided")
            return self._empty_profile()
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Extract all fields
        name = self._extract_name(lines, text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        address = self._extract_address(lines)
        skills = self._extract_skills(text)
        experience_years = self._extract_experience(text)
        education = self._extract_education(text)
        
        profile = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "extraction_confidence": self._calculate_confidence(name, email, skills)
        }
        
        self.logger.info(f"Extracted: {name} | {len(skills)} skills | {experience_years}yr exp")
        return profile
    
    def _extract_name(self, lines: List[str], full_text: str) -> str:
        """
        Rule 1: Explicit headers (Candidate:, Name:, Full Name:)
        Rule 2: First valid capitalized line (not address)
        Rule 3: Fallback to Unknown
        """
        # Rule 1: Header patterns
        header_patterns = [
            r"^(?:Candidate|Name|Full\s*Name|Applicant)\s*[:\-]\s*(.+)",
            r"^(?:Resume\s*of|CV\s*of)\s*[:\-]?\s*(.+)"
        ]
        
        for line in lines[:20]:  # Check first 20 lines
            for pattern in header_patterns:
                if match := re.match(pattern, line, re.IGNORECASE):
                    name = match.group(1).strip()
                    if self._is_valid_name(name):
                        return name
        
        # Rule 2: Heuristic - First valid line
        for line in lines[:15]:
            if self._is_valid_name(line):
                words = line.split()
                # Verify not an address
                if not any(word.lower() in self.ADDRESS_TOKENS for word in words):
                    # Must be 2-5 words for a typical name
                    if 2 <= len(words) <= 5:
                        return line
        
        return "Unknown Candidate"
    
    def _is_valid_name(self, text: str) -> bool:
        """Validate if text looks like a person's name"""
        if not text or len(text) < 2:
            return False
        
        words = text.split()
        if len(words) < 2 or len(words) > 6:
            return False
        
        # Check alphabetic ratio
        alpha_chars = sum(c.isalpha() or c.isspace() for c in text)
        if alpha_chars / len(text) < 0.75:
            return False
        
        # Reject if contains blocklist words
        if any(word.lower() in self.NAME_BLOCKLIST for word in words):
            return False
        
        # At least one capitalized word
        if not any(word[0].isupper() for word in words if word):
            return False
        
        # Reject if looks like a title or position
        if any(kw in text.lower() for kw in ['engineer', 'developer', 'manager', 'director', 'analyst']):
            return False
        
        return True
    
    def _extract_email(self, text: str) -> str:
        """Extract email with comprehensive regex"""
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        match = re.search(pattern, text)
        return match.group(0) if match else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone - international and local formats"""
        patterns = [
            r"(?:\+|00)\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9}",  # International
            r"\d{3}[\s\-]?\d{3}[\s\-]?\d{4}",  # US format
            r"\d{4}[\s\-]?\d{3}[\s\-]?\d{3}",  # Some EU formats
            r"\(\d{3}\)\s*\d{3}[\s\-]?\d{4}"  # (xxx) xxx-xxxx
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, text):
                return match.group(0)
        
        return ""
    
    def _extract_address(self, lines: List[str]) -> str:
        """Extract address using multi-strategy approach"""
        # Strategy 1: Explicit header
        for i, line in enumerate(lines[:25]):
            if re.match(r"^(?:Address|Location|Residence)\s*[:\-]", line, re.IGNORECASE):
                if ':' in line:
                    addr = line.split(':', 1)[1].strip()
                    if addr:
                        return addr
                elif i + 1 < len(lines):
                    return lines[i + 1]
        
        # Strategy 2: Line with address indicators
        for line in lines[:25]:
            words_lower = [w.lower() for w in line.split()]
            address_score = sum(1 for w in words_lower if w in self.ADDRESS_TOKENS)
            
            # High confidence if multiple address tokens
            if address_score >= 2 and len(words_lower) >= 2:
                return line
        
        return ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """
        Multi-strategy skill extraction:
        1. Dictionary matching (exact)
        2. Fuzzy matching for common variations
        3. Multi-word skill detection
        """
        text_lower = text.lower()
        found_skills: Set[str] = set()
        
        # Tokenize
        tokens = re.findall(r"\b[\w\+\#\./-]+\b", text_lower)
        
        # Exact single-word matches
        for token in tokens:
            if token in self.SKILLS_DATABASE:
                # Normalize via synonyms
                normalized = self.SKILL_SYNONYMS.get(token, token)
                found_skills.add(normalized)
        
        # Multi-word skills (scan full text)
        for skill in self.SKILLS_DATABASE:
            if ' ' in skill or '/' in skill:
                if skill in text_lower:
                    found_skills.add(skill)
        
        # Handle compound skills (e.g., "node.js", "c++", "c#")
        special_patterns = [
            (r'\bnode\.?js\b', 'node.js'),
            (r'\bc\+\+\b', 'c++'),
            (r'\bc#\b', 'c#'),
            (r'\b\.net\b', 'asp.net'),
        ]
        
        for pattern, skill_name in special_patterns:
            if re.search(pattern, text_lower):
                found_skills.add(skill_name)
        
        return sorted(list(found_skills))
    
    def _extract_experience(self, text: str) -> int:
        """Extract years of experience using multiple patterns"""
        patterns = [
            # Standard patterns
            r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)",
            r"experience\s*[:\-]\s*(\d+)\s*(?:years?|yrs?)",
            r"(\d+)\s*(?:years?|yrs?)\s*in\s*\w+",
            r"total\s*[:\-]?\s*(\d+)\s*(?:years?|yrs?)",
            # Additional patterns for broken formatting
            r"(?:experience|exp)\D*(\d+)\D*(?:year|yr)",
            r"(\d+)\D*(?:year|yr)\D*(?:experience|exp)",
            # Date range patterns (2019-2024 = 5 years)
            r"(20\d{2})\s*[-–—]\s*(20\d{2}|present|current)",
        ]
        
        # Try explicit patterns first
        for pattern in patterns[:-1]:  # All except date range
            if match := re.search(pattern, text.lower()):
                years = int(match.group(1))
                if 0 < years <= 50:  # Sanity check
                    return years
        
        # Try extracting from date ranges
        date_matches = re.findall(patterns[-1], text.lower())
        if date_matches:
            total_years = 0
            for start_year, end_year in date_matches:
                start = int(start_year)
                if 'present' in end_year or 'current' in end_year:
                    end = 2024  # Current year
                else:
                    end = int(end_year)
                total_years += max(0, end - start)
            if total_years > 0:
                return min(total_years, 50)  # Cap at 50 years
        
        return 0
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education degrees"""
        degrees = []
        degree_patterns = [
            (r"\b(?:B\.?S\.?|Bachelor'?s?|B\.?A\.?|B\.?Sc\.?)\b", "Bachelor's"),
            (r"\b(?:M\.?S\.?|Master'?s?|M\.?A\.?|M\.?Sc\.?|MBA)\b", "Master's"),
            (r"\b(?:Ph\.?D\.?|Doctorate|Doctoral)\b", "PhD"),
            (r"\b(?:Associate'?s?|A\.?S\.?|A\.?A\.?)\b", "Associate's"),
        ]
        
        for pattern, degree_name in degree_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if degree_name not in degrees:
                    degrees.append(degree_name)
        
        return degrees
    
    def _calculate_confidence(self, name: str, email: str, skills: List[str]) -> float:
        """Calculate extraction confidence score"""
        score = 0.0
        
        if name and name != "Unknown Candidate":
            score += 0.3
        if email:
            score += 0.3
        if skills:
            score += 0.4 * min(len(skills) / 5.0, 1.0)
        
        return round(score, 2)
    
    def _empty_profile(self) -> Dict:
        """Return empty profile structure"""
        return {
            "name": "Unknown Candidate",
            "email": "",
            "phone": "",
            "address": "",
            "skills": [],
            "experience_years": 0,
            "education": [],
            "extraction_confidence": 0.0
        }


# Singleton instance
extractor = CandidateExtractor()
