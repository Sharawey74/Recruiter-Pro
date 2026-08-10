"""
Agent 3: Hybrid Scoring Agent
Combines rule-based scoring with ML predictions for robust matching

Architecture:
- Rule-based scoring: Skill matching, experience, education (60% weight)
- ML scoring: ATS engine predictions (40% weight)
- Hybrid score: Weighted combination of both approaches
"""
import json
import logging
from collections import Counter
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from ..storage.models import ScoreBreakdown, CVProfile, JobPosting
from ..core.config import get_config
from ..ml_engine.ats_predictor import ATSPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SkillMatch:
    """Skill matching results"""
    matched_skills: List[str]
    missing_skills: List[str]
    extra_skills: List[str]
    match_ratio: float


class HybridScoringAgent:
    """
    Agent 3: Hybrid Scorer
    
    Combines rule-based and ML approaches for robust scoring:
    1. Rule-based: Skills (60%), Experience (25%), Education (10%), Keywords (5%)
    2. ML-based: ATS Engine prediction (optional)
    3. Hybrid: Weighted combination based on configuration
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.scoring_config = self.config.scoring
        
        # Initialize ML predictor if enabled
        self.ml_predictor = None
        if self.scoring_config.ml_enabled:
            try:
                self.ml_predictor = ATSPredictor(model_dir="models/production")
                if self.ml_predictor.load_model():
                    logger.info("[OK] ML Predictor initialized for hybrid scoring")
                    model_info = self.ml_predictor.get_model_info()
                    logger.info(f"   Model: {model_info.get('model_name', 'Unknown')}")
                    logger.info(f"   Test Recall: {model_info.get('test_metrics', {}).get('recall', 'N/A')}")
                else:
                    logger.warning("[WARN] Failed to load ML model. Using rule-based only.")
                    self.ml_predictor = None
            except Exception as e:
                logger.warning(f"[WARN] ML Predictor unavailable: {e}. Using rule-based only.")
                self.ml_predictor = None
        
        # Load the skill vocabulary as a flat {alias_lower: Canonical} index.
        self.skills_database = self._load_skills_database()

    @staticmethod
    def _build_alias_index(raw: Dict) -> Dict[str, str]:
        """
        Flatten the family-nested vocabulary into {alias_lower: Canonical}.

        This is the fix for A0. The previous code iterated the raw file as if
        it were flat -- {canonical: [aliases]} -- but it is nested by family:

            {"programming_languages": {"Python": ["python", "py"], ...}, ...}

        so `for canonical, aliases in raw.items()` bound `canonical` to the
        *family name* and `aliases` to the inner dict. `[a.lower() for a in
        aliases]` then iterated that dict's keys, the membership test passed,
        and the function returned "programming_languages" for every language.
        Python and Java normalized to an identical string and matched
        perfectly. Skills are 50% of the rule-based score, so about a third of
        every reported score was noise, biased upward.

        Handles both layouts: the current one, which separates `_meta` from
        `families`, and the older one that mixed metadata keys in beside the
        families. The isinstance guard is what skips `comment` / `_meta` -- and
        its absence is what caused the original bug.
        """
        families = raw.get("families")
        if not isinstance(families, dict):
            # Legacy layout: families sit at the top level next to metadata.
            families = {k: v for k, v in raw.items() if isinstance(v, dict)}

        index: Dict[str, str] = {}
        for family, entries in families.items():
            if not isinstance(entries, dict):
                continue
            for canonical, aliases in entries.items():
                index[canonical.lower()] = canonical
                if not isinstance(aliases, (list, tuple)):
                    continue
                for alias in aliases:
                    index[str(alias).lower()] = canonical
        return index

    def _load_skills_database(self) -> Dict[str, str]:
        """Load the skill vocabulary and flatten it into an alias index."""
        skills_path = Path(self.config.skills_database_path)

        if not skills_path.exists():
            logger.warning(f"Skills database not found: {skills_path}")
            return {}

        try:
            with open(skills_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            index = self._build_alias_index(raw)
            logger.info(
                f"[OK] Skill vocabulary loaded: {len(set(index.values()))} canonical "
                f"skills, {len(index)} aliases"
            )
            return index
        except Exception as e:
            logger.error(f"Failed to load skills database: {e}", exc_info=True)
            return {}
    
    def score_match(
        self, 
        cv: CVProfile, 
        job: JobPosting,
        include_ml: bool = True
    ) -> ScoreBreakdown:
        """
        Score CV-Job match using hybrid approach
        
        Args:
            cv: Candidate CV profile
            job: Job posting requirements
            include_ml: Whether to include ML scoring
        
        Returns:
            ScoreBreakdown with all scoring components
        """
        # 1. Rule-based scoring
        skill_match = self._score_skills(cv, job)
        experience_score = self._score_experience(cv, job)
        education_score = self._score_education(cv, job)
        keyword_score = self._score_keywords(cv, job)
        title_score = self._score_title_similarity(cv, job)
        
        # Calculate weighted rule-based score with enhanced weights
        # Skills: 50%, Title: 17%, Experience: 20%, Education: 8%, Keywords: 5%
        rule_based_score = (
            skill_match.match_ratio * 0.50 +
            title_score * 0.17 +
            experience_score * 0.20 +
            education_score * 0.08 +
            keyword_score * 0.05
        )
        
        # 2. ML-based scoring (if enabled)
        ml_score = None
        ml_probability = None
        if include_ml and self.ml_predictor:
            ml_result = self._get_ml_score(cv, job)
            if ml_result:
                # Convert ml_score from 0-100 to 0-1 scale
                ml_score = ml_result['ml_score'] / 100.0 if ml_result['ml_score'] > 1 else ml_result['ml_score']
                ml_probability = ml_result['probability']
        
        # 3. Calculate hybrid score
        if ml_score is not None:
            hybrid_score = (
                rule_based_score * self.scoring_config.rule_weight +
                ml_score * self.scoring_config.ml_weight
            )
        else:
            hybrid_score = rule_based_score
        
        # 4. Detect over/under qualification
        overqualified = self._is_overqualified(cv, job, experience_score)
        underqualified = self._is_underqualified(cv, job, skill_match.match_ratio)
        
        # 5. Build score breakdown
        return ScoreBreakdown(
            skill_score=skill_match.match_ratio,
            experience_score=experience_score,
            education_score=education_score,
            keyword_score=keyword_score,
            rule_based_score=rule_based_score,
            ml_score=ml_score,
            hybrid_score=hybrid_score,
            matched_skills=skill_match.matched_skills,
            missing_skills=skill_match.missing_skills,
            extra_skills=skill_match.extra_skills,
            overqualified=overqualified,
            underqualified=underqualified
        )
    
    def _score_skills(self, cv: CVProfile, job: JobPosting) -> SkillMatch:
        """
        Score skill matching between CV and job with enhanced precision
        
        Uses fuzzy matching, synonym detection, and weighted scoring
        """
        cv_skills = set(self._normalize_skills(cv.skills))
        required_skills = set(self._normalize_skills(job.required_skills))
        preferred_skills = set(self._normalize_skills(job.preferred_skills))
        
        # Enhanced matching with fuzzy logic and synonyms
        matched_required = self._find_skill_matches(cv_skills, required_skills)
        matched_preferred = self._find_skill_matches(cv_skills, preferred_skills)
        matched_skills = list(set(matched_required + matched_preferred))
        
        # Find gaps
        missing_required = [s for s in required_skills if not self._has_skill_match(s, cv_skills)]
        missing_preferred = [s for s in preferred_skills if not self._has_skill_match(s, cv_skills)]
        
        # Extra skills candidate has
        extra_skills = list(cv_skills - required_skills - preferred_skills)
        
        # Calculate match ratio with enhanced precision
        total_required = len(required_skills) or 1
        total_preferred = len(preferred_skills) or 0
        
        # Weighted ratio: required skills are critical (85%), preferred are bonus (15%)
        required_match_ratio = len(matched_required) / total_required
        preferred_match_ratio = len(matched_preferred) / max(total_preferred, 1) if total_preferred > 0 else 0
        
        match_ratio = (required_match_ratio * 0.85) + (preferred_match_ratio * 0.15)
        
        # Penalty for missing critical required skills
        if len(missing_required) > len(required_skills) * 0.5:  # Missing more than 50%
            match_ratio *= 0.7  # 30% penalty
        
        return SkillMatch(
            matched_skills=matched_skills,
            missing_skills=missing_required + missing_preferred,
            extra_skills=extra_skills[:10],  # Limit to top 10
            match_ratio=min(1.0, match_ratio)
        )
    
    def _find_skill_matches(self, cv_skills: set, job_skills: set) -> List[str]:
        """Find skill matches with fuzzy matching and synonyms"""
        matches = []
        
        # Skill synonyms for better matching
        synonyms = {
            'javascript': ['js', 'es6', 'es2015', 'ecmascript'],
            'python': ['py', 'python3', 'python2'],
            'java': ['jdk', 'jre', 'java8', 'java11', 'java17'],
            'csharp': ['c#', 'cs', 'dotnet', '.net', 'net', 'asp.net', 'aspnet'],
            'cpp': ['c++', 'cplusplus'],
            'sql': ['mysql', 'postgresql', 'mssql', 'tsql', 'plsql', 'ms sql', 'microsoft sql'],
            'react': ['reactjs', 'react.js'],
            'angular': ['angularjs', 'angular.js'],
            'vue': ['vuejs', 'vue.js'],
            'node': ['nodejs', 'node.js'],
            'docker': ['containerization', 'containers'],
            'kubernetes': ['k8s'],
            'aws': ['amazon web services', 'amazon cloud'],
            'gcp': ['google cloud', 'google cloud platform'],
            'azure': ['microsoft azure', 'azure cloud'],
            'machine learning': ['ml', 'machinelearning'],
            'deep learning': ['dl', 'deeplearning', 'neural networks'],
            'artificial intelligence': ['ai'],
            'devops': ['dev ops', 'devsecops'],
            'cicd': ['ci/cd', 'ci-cd', 'continuous integration', 'continuous deployment'],
            'api': ['rest api', 'restful', 'rest', 'graphql'],
            'html': ['html5'],
            'css': ['css3', 'scss', 'sass'],
            'typescript': ['ts'],
            'mongodb': ['mongo'],
            'postgresql': ['postgres'],
            'jenkins': ['ci'],
            'git': ['github', 'gitlab', 'version control'],
            'agile': ['scrum', 'kanban'],
            'flask': ['python flask'],
            'fastapi': ['fast api'],
            'django': ['python django'],
            'spring': ['spring boot', 'springboot'],
            'llm': ['large language model', 'gpt', 'generative ai', 'genai'],
            'nlp': ['natural language processing', 'text processing'],
            'rag': ['retrieval augmented generation'],
            'langchain': ['lang chain'],
            'tensorflow': ['tf'],
            'pytorch': ['torch'],
            'scikit': ['sklearn', 'scikit-learn'],
        }
        
        for job_skill in job_skills:
            # Direct match
            if job_skill in cv_skills:
                matches.append(job_skill)
                continue
            
            # Check synonyms
            matched = False
            for canonical, aliases in synonyms.items():
                if job_skill in aliases or job_skill == canonical:
                    # Check if CV has canonical or any alias
                    if canonical in cv_skills or any(alias in cv_skills for alias in aliases):
                        matches.append(job_skill)
                        matched = True
                        break
            
            if matched:
                continue
            
            # Fuzzy partial match (e.g., "python" matches "python3")
            for cv_skill in cv_skills:
                if len(job_skill) >= 4 and (job_skill in cv_skill or cv_skill in job_skill):
                    matches.append(job_skill)
                    break
        
        return matches
    
    def _has_skill_match(self, skill: str, cv_skills: set) -> bool:
        """Check if a skill has a match in CV skills"""
        return len(self._find_skill_matches(cv_skills, {skill})) > 0
    
    def _score_experience(self, cv: CVProfile, job: JobPosting) -> float:
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
    
    def _score_title_similarity(self, cv: CVProfile, job: JobPosting) -> float:
        """Score similarity between CV experience/title and job title for better role matching"""
        if not cv.extracted_data:
            return 0.4  # Low score if no data
        
        # Extract candidate's role/title from CV
        cv_roles = []
        if 'title' in cv.extracted_data:
            cv_roles.append(cv.extracted_data['title'].lower())
        if 'current_role' in cv.extracted_data:
            cv_roles.append(cv.extracted_data['current_role'].lower())
        
        # Use CV text as fallback
        if not cv_roles and cv.raw_text:
            # Try to extract role from common patterns
            import re
            role_patterns = [
                r'(software|web|mobile|backend|frontend|full[ -]?stack|data|ml|ai|devops|security|cloud)\s+(engineer|developer|architect|analyst)',
                r'(junior|senior|lead|principal)\s+(engineer|developer|programmer)',
                r'(intern|trainee|student).*?(engineer|developer|programmer)',
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
            'developer': ['engineer', 'programmer', 'coder', 'dev', 'software'],
            'engineer': ['developer', 'architect', 'programmer', 'software'],
            'analyst': ['researcher', 'data scientist', 'scientist', 'specialist'],
            'manager': ['lead', 'director', 'head', 'supervisor', 'coordinator'],
            'intern': ['trainee', 'junior', 'graduate', 'student', 'entry'],
            'senior': ['sr', 'lead', 'principal', 'expert'],
            'junior': ['jr', 'entry', 'associate', 'trainee'],
            'full stack': ['fullstack', 'full-stack', 'full stack developer'],
            'backend': ['back-end', 'back end', 'server side'],
            'frontend': ['front-end', 'front end', 'client side', 'ui'],
            'data': ['data science', 'analytics', 'business intelligence'],
            'ai': ['artificial intelligence', 'machine learning', 'ml', 'deep learning'],
            'devops': ['devsecops', 'sre', 'site reliability', 'infrastructure'],
            'security': ['cyber', 'infosec', 'penetration', 'ethical hacker'],
            'marketing': ['digital marketing', 'growth', 'brand', 'content'],
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
        seniority_levels = ['intern', 'junior', 'mid', 'senior', 'lead', 'principal', 'staff', 'manager', 'director']
        for level in seniority_levels:
            if level in job_title:
                for cv_role in cv_roles:
                    if level in cv_role:
                        return 0.7  # Seniority match even if role differs
        
        # Check if general domain matches (engineering, data, marketing, etc.)
        domains = ['engineering', 'developer', 'data', 'marketing', 'sales', 'design', 'product']
        for domain in domains:
            domain_in_job = domain in job_title
            domain_in_cv = any(domain in cv_role for cv_role in cv_roles)
            if domain_in_job and domain_in_cv:
                return 0.5  # Same domain, different specific role
        
        return 0.3  # Low score if no title match
    
    def _score_education(self, cv: CVProfile, job: JobPosting) -> float:
        """Score education level match (0-1)"""
        education_levels = {
            'high school': 1,
            'diploma': 2,
            'associate': 3,
            'bachelor': 4,
            "bachelor's": 4,
            'master': 5,
            "master's": 5,
            'phd': 6,
            'doctorate': 6
        }
        
        cv_edu = (cv.education or '').lower()
        job_edu = (job.education_level or '').lower()
        
        # Find education level
        cv_level = next((v for k, v in education_levels.items() if k in cv_edu), 3)
        job_level = next((v for k, v in education_levels.items() if k in job_edu), 3)
        
        # Match or exceed required
        if cv_level >= job_level:
            return 1.0
        
        # Below required (linear penalty)
        return max(0.3, cv_level / job_level)
    
    def _score_keywords(self, cv: CVProfile, job: JobPosting) -> float:
        """Score keyword presence in CV text (0-1)"""
        if not cv.raw_text or not job.description:
            return 0.5  # Neutral if data missing
        
        cv_text = cv.raw_text.lower()
        job_desc = job.description.lower()
        
        # Extract key terms from job description
        keywords = self._extract_keywords(job_desc)
        
        if not keywords:
            return 0.5
        
        # Count matches
        matches = sum(1 for kw in keywords if kw in cv_text)
        
        return min(1.0, matches / len(keywords))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from job description"""
        # Simple approach: extract common technical terms
        import re
        
        # Remove common words
        stopwords = {'the', 'and', 'or', 'with', 'for', 'in', 'on', 'at', 'to', 'of', 'a', 'an'}

        # Extract words (3+ characters)
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

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
    
    def _get_ml_score(self, cv: CVProfile, job: JobPosting) -> Optional[Dict]:
        """Get ML model prediction score"""
        if not self.ml_predictor:
            return None
        
        try:
            # Prepare CV data for ML predictor
            cv_data = {
                'Skills': ', '.join(cv.skills),
                'Experience': cv.experience_years or 0,
                'Education': cv.education or 'Bachelor',
                'Certifications': cv.extracted_data.get('certifications', 'None'),
                'Job Role': job.title,
                'Projects Count': cv.extracted_data.get('projects_count', 0),
                'Salary': cv.extracted_data.get('expected_salary', 50000)
            }
            
            # Get prediction from ML predictor
            result = self.ml_predictor.predict(cv_data, use_optimal_threshold=True)
            
            return result
            
        except Exception as e:
            logger.error(f"ML scoring failed: {e}")
            return None
    
    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize skill names for matching"""
        normalized = []
        
        for skill in skills:
            # Lowercase and strip
            skill = skill.lower().strip()
            
            # Remove common variations
            skill = skill.replace('.', '').replace('-', ' ')
            
            # Check canonical database for standardization
            canonical = self._get_canonical_skill(skill)
            normalized.append(canonical or skill)
        
        return normalized
    
    def _get_canonical_skill(self, skill: str) -> Optional[str]:
        """
        Resolve a skill to its canonical name.

        One dict lookup against the alias index built at load time, instead of
        the previous linear scan over the whole vocabulary per skill. That scan
        ran once per skill per job -- so at 800 jobs it was the hot path -- and
        it was also where A0 lived. See _build_alias_index.
        """
        if not self.skills_database:
            return None
        return self.skills_database.get(skill.lower())
    
    def _is_overqualified(self, cv: CVProfile, job: JobPosting, exp_score: float) -> bool:
        """Check if candidate is overqualified"""
        if job.min_experience_years is None or cv.experience_years is None:
            return False
        
        # Significantly more experience than required
        multiplier = 2.0  # Default overqualification multiplier
        return cv.experience_years > (job.min_experience_years * multiplier)
    
    def _is_underqualified(self, cv: CVProfile, job: JobPosting, skill_ratio: float) -> bool:
        """Check if candidate is underqualified"""
        # Missing too many critical skills
        return skill_ratio < 0.4
