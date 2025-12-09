"""
Agent 2: Feature Generator
Generates numerical features for profile-job matching.
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class FeatureGenerator:
    """
    Agent 2: Generates 12 numerical features for matching profiles to jobs.
    
    Features:
    1. skill_overlap_count - Number of matching skills
    2. skill_overlap_ratio - Ratio of matched skills to job requirements
    3. jaccard_similarity - Jaccard index of skill sets
    4. profile_skill_count - Total skills in profile
    5. job_skill_count - Total skills required by job
    6. experience_delta - Years difference (profile - job requirement)
    7. experience_match - Binary flag if meets requirement
    8. overqualified - Binary flag if experience > 2x requirement
    9. underqualified - Binary flag if experience < requirement
    10. experience_ratio - Profile experience / job requirement
    11. tfidf_similarity - Cosine similarity of profile and job text
    12. seniority_match - Binary flag if seniority levels align
    """
    
    # Define consistent feature order for ML model
    FEATURE_ORDER = [
        'skill_overlap_count',
        'skill_overlap_ratio',
        'jaccard_similarity',
        'profile_skill_count',
        'job_skill_count',
        'experience_delta',
        'experience_match',
        'overqualified',
        'underqualified',
        'experience_ratio',
        'tfidf_similarity',
        'seniority_match'
    ]
    
    def __init__(self, 
                 vectorizer_path: str = "models/tfidf_vectorizer.pkl",
                 output_dir: str = "data/json/features"):
        """
        Initialize the Feature Generator.
        
        Args:
            vectorizer_path: Path to save/load TF-IDF vectorizer
            output_dir: Directory to save feature files
        """
        self.vectorizer_path = Path(vectorizer_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create TF-IDF vectorizer
        self.tfidf_vectorizer = self._load_or_create_vectorizer()
        
        print(f"FeatureGenerator initialized")
        print(f"  - Vectorizer: {'loaded' if self.vectorizer_path.exists() else 'created'}")
        print(f"  - Output dir: {self.output_dir}")
    
    def _load_or_create_vectorizer(self) -> TfidfVectorizer:
        """Load existing vectorizer or create new one."""
        if self.vectorizer_path.exists():
            try:
                with open(self.vectorizer_path, 'rb') as f:
                    vectorizer = pickle.load(f)
                print(f"Loaded TF-IDF vectorizer from {self.vectorizer_path}")
                return vectorizer
            except Exception as e:
                print(f"Error loading vectorizer: {e}")
                print("Creating new vectorizer...")
        
        # Create new vectorizer
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1,  # Changed from 2 to 1 for small datasets
            stop_words='english'
        )
        
        # Save vectorizer directory
        self.vectorizer_path.parent.mkdir(parents=True, exist_ok=True)
        
        return vectorizer
    
    def save_vectorizer(self):
        """Save the TF-IDF vectorizer to disk."""
        try:
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
            print(f"Saved TF-IDF vectorizer to {self.vectorizer_path}")
        except Exception as e:
            print(f"Error saving vectorizer: {e}")
    
    def generate_features(self, profile: Dict, job: Dict) -> Dict:
        """
        Generate all 12 features for a profile-job pair.
        
        Args:
            profile: Parsed profile dictionary from Agent 1
            job: Parsed job dictionary from Agent 1
            
        Returns:
            Dictionary with all features
        """
        features = {}
        
        # 1-5: Skill overlap features
        skill_features = self._calculate_skill_overlap(
            profile.get('skills', []),
            job.get('skills', [])
        )
        features.update(skill_features)
        
        # 6-10: Experience features
        experience_features = self._calculate_experience_features(
            profile.get('experience_years', 0),
            job.get('experience', {})
        )
        features.update(experience_features)
        
        # 11: TF-IDF similarity
        tfidf_sim = self._calculate_tfidf_similarity(
            profile.get('cleaned_text', ''),
            job.get('qualifications', '')
        )
        features['tfidf_similarity'] = tfidf_sim
        
        # 12: Seniority match
        seniority_match = self._calculate_seniority_match(
            profile.get('seniority', ''),
            job.get('experience', {})
        )
        features['seniority_match'] = seniority_match
        
        return features
    
    def _calculate_skill_overlap(self, profile_skills: List[str], 
                                 job_skills: List[str]) -> Dict:
        """
        Calculate skill overlap features.
        
        Returns:
            Dictionary with 5 skill-related features
        """
        # Convert to sets for comparison (case-insensitive)
        profile_set = set([s.lower() for s in profile_skills])
        job_set = set([s.lower() for s in job_skills])
        
        # Calculate overlap
        overlap = profile_set & job_set
        union = profile_set | job_set
        
        # Feature 1: Overlap count
        skill_overlap_count = len(overlap)
        
        # Feature 2: Overlap ratio (matched / required)
        if len(job_set) > 0:
            skill_overlap_ratio = len(overlap) / len(job_set)
        else:
            skill_overlap_ratio = 0.0
        
        # Feature 3: Jaccard similarity
        if len(union) > 0:
            jaccard_similarity = len(overlap) / len(union)
        else:
            jaccard_similarity = 0.0
        
        # Feature 4: Profile skill count
        profile_skill_count = len(profile_set)
        
        # Feature 5: Job skill count
        job_skill_count = len(job_set)
        
        return {
            'skill_overlap_count': skill_overlap_count,
            'skill_overlap_ratio': skill_overlap_ratio,
            'jaccard_similarity': jaccard_similarity,
            'profile_skill_count': profile_skill_count,
            'job_skill_count': job_skill_count
        }
    
    def _calculate_experience_features(self, profile_exp: int, 
                                       job_exp: Dict) -> Dict:
        """
        Calculate experience-related features.
        
        Args:
            profile_exp: Years of experience in profile
            job_exp: Job experience dictionary with min_years and max_years
            
        Returns:
            Dictionary with 5 experience-related features
        """
        # Get job requirements
        min_years = job_exp.get('min_years', 0)
        max_years = job_exp.get('max_years', min_years)
        
        # Use average if range provided
        if max_years > min_years:
            required_exp = (min_years + max_years) / 2
        else:
            required_exp = min_years
        
        # Feature 6: Experience delta
        experience_delta = profile_exp - required_exp
        
        # Feature 7: Experience match (meets minimum requirement)
        experience_match = 1 if profile_exp >= min_years else 0
        
        # Feature 8: Overqualified (more than 2x max requirement)
        if max_years > 0:
            overqualified = 1 if profile_exp > (max_years * 2) else 0
        else:
            overqualified = 0
        
        # Feature 9: Underqualified (less than minimum)
        underqualified = 1 if profile_exp < min_years else 0
        
        # Feature 10: Experience ratio (capped at 2.0)
        if required_exp > 0:
            experience_ratio = min(profile_exp / required_exp, 2.0)
        else:
            experience_ratio = 1.0 if profile_exp == 0 else 2.0
        
        return {
            'experience_delta': experience_delta,
            'experience_match': experience_match,
            'overqualified': overqualified,
            'underqualified': underqualified,
            'experience_ratio': experience_ratio
        }
    
    def _calculate_tfidf_similarity(self, profile_text: str, 
                                    job_text: str) -> float:
        """
        Calculate TF-IDF cosine similarity between profile and job text.
        
        Args:
            profile_text: Cleaned profile text
            job_text: Job qualifications text
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        # Handle empty text
        if not profile_text or not job_text:
            return 0.0
        
        try:
            # Fit and transform texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([profile_text, job_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            print(f"Error calculating TF-IDF similarity: {e}")
            return 0.0
    
    def _calculate_seniority_match(self, profile_seniority: str, 
                                   job_exp: Dict) -> int:
        """
        Calculate if seniority level matches job requirements.
        
        Args:
            profile_seniority: Seniority level from profile
            job_exp: Job experience requirements
            
        Returns:
            1 if match, 0 otherwise
        """
        # Map seniority to experience ranges
        seniority_map = {
            'entry-level': (0, 2),
            'junior': (2, 5),
            'mid-level': (5, 10),
            'senior': (10, 20),
            'executive': (15, 50)
        }
        
        profile_seniority = profile_seniority.lower()
        
        if profile_seniority not in seniority_map:
            return 0
        
        # Get profile seniority range
        profile_min, profile_max = seniority_map[profile_seniority]
        
        # Get job requirements
        job_min = job_exp.get('min_years', 0)
        job_max = job_exp.get('max_years', job_min)
        
        # Check for overlap in ranges
        if job_max >= profile_min and job_min <= profile_max:
            return 1
        else:
            return 0
    
    def generate_feature_vector(self, features: Dict) -> np.ndarray:
        """
        Convert feature dictionary to numpy array in consistent order.
        
        Args:
            features: Dictionary of features
            
        Returns:
            Numpy array of 12 features in consistent order
        """
        vector = []
        for feature_name in self.FEATURE_ORDER:
            value = features.get(feature_name, 0.0)
            vector.append(float(value))
        
        return np.array(vector)
    
    def save_features(self, features: Dict, profile_id: str, job_id: str):
        """
        Save features to JSON file.
        
        Args:
            features: Feature dictionary
            profile_id: Profile identifier
            job_id: Job identifier
        """
        # Create feature record
        feature_record = {
            'profile_id': profile_id,
            'job_id': job_id,
            'features': features,
            'feature_vector': self.generate_feature_vector(features).tolist(),
            'generated_at': datetime.now().isoformat(),
            'generator_version': 'v1.0'
        }
        
        # Save to file
        output_path = self.output_dir / f"{profile_id}_{job_id}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(feature_record, f, indent=2, ensure_ascii=False)
        
        print(f"Saved features to: {output_path}")
    
    def load_features(self, profile_id: str, job_id: str) -> Dict:
        """
        Load features from JSON file.
        
        Args:
            profile_id: Profile identifier
            job_id: Job identifier
            
        Returns:
            Feature dictionary
        """
        feature_path = self.output_dir / f"{profile_id}_{job_id}.json"
        
        if not feature_path.exists():
            raise FileNotFoundError(f"Feature file not found: {feature_path}")
        
        with open(feature_path, 'r', encoding='utf-8') as f:
            feature_record = json.load(f)
        
        return feature_record


