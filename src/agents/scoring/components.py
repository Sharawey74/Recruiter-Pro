"""
The scoring components that depend on nothing.

Experience, title, education and keyword scoring, plus the two qualification
flags, are pure functions of `(cv, job)`. They read no configuration, no
vocabulary and no model -- they were methods only because everything in Agent 3
was a method. Moved here verbatim, minus `self`.

Each returns a float in [0, 1]. The caller applies the weights; nothing here
knows what it is worth.

Two things deliberately left alone in the move, so that "this refactor changed
no score" stays checkable by diffing `scripts/score_probe.py` output:

* `role_keywords` in `score_title_similarity` is still a function-local literal
  rebuilt on every call -- once per job per upload. Hoisting it is backlog 3.2.
* `is_overqualified` takes an `exp_score` it never reads, and `is_underqualified`
  takes a `cv` and `job` it never reads. Both signatures are preserved as they
  were; tightening them is a separate change with its own diff.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List

from ...storage.models import CVProfile, JobPosting


def score_experience(cv: CVProfile, job: JobPosting) -> float:
    """Score experience match with tighter ranges and precision (0-1)"""
    if job.min_experience_years is None or cv.experience_years is None:
        return 0.6  # Reduced neutral score for missing data

    required_min = job.min_experience_years
    required_max = job.max_experience_years or (required_min + 3)
    actual = cv.experience_years

    # Perfect match within required range
    if required_min <= actual <= required_max:
        return 1.0

    # Slightly below minimum (1-2 years gap) - acceptable for growth
    if required_min - 2 <= actual < required_min:
        gap = required_min - actual
        return max(0.75, 1.0 - (gap * 0.1))  # 10% penalty per year

    # Significantly below minimum - underqualified
    if actual < required_min - 2:
        return max(0.2, (actual / required_min) * 0.6)

    # Slightly above maximum (1-2 years) - still acceptable
    if required_max < actual <= required_max + 2:
        excess = actual - required_max
        return max(0.85, 1.0 - (excess * 0.075))

    # Significantly overqualified - risk of job hopping or boredom
    if actual > required_max + 2:
        excess = actual - required_max
        penalty = min(0.5, excess * 0.08)  # 8% penalty per year excess, max 50%
        return max(0.3, 1.0 - penalty)

    return 0.6


def score_title_similarity(cv: CVProfile, job: JobPosting) -> float:
    """Score similarity between CV experience/title and job title for better role matching"""
    if not cv.extracted_data:
        return 0.4  # Low score if no data

    # Extract candidate's role/title from CV
    cv_roles = []
    if "title" in cv.extracted_data:
        cv_roles.append(cv.extracted_data["title"].lower())
    if "current_role" in cv.extracted_data:
        cv_roles.append(cv.extracted_data["current_role"].lower())

    # Use CV text as fallback
    if not cv_roles and cv.raw_text:
        # Try to extract role from common patterns
        role_patterns = [
            r"(software|web|mobile|backend|frontend|full[ -]?stack|data|ml|ai|devops|security|cloud)\s+(engineer|developer|architect|analyst)",
            r"(junior|senior|lead|principal)\s+(engineer|developer|programmer)",
            r"(intern|trainee|student).*?(engineer|developer|programmer)",
        ]
        for pattern in role_patterns:
            match = re.search(pattern, cv.raw_text.lower())
            if match:
                cv_roles.append(match.group(0))
                break

    if not cv_roles:
        return 0.4  # No role information found

    job_title = job.title.lower()

    # Role synonyms and related terms
    role_keywords = {
        "developer": ["engineer", "programmer", "coder", "dev", "software"],
        "engineer": ["developer", "architect", "programmer", "software"],
        "analyst": ["researcher", "data scientist", "scientist", "specialist"],
        "manager": ["lead", "director", "head", "supervisor", "coordinator"],
        "intern": ["trainee", "junior", "graduate", "student", "entry"],
        "senior": ["sr", "lead", "principal", "expert"],
        "junior": ["jr", "entry", "associate", "trainee"],
        "full stack": ["fullstack", "full-stack", "full stack developer"],
        "backend": ["back-end", "back end", "server side"],
        "frontend": ["front-end", "front end", "client side", "ui"],
        "data": ["data science", "analytics", "business intelligence"],
        "ai": ["artificial intelligence", "machine learning", "ml", "deep learning"],
        "devops": ["devsecops", "sre", "site reliability", "infrastructure"],
        "security": ["cyber", "infosec", "penetration", "ethical hacker"],
        "marketing": ["digital marketing", "growth", "brand", "content"],
    }

    # Check for direct matches
    for cv_role in cv_roles:
        # Exact match
        if cv_role in job_title or job_title in cv_role:
            return 1.0

        # Check if key terms match
        job_terms = set(job_title.split())
        cv_terms = set(cv_role.split())

        # Strong overlap
        overlap = job_terms.intersection(cv_terms)
        if len(overlap) >= 2:
            return 0.95

        # Check synonyms
        for key, synonyms in role_keywords.items():
            key_in_job = key in job_title or any(syn in job_title for syn in synonyms)
            key_in_cv = key in cv_role or any(syn in cv_role for syn in synonyms)

            if key_in_job and key_in_cv:
                return 0.85

    # Check if seniority level matches
    seniority_levels = [
        "intern",
        "junior",
        "mid",
        "senior",
        "lead",
        "principal",
        "staff",
        "manager",
        "director",
    ]
    for level in seniority_levels:
        if level in job_title:
            for cv_role in cv_roles:
                if level in cv_role:
                    return 0.7  # Seniority match even if role differs

    # Check if general domain matches (engineering, data, marketing, etc.)
    domains = ["engineering", "developer", "data", "marketing", "sales", "design", "product"]
    for domain in domains:
        domain_in_job = domain in job_title
        domain_in_cv = any(domain in cv_role for cv_role in cv_roles)
        if domain_in_job and domain_in_cv:
            return 0.5  # Same domain, different specific role

    return 0.3  # Low score if no title match


def score_education(cv: CVProfile, job: JobPosting) -> float:
    """Score education level match (0-1)"""
    education_levels = {
        "high school": 1,
        "diploma": 2,
        "associate": 3,
        "bachelor": 4,
        "bachelor's": 4,
        "master": 5,
        "master's": 5,
        "phd": 6,
        "doctorate": 6,
    }

    cv_edu = (cv.education or "").lower()
    job_edu = (job.education_level or "").lower()

    # Find education level
    cv_level = next((v for k, v in education_levels.items() if k in cv_edu), 3)
    job_level = next((v for k, v in education_levels.items() if k in job_edu), 3)

    # Match or exceed required
    if cv_level >= job_level:
        return 1.0

    # Below required (linear penalty)
    return max(0.3, cv_level / job_level)


def score_keywords(cv: CVProfile, job: JobPosting) -> float:
    """Score keyword presence in CV text (0-1)"""
    if not cv.raw_text or not job.description:
        return 0.5  # Neutral if data missing

    cv_text = cv.raw_text.lower()
    job_desc = job.description.lower()

    # Extract key terms from job description
    keywords = extract_keywords(job_desc)

    if not keywords:
        return 0.5

    # Count matches
    matches = sum(1 for kw in keywords if kw in cv_text)

    return min(1.0, matches / len(keywords))


def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from job description"""
    # Remove common words
    stopwords = {"the", "and", "or", "with", "for", "in", "on", "at", "to", "of", "a", "an"}

    # Extract words (3+ characters)
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())

    # Rank by frequency, then alphabetically to break ties.
    #
    # This previously did `[w for w in set(words) ...][:20]`, slicing 20
    # items out of a set. Python randomizes string hashing per process, so
    # set iteration order changed on every restart and the same CV/job pair
    # scored differently after a server restart - measured at 0.40 vs 0.45
    # across five runs of identical input. That violates the determinism
    # rule for Agent 3 in ADR-1, and it silently reorders near-ties in the
    # returned top-K.
    #
    # Frequency ranking is also more useful than hash order: a term the job
    # description repeats is more likely to matter than one it mentions once.
    counts = Counter(w for w in words if w not in stopwords)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    return [w for w, _ in ranked[:20]]  # Top 20 keywords


def is_overqualified(cv: CVProfile, job: JobPosting, exp_score: float) -> bool:
    """Check if candidate is overqualified"""
    if job.min_experience_years is None or cv.experience_years is None:
        return False

    # Significantly more experience than required
    multiplier = 2.0  # Default overqualification multiplier
    return cv.experience_years > (job.min_experience_years * multiplier)


def is_underqualified(cv: CVProfile, job: JobPosting, skill_ratio: float) -> bool:
    """Check if candidate is underqualified"""
    # Missing too many critical skills
    return skill_ratio < 0.4
