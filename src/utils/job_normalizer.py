"""
Job Data Normalizer - Maps jobs.json schema to expected application schema.
Handles multiple data formats and ensures consistent field names.
"""
from typing import Dict, List


def normalize_job(job_data: Dict) -> Dict:
    """
    Normalize a single job entry to standard schema.
    
    Maps from jobs.json format:
        - "Job Id" -> "job_id"
        - "Job Title" -> "job_title"
        - "skills" -> "skills_required" (parsed from pipe-separated string)
        - "Experience" -> "experience_required" (parsed into min/max years)
        - "Location" -> "location"
        - Infers "role_category" from job title
    
    Args:
        job_data: Raw job dictionary from jobs.json
        
    Returns:
        Normalized job dictionary with consistent field names
    """
    # Extract base fields
    job_id = job_data.get('Job Id', job_data.get('job_id', 'unknown'))
    job_title = job_data.get('Job Title', job_data.get('job_title', 'Unknown Position'))
    location = job_data.get('Location', job_data.get('location', 'Remote'))
    
    # Parse skills from pipe-separated string
    skills_raw = job_data.get('skills', job_data.get('skills_required', ''))
    if isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split('|') if s.strip()]
    elif isinstance(skills_raw, list):
        skills = skills_raw
    else:
        skills = []
    
    # Parse experience range
    experience_str = job_data.get('Experience', job_data.get('experience', '0 - 0 yrs'))
    min_exp, max_exp = parse_experience_range(experience_str)
    
    # Infer role category from job title (simple heuristic)
    role_category = infer_category_from_title(job_title)
    
    # Build normalized structure
    normalized = {
        'job_id': str(job_id),
        'job_title': job_title,
        'role_category': role_category,
        'skills_required': skills,
        'experience_required': {
            'min_years': min_exp,
            'max_years': max_exp
        },
        'location': location,
        'description': job_data.get('Qualifications', job_data.get('description', ''))
    }
    
    return normalized


def parse_experience_range(exp_str: str) -> tuple:
    """
    Parse experience string like "2 - 5 yrs" into (min, max) tuple.
    
    Args:
        exp_str: Experience string (e.g., "2 - 5 yrs", "12 - 17 Years")
        
    Returns:
        Tuple of (min_years, max_years)
    """
    import re
    
    # Common patterns: "2 - 5 yrs", "12 - 17 Years", "0 - 2 years"
    match = re.search(r'(\d+)\s*-\s*(\d+)', exp_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Single value: "5 years", "5+ yrs"
    match = re.search(r'(\d+)\+?', exp_str)
    if match:
        val = int(match.group(1))
        return val, val + 3  # Assume range of +3 years
    
    # Default fallback
    return 0, 5


def infer_category_from_title(title: str) -> str:
    """
    Infer role category from job title using keyword matching.
    
    Args:
        title: Job title string
        
    Returns:
        Category name (e.g., "Engineering", "Sales", "Design")
    """
    title_lower = title.lower()
    
    # Engineering & Technical
    if any(kw in title_lower for kw in ['engineer', 'developer', 'programmer', 'architect', 'devops', 'sre', 'backend', 'frontend', 'full stack', 'mean stack']):
        return 'Engineering'
    
    # Data & Analytics
    if any(kw in title_lower for kw in ['data', 'analyst', 'analytics', 'scientist', 'ml', 'ai', 'machine learning']):
        return 'Data & Analytics'
    
    # Design & Creative
    if any(kw in title_lower for kw in ['designer', 'artist', 'ux', 'ui', 'creative', 'graphic']):
        return 'Design'
    
    # Management & Leadership
    if any(kw in title_lower for kw in ['manager', 'director', 'lead', 'head', 'vp', 'cto', 'ceo', 'team lead']):
        return 'Management'
    
    # Sales & Marketing
    if any(kw in title_lower for kw in ['sales', 'marketing', 'business development', 'account', 'telesales', 'tele sales']):
        return 'Sales & Marketing'
    
    # Operations & Support
    if any(kw in title_lower for kw in ['operations', 'support', 'customer', 'helpdesk', 'service']):
        return 'Operations & Support'
    
    # Default category
    return 'General'


def normalize_jobs_list(jobs_list: List[Dict], limit: int = None) -> List[Dict]:
    """
    Normalize a list of jobs from jobs.json format.
    
    Args:
        jobs_list: List of raw job dictionaries
        limit: Optional limit on number of jobs to return
        
    Returns:
        List of normalized job dictionaries
    """
    normalized = [normalize_job(job) for job in jobs_list]
    
    if limit:
        normalized = normalized[:limit]
    
    return normalized
