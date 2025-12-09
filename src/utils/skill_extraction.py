"""
Skill extraction utilities for resume parsing.
"""
import re
from typing import List, Set

# Comprehensive skill database
TECHNICAL_SKILLS = {
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
    'go', 'rust', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash', 'powershell',
    
    # Web Technologies
    'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
    'spring', 'asp.net', 'jquery', 'bootstrap', 'tailwind', 'sass', 'webpack', 'next.js',
    
    # Databases
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'oracle', 'sqlite',
    'dynamodb', 'elasticsearch', 'neo4j', 'mariadb',
    
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github actions',
    'terraform', 'ansible', 'ci/cd', 'devops', 'linux', 'unix', 'nginx', 'apache',
    
    # Data Science & ML
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'keras',
    'pandas', 'numpy', 'matplotlib', 'seaborn', 'nlp', 'computer vision', 'data analysis',
    'data science', 'statistics', 'big data', 'hadoop', 'spark', 'tableau', 'power bi',
    
    # Mobile Development
    'android', 'ios', 'react native', 'flutter', 'xamarin', 'mobile development',
    
    # Other Technologies
    'git', 'api', 'rest', 'graphql', 'microservices', 'agile', 'scrum', 'jira',
    'testing', 'unit testing', 'selenium', 'jest', 'pytest', 'tdd', 'oop',
    'data structures', 'algorithms', 'system design', 'networking', 'security',
    'blockchain', 'iot', 'embedded systems',
}

# Soft skills
SOFT_SKILLS = {
    'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
    'time management', 'project management', 'analytical', 'creative', 'adaptable',
    'collaboration', 'presentation', 'negotiation', 'mentoring', 'strategic thinking',
}

# Domain-specific skills
DOMAIN_SKILLS = {
    'finance', 'healthcare', 'retail', 'e-commerce', 'marketing', 'sales', 'hr',
    'accounting', 'legal', 'education', 'manufacturing', 'logistics', 'supply chain',
}

ALL_SKILLS = TECHNICAL_SKILLS | SOFT_SKILLS | DOMAIN_SKILLS


def extract_skills(text: str, custom_skills: List[str] = None) -> List[str]:
    """
    Extract skills from text using pattern matching.
    
    Args:
        text: Text to extract skills from
        custom_skills: Additional skills to look for
        
    Returns:
        List of found skills
    """
    if not text:
        return []
    
    text_lower = text.lower()
    found_skills = set()
    
    # Combine default and custom skills
    skills_to_check = ALL_SKILLS.copy()
    if custom_skills:
        skills_to_check.update([s.lower() for s in custom_skills])
    
    # Check for each skill
    for skill in skills_to_check:
        # Use word boundaries for exact matches
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    
    # Also check for common variations
    variations = {
        'js': 'javascript',
        'ts': 'typescript',
        'k8s': 'kubernetes',
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
        'dl': 'deep learning',
        'cv': 'computer vision',
        'db': 'database',
    }
    
    for abbr, full_name in variations.items():
        if re.search(r'\b' + abbr + r'\b', text_lower):
            found_skills.add(full_name)
    
    return sorted(list(found_skills))


def extract_skills_from_list(text: str, delimiter: str = '|') -> List[str]:
    """
    Extract skills from a delimited list (e.g., "Python | Java | SQL").
    
    Args:
        text: Text containing delimited skills
        delimiter: Delimiter character
        
    Returns:
        List of skills
    """
    if not text:
        return []
    
    # Split by delimiter
    skills = [s.strip().lower() for s in text.split(delimiter)]
    
    # Filter out empty strings
    skills = [s for s in skills if s]
    
    return skills


def categorize_skills(skills: List[str]) -> dict:
    """
    Categorize skills into technical, soft, and domain categories.
    
    Args:
        skills: List of skills
        
    Returns:
        Dictionary with categorized skills
    """
    categorized = {
        'technical': [],
        'soft': [],
        'domain': [],
        'other': []
    }
    
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in TECHNICAL_SKILLS:
            categorized['technical'].append(skill)
        elif skill_lower in SOFT_SKILLS:
            categorized['soft'].append(skill)
        elif skill_lower in DOMAIN_SKILLS:
            categorized['domain'].append(skill)
        else:
            categorized['other'].append(skill)
    
    return categorized


def calculate_skill_match(profile_skills: List[str], job_skills: List[str]) -> dict:
    """
    Calculate skill matching metrics between profile and job.
    
    Args:
        profile_skills: Skills from candidate profile
        job_skills: Required skills from job
        
    Returns:
        Dictionary with matching metrics
    """
    profile_set = set([s.lower() for s in profile_skills])
    job_set = set([s.lower() for s in job_skills])
    
    matched = profile_set & job_set
    missing = job_set - profile_set
    extra = profile_set - job_set
    
    # Calculate Jaccard similarity
    union = profile_set | job_set
    jaccard = len(matched) / len(union) if union else 0.0
    
    # Calculate overlap ratio
    overlap_ratio = len(matched) / len(job_set) if job_set else 0.0
    
    return {
        'matched_skills': sorted(list(matched)),
        'missing_skills': sorted(list(missing)),
        'extra_skills': sorted(list(extra)),
        'match_count': len(matched),
        'match_ratio': overlap_ratio,
        'jaccard_similarity': jaccard,
    }


def extract_skill_level(text: str, skill: str) -> str:
    """
    Try to extract proficiency level for a skill.
    
    Args:
        text: Text containing skill information
        skill: Skill to check
        
    Returns:
        Proficiency level (beginner, intermediate, advanced, expert) or 'unknown'
    """
    if not text or not skill:
        return 'unknown'
    
    text_lower = text.lower()
    skill_lower = skill.lower()
    
    # Find skill context
    pattern = rf'{re.escape(skill_lower)}[^.]*?(?:beginner|intermediate|advanced|expert|proficient|skilled)'
    match = re.search(pattern, text_lower)
    
    if match:
        context = match.group(0)
        if 'expert' in context or 'advanced' in context:
            return 'advanced'
        elif 'intermediate' in context or 'proficient' in context:
            return 'intermediate'
        elif 'beginner' in context:
            return 'beginner'
    
    return 'unknown'


def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill name to standard format.
    
    Args:
        skill: Skill name
        
    Returns:
        Normalized skill name
    """
    # Common normalizations
    normalizations = {
        'js': 'javascript',
        'ts': 'typescript',
        'k8s': 'kubernetes',
        'aws': 'amazon web services',
        'gcp': 'google cloud platform',
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
        'dl': 'deep learning',
        'nlp': 'natural language processing',
        'cv': 'computer vision',
    }
    
    skill_lower = skill.lower().strip()
    return normalizations.get(skill_lower, skill_lower)
