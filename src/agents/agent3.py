"""
Agent 3: Job Matcher & Decision Engine
Rule-based scoring with intelligent decision logic and detailed explanations
Maximized efficiency with synonym matching and comprehensive explanation generation
"""
import logging
from typing import Dict, List, Tuple

class JobMatcher:
    """
    Deterministic Job Matcher & Decision Engine - Agent 3
    Scoring: Weighted formula with skill/experience/education components
    Decision: Rule-based with detailed, actionable explanations
    """
    
    # Classification thresholds
    THRESHOLD_SHORTLIST = 0.70  # 70%+
    THRESHOLD_REVIEW = 0.40     # 40-69%
    
    # Scoring weights
    WEIGHT_SKILLS = 0.60
    WEIGHT_EXPERIENCE = 0.25
    WEIGHT_EDUCATION = 0.10
    WEIGHT_KEYWORDS = 0.05
    
    # Comprehensive skill synonyms
    SKILL_SYNONYMS = {
        'js': ['javascript', 'js', 'ecmascript'],
        'javascript': ['javascript', 'js', 'ecmascript'],
        'ts': ['typescript', 'ts'],
        'typescript': ['typescript', 'ts'],
        'nodejs': ['node.js', 'nodejs', 'node'],
        'node.js': ['node.js', 'nodejs', 'node'],
        'node': ['node.js', 'nodejs', 'node'],
        'react': ['react', 'reactjs', 'react.js'],
        'reactjs': ['react', 'reactjs', 'react.js'],
        'angular': ['angular', 'angularjs', 'angular.js'],
        'angularjs': ['angular', 'angularjs', 'angular.js'],
        'vue': ['vue', 'vuejs', 'vue.js'],
        'vuejs': ['vue', 'vuejs', 'vue.js'],
        'mongodb': ['mongodb', 'mongo'],
        'mongo': ['mongodb', 'mongo'],
        'postgresql': ['postgresql', 'postgres', 'psql'],
        'postgres': ['postgresql', 'postgres', 'psql'],
        'k8s': ['kubernetes', 'k8s'],
        'kubernetes': ['kubernetes', 'k8s'],
        'ml': ['machine learning', 'ml'],
        'machine learning': ['machine learning', 'ml'],
        'ai': ['artificial intelligence', 'ai'],
        'artificial intelligence': ['artificial intelligence', 'ai'],
        'sklearn': ['scikit-learn', 'sklearn'],
        'scikit-learn': ['scikit-learn', 'sklearn'],
        'c++': ['c++', 'cpp'],
        'cpp': ['c++', 'cpp'],
        'c#': ['c#', 'csharp'],
        'csharp': ['c#', 'csharp'],
        'go': ['go', 'golang'],
        'golang': ['go', 'golang']
    }
    
    def __init__(self):
        self.logger = logging.getLogger("Agent3_Matcher")
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    def match_and_decide(self, candidate: Dict, jobs: List[Dict]) -> List[Dict]:
        """
        Main pipeline: Score all jobs and generate decisions with explanations
        
        Args:
            candidate: Structured profile from Agent 2
            jobs: List of job postings
            
        Returns:
            Ranked list of matches with decisions and detailed explanations
        """
        results = []
        
        for job in jobs:
            # Calculate score components
            skill_score, matched, missing = self._score_skills(
                candidate.get('skills', []),
                job.get('required_skills', [])
            )
            
            exp_score = self._score_experience(
                candidate.get('experience_years', 0),
                job.get('min_experience_years', 0)
            )
            
            edu_score = self._score_education(
                candidate.get('education', []),
                job.get('description', '')
            )
            
            keyword_score = self._score_keywords(candidate, job)
            
            # Weighted final score
            final_score = (
                skill_score * self.WEIGHT_SKILLS +
                exp_score * self.WEIGHT_EXPERIENCE +
                edu_score * self.WEIGHT_EDUCATION +
                keyword_score * self.WEIGHT_KEYWORDS
            )
            
            # Make decision
            decision = self._make_decision(final_score)
            
            # Generate detailed explanation
            explanation = self._generate_explanation(
                decision, final_score, skill_score, exp_score,
                matched, missing, candidate, job
            )
            
            result = {
                "job_id": job.get('job_id', ''),
                "job_title": job.get('title', ''),
                "score": round(final_score * 100, 1),
                "decision": decision,
                "explanation": explanation,
                "matched_skills": list(matched),
                "missing_skills": list(missing),
                "skill_match_percentage": round(skill_score * 100, 1),
                "experience_match": exp_score >= 0.8,
                "experience_years_candidate": candidate.get('experience_years', 0),
                "experience_years_required": job.get('min_experience_years', 0),
                "breakdown": {
                    "skills": round(skill_score * 100, 1),
                    "experience": round(exp_score * 100, 1),
                    "education": round(edu_score * 100, 1),
                    "keywords": round(keyword_score * 100, 1)
                }
            }
            
            results.append(result)
            self.logger.info(
                f"{job.get('title')}: {result['score']}% → {decision}"
            )
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Add rankings
        for i, result in enumerate(results, 1):
            result['ranking'] = i
        
        return results[:3]  # Top 3 only
    
    def _score_skills(self, candidate_skills: List[str], job_skills: List[str]) -> Tuple[float, set, set]:
        """
        Score skill match with synonym support
        Returns: (score, matched_skills, missing_skills)
        """
        if not job_skills:
            return 0.0, set(), set()
        
        # Normalize and expand with synonyms
        candidate_set = self._expand_skills(set(s.lower() for s in candidate_skills))
        job_set = self._expand_skills(set(s.lower() for s in job_skills))
        
        # Find matches
        matched = candidate_set.intersection(job_set)
        
        # Map back to original job skills for display
        matched_display = set()
        missing_display = set()
        
        for job_skill in job_skills:
            job_skill_expanded = self._expand_skills({job_skill.lower()})
            if job_skill_expanded.intersection(candidate_set):
                matched_display.add(job_skill.lower())
            else:
                missing_display.add(job_skill.lower())
        
        score = len(matched_display) / len(job_skills) if job_skills else 0.0
        
        return score, matched_display, missing_display
    
    def _expand_skills(self, skills: set) -> set:
        """Expand skills using synonym mapping"""
        expanded = set(skills)
        for skill in skills:
            if skill in self.SKILL_SYNONYMS:
                expanded.update(self.SKILL_SYNONYMS[skill])
        return expanded
    
    def _score_experience(self, candidate_years: int, required_years: int) -> float:
        """
        Experience scoring:
        - Meets or exceeds: 1.0
        - Slightly under (80%+): 0.7
        - Significantly under: Proportional
        - No experience vs requirement: 0.2
        """
        if required_years == 0:
            return 1.0
        
        if candidate_years >= required_years:
            # Bonus for exceeding (caps at 1.0)
            excess_bonus = min((candidate_years - required_years) * 0.05, 0.0)
            return min(1.0 + excess_bonus, 1.0)
        
        ratio = candidate_years / required_years
        
        if ratio >= 0.8:
            return 0.7
        elif ratio >= 0.5:
            return 0.5
        elif ratio > 0:
            return 0.3
        else:
            return 0.2
    
    def _score_education(self, candidate_edu: List[str], job_desc: str) -> float:
        """
        Education scoring based on requirement detection
        """
        job_desc_lower = job_desc.lower()
        
        # Check if education is required
        requires_bachelors = any(kw in job_desc_lower for kw in ['bachelor', "bachelor's", 'b.s', 'b.a', 'b.sc'])
        requires_masters = any(kw in job_desc_lower for kw in ['master', "master's", 'm.s', 'm.a', 'mba'])
        requires_phd = any(kw in job_desc_lower for kw in ['phd', 'ph.d', 'doctorate', 'doctoral'])
        
        if not (requires_bachelors or requires_masters or requires_phd):
            return 0.5  # Neutral if not specified
        
        has_bachelors = any('bachelor' in edu.lower() or 'associate' in edu.lower() for edu in candidate_edu)
        has_masters = any('master' in edu.lower() for edu in candidate_edu)
        has_phd = any('phd' in edu.lower() or 'doctorate' in edu.lower() for edu in candidate_edu)
        
        if requires_phd:
            return 1.0 if has_phd else 0.3
        elif requires_masters:
            if has_masters or has_phd:
                return 1.0
            elif has_bachelors:
                return 0.6
            else:
                return 0.3
        elif requires_bachelors:
            if has_bachelors or has_masters or has_phd:
                return 1.0
            else:
                return 0.4
        
        return 0.5
    
    def _score_keywords(self, candidate: Dict, job: Dict) -> float:
        """Bonus score for matching job title keywords"""
        candidate_text = ' '.join([
            candidate.get('name', ''),
            ' '.join(candidate.get('skills', [])),
            ' '.join(candidate.get('education', []))
        ]).lower()
        
        job_title = job.get('title', '').lower()
        
        # Extract meaningful keywords (exclude common words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'of', 'with', 'at', 'by', 'from'}
        title_words = [w for w in job_title.split() if w not in stop_words and len(w) > 2]
        
        if not title_words:
            return 0.5
        
        matches = sum(1 for word in title_words if word in candidate_text)
        return matches / len(title_words)
    
    def _make_decision(self, score: float) -> str:
        """
        Decision rules:
        - 70%+: SHORTLIST
        - 40-69%: REVIEW
        - <40%: REJECT
        """
        if score >= self.THRESHOLD_SHORTLIST:
            return "SHORTLIST"
        elif score >= self.THRESHOLD_REVIEW:
            return "REVIEW"
        else:
            return "REJECT"
    
    def _generate_explanation(
        self, decision: str, final_score: float, skill_score: float, exp_score: float,
        matched: set, missing: set, candidate: Dict, job: Dict
    ) -> str:
        """
        Generate detailed 3-4 sentence explanation for hiring decision
        Provides actionable insights for recruiters
        """
        candidate_name = candidate.get('name', 'Candidate')
        job_title = job.get('title', 'this position')
        candidate_exp = candidate.get('experience_years', 0)
        required_exp = job.get('min_experience_years', 0)
        
        matched_count = len(matched)
        total_required = len(matched) + len(missing)
        missing_count = len(missing)
        
        explanations = {
            "SHORTLIST": self._explanation_shortlist,
            "REVIEW": self._explanation_review,
            "REJECT": self._explanation_reject
        }
        
        return explanations[decision](
            candidate_name, job_title, final_score, skill_score, exp_score,
            matched_count, total_required, missing_count, matched, missing,
            candidate_exp, required_exp
        )
    
    def _explanation_shortlist(
        self, name, job_title, score, skill_score, exp_score,
        matched_count, total_required, missing_count, matched, missing,
        cand_exp, req_exp
    ) -> str:
        """Generate SHORTLIST explanation"""
        # Sentence 1: Overall assessment
        explanation = f"Strong candidate for {job_title} with {score:.0f}% overall match. "
        
        # Sentence 2: Skills analysis
        if skill_score >= 0.8:
            matched_list = ', '.join(list(matched)[:4])
            explanation += f"Excellent skill alignment with {matched_count}/{total_required} required skills matched ({matched_list}). "
        else:
            matched_list = ', '.join(list(matched)[:4])
            explanation += f"Good skill coverage with {matched_count}/{total_required} core competencies ({matched_list}). "
        
        # Sentence 3: Experience analysis
        if exp_score >= 0.9:
            explanation += f"Exceeds experience requirement ({cand_exp} years vs {req_exp} required). "
        else:
            explanation += f"Meets experience requirement ({cand_exp} years experience). "
        
        # Sentence 4: Recommendation
        if missing_count == 0:
            explanation += "Perfect skill match - recommend immediate interview."
        elif missing_count <= 2:
            missing_list = ', '.join(list(missing))
            explanation += f"Minor gaps in {missing_list} can be addressed through training. Recommended for next round."
        else:
            explanation += "Recommend interview to assess cultural fit and discuss skill development plan."
        
        return explanation
    
    def _explanation_review(
        self, name, job_title, score, skill_score, exp_score,
        matched_count, total_required, missing_count, matched, missing,
        cand_exp, req_exp
    ) -> str:
        """Generate REVIEW explanation"""
        # Sentence 1: Overall assessment
        explanation = f"Moderate match for {job_title} with {score:.0f}% compatibility. "
        
        # Sentence 2: Skills analysis
        if skill_score >= 0.5:
            matched_list = ', '.join(list(matched)[:3])
            explanation += f"Possesses {matched_count}/{total_required} required skills including {matched_list}. "
        else:
            explanation += f"Limited skill overlap with {matched_count}/{total_required} competencies matched. "
        
        # Sentence 3: Gap analysis
        if missing_count > 0:
            missing_list = ', '.join(list(missing)[:3])
            if missing_count > 3:
                explanation += f"Notable gaps in {missing_list} and {missing_count - 3} other areas. "
            else:
                explanation += f"Missing key skills: {missing_list}. "
        
        # Sentence 4: Recommendation
        if exp_score >= 0.7:
            explanation += f"Strong experience background ({cand_exp} years) may compensate for skill gaps through on-the-job learning. Consider for phone screening."
        elif cand_exp < req_exp:
            explanation += f"Underqualified in experience ({cand_exp} vs {req_exp} years required). Suitable for junior version of role or with extensive training program."
        else:
            explanation += "Review application carefully to assess potential and growth trajectory. May be suitable with mentoring support."
        
        return explanation
    
    def _explanation_reject(
        self, name, job_title, score, skill_score, exp_score,
        matched_count, total_required, missing_count, matched, missing,
        cand_exp, req_exp
    ) -> str:
        """Generate REJECT explanation"""
        # Sentence 1: Overall assessment
        explanation = f"Not recommended for {job_title} with only {score:.0f}% match. "
        
        # Sentence 2: Skills gap
        if matched_count > 0:
            matched_list = ', '.join(list(matched)[:2])
            explanation += f"Minimal skill alignment - only {matched_count}/{total_required} requirements met ({matched_list}). "
        else:
            explanation += f"No matching technical skills from the {total_required} requirements. "
        
        # Sentence 3: Specific gaps
        if missing_count > 0:
            missing_list = ', '.join(list(missing)[:4])
            if missing_count > 4:
                explanation += f"Lacks critical competencies including {missing_list} and {missing_count - 4} others. "
            else:
                explanation += f"Missing essential skills: {missing_list}. "
        
        # Sentence 4: Final recommendation
        if exp_score < 0.3:
            explanation += f"Additionally underqualified in experience ({cand_exp} vs {req_exp} years). Not suitable for current role requirements."
        else:
            explanation += "Experience level present but insufficient to compensate for significant skill gaps. Recommend alternative positions better aligned with background."
        
        return explanation


# Singleton instance
matcher = JobMatcher()