# Test function
if __name__ == "__main__":
    # Test the feature generator
    generator = FeatureGenerator()
    
    # Sample profile (from Agent 1 output)
    sample_profile = {
        'profile_id': 'test_001',
        'skills': ['python', 'java', 'sql', 'aws', 'docker'],
        'experience_years': 5,
        'seniority': 'mid-level',
        'cleaned_text': 'Experienced software engineer with expertise in Python and cloud technologies'
    }
    
    # Sample job (from Agent 1 output)
    sample_job = {
        'job_id': '12345',
        'job_title': 'Senior Python Developer',
        'skills': ['python', 'django', 'sql', 'aws', 'kubernetes'],
        'experience': {
            'min_years': 3,
            'max_years': 7
        },
        'qualifications': 'Looking for experienced Python developer with cloud experience'
    }
    
    print("\n" + "="*60)
    print("Testing Feature Generation")
    print("="*60)
    
    # Generate features
    features = generator.generate_features(sample_profile, sample_job)
    
    print("\nGenerated Features:")
    for feature_name in generator.FEATURE_ORDER:
        value = features.get(feature_name, 0.0)
        print(f"  {feature_name:25s}: {value}")
    
    # Generate feature vector
    feature_vector = generator.generate_feature_vector(features)
    print(f"\nFeature Vector: {feature_vector}")
    print(f"Vector Length: {len(feature_vector)}")
    
    # Save features
    generator.save_features(features, 'test_001', '12345')
    
    # Save vectorizer
    generator.save_vectorizer()
    
    print("\n" + "="*60)
    print("Feature Generation Test Complete!")
    print("="*60)
