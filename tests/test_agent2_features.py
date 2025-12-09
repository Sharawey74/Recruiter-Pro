"""
Unit tests for Agent 2: Feature Generator
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.agent2_features import FeatureGenerator


class TestFeatureGenerator:
    """Test suite for FeatureGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a FeatureGenerator instance for testing."""
        return FeatureGenerator()
    
    @pytest.fixture
    def sample_profile(self):
        """Sample profile for testing."""
        return {
            'profile_id': 'test_profile_001',
            'skills': ['python', 'java', 'sql', 'aws', 'docker'],
            'experience_years': 5,
            'seniority': 'mid-level',
            'cleaned_text': 'Experienced software engineer with Python and cloud expertise'
        }
    
    @pytest.fixture
    def sample_job(self):
        """Sample job for testing."""
        return {
            'job_id': 'test_job_001',
            'job_title': 'Senior Python Developer',
            'skills': ['python', 'django', 'sql', 'aws', 'kubernetes'],
            'experience': {
                'min_years': 3,
                'max_years': 7
            },
            'qualifications': 'Looking for experienced Python developer with cloud experience'
        }
    
    # Test Skill Overlap Features
    
    def test_skill_overlap_exact_match(self, generator):
        """Test skill overlap with exact match."""
        profile_skills = ['python', 'java', 'sql']
        job_skills = ['python', 'java', 'sql']
        
        features = generator._calculate_skill_overlap(profile_skills, job_skills)
        
        assert features['skill_overlap_count'] == 3
        assert features['skill_overlap_ratio'] == 1.0
        assert features['jaccard_similarity'] == 1.0
        assert features['profile_skill_count'] == 3
        assert features['job_skill_count'] == 3
    
    def test_skill_overlap_no_match(self, generator):
        """Test skill overlap with no matches."""
        profile_skills = ['python', 'java']
        job_skills = ['ruby', 'go']
        
        features = generator._calculate_skill_overlap(profile_skills, job_skills)
        
        assert features['skill_overlap_count'] == 0
        assert features['skill_overlap_ratio'] == 0.0
        assert features['jaccard_similarity'] == 0.0
        assert features['profile_skill_count'] == 2
        assert features['job_skill_count'] == 2
    
    def test_skill_overlap_partial_match(self, generator):
        """Test skill overlap with partial match."""
        profile_skills = ['python', 'java', 'sql', 'aws']
        job_skills = ['python', 'sql', 'docker']
        
        features = generator._calculate_skill_overlap(profile_skills, job_skills)
        
        assert features['skill_overlap_count'] == 2
        assert features['skill_overlap_ratio'] == pytest.approx(2/3, rel=0.01)
        assert features['jaccard_similarity'] == pytest.approx(2/5, rel=0.01)
        assert features['profile_skill_count'] == 4
        assert features['job_skill_count'] == 3
    
    def test_skill_overlap_empty_skills(self, generator):
        """Test skill overlap with empty skill lists."""
        features = generator._calculate_skill_overlap([], [])
        
        assert features['skill_overlap_count'] == 0
        assert features['skill_overlap_ratio'] == 0.0
        assert features['jaccard_similarity'] == 0.0
        assert features['profile_skill_count'] == 0
        assert features['job_skill_count'] == 0
    
    def test_skill_overlap_case_insensitive(self, generator):
        """Test that skill matching is case-insensitive."""
        profile_skills = ['Python', 'JAVA', 'Sql']
        job_skills = ['python', 'java', 'sql']
        
        features = generator._calculate_skill_overlap(profile_skills, job_skills)
        
        assert features['skill_overlap_count'] == 3
        assert features['skill_overlap_ratio'] == 1.0
    
    # Test Experience Features
    
    def test_experience_exact_match(self, generator):
        """Test experience features with exact match."""
        profile_exp = 5
        job_exp = {'min_years': 5, 'max_years': 7}
        
        features = generator._calculate_experience_features(profile_exp, job_exp)
        
        assert features['experience_delta'] == -1.0  # 5 - 6 (average)
        assert features['experience_match'] == 1
        assert features['overqualified'] == 0
        assert features['underqualified'] == 0
        assert features['experience_ratio'] == pytest.approx(5/6, rel=0.01)
    
    def test_experience_overqualified(self, generator):
        """Test experience features when overqualified."""
        profile_exp = 20
        job_exp = {'min_years': 3, 'max_years': 7}
        
        features = generator._calculate_experience_features(profile_exp, job_exp)
        
        assert features['experience_match'] == 1
        assert features['overqualified'] == 1  # 20 > 7*2
        assert features['underqualified'] == 0
    
    def test_experience_underqualified(self, generator):
        """Test experience features when underqualified."""
        profile_exp = 2
        job_exp = {'min_years': 5, 'max_years': 8}
        
        features = generator._calculate_experience_features(profile_exp, job_exp)
        
        assert features['experience_match'] == 0
        assert features['overqualified'] == 0
        assert features['underqualified'] == 1
    
    def test_experience_zero_experience(self, generator):
        """Test experience features with zero experience."""
        profile_exp = 0
        job_exp = {'min_years': 0, 'max_years': 2}
        
        features = generator._calculate_experience_features(profile_exp, job_exp)
        
        assert features['experience_delta'] == -1.0  # 0 - 1 (average)
        assert features['experience_match'] == 1  # Meets minimum of 0
        assert features['underqualified'] == 0
    
    def test_experience_ratio_capped(self, generator):
        """Test that experience ratio is capped at 2.0."""
        profile_exp = 30
        job_exp = {'min_years': 5, 'max_years': 10}
        
        features = generator._calculate_experience_features(profile_exp, job_exp)
        
        assert features['experience_ratio'] == 2.0  # Capped
    
    # Test TF-IDF Similarity
    
    def test_tfidf_similarity_similar_text(self, generator):
        """Test TF-IDF similarity with similar text."""
        text1 = "Python developer with machine learning experience"
        text2 = "Looking for Python developer with ML experience"
        
        similarity = generator._calculate_tfidf_similarity(text1, text2)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.25  # Should have some similarity (adjusted threshold)
    
    def test_tfidf_similarity_different_text(self, generator):
        """Test TF-IDF similarity with completely different text."""
        text1 = "Python developer with cloud experience"
        text2 = "Marketing manager with sales expertise"
        
        similarity = generator._calculate_tfidf_similarity(text1, text2)
        
        assert 0.0 <= similarity <= 1.0
    
    def test_tfidf_similarity_empty_text(self, generator):
        """Test TF-IDF similarity with empty text."""
        similarity = generator._calculate_tfidf_similarity("", "Some text")
        assert similarity == 0.0
        
        similarity = generator._calculate_tfidf_similarity("Some text", "")
        assert similarity == 0.0
        
        similarity = generator._calculate_tfidf_similarity("", "")
        assert similarity == 0.0
    
    # Test Seniority Match
    
    def test_seniority_match_aligned(self, generator):
        """Test seniority match when aligned."""
        # Mid-level (5-10 years) should match 5-8 years requirement
        match = generator._calculate_seniority_match(
            'mid-level',
            {'min_years': 5, 'max_years': 8}
        )
        assert match == 1
    
    def test_seniority_match_not_aligned(self, generator):
        """Test seniority match when not aligned."""
        # Entry-level (0-2 years) should not match 10+ years requirement
        match = generator._calculate_seniority_match(
            'entry-level',
            {'min_years': 10, 'max_years': 15}
        )
        assert match == 0
    
    def test_seniority_match_unknown(self, generator):
        """Test seniority match with unknown seniority."""
        match = generator._calculate_seniority_match(
            'unknown',
            {'min_years': 5, 'max_years': 8}
        )
        assert match == 0
    
    # Test Feature Generation
    
    def test_generate_features_complete(self, generator, sample_profile, sample_job):
        """Test that all 12 features are generated."""
        features = generator.generate_features(sample_profile, sample_job)
        
        # Check all features present
        assert len(features) == 12
        for feature_name in generator.FEATURE_ORDER:
            assert feature_name in features
    
    def test_generate_features_values_valid(self, generator, sample_profile, sample_job):
        """Test that generated feature values are valid."""
        features = generator.generate_features(sample_profile, sample_job)
        
        # Check skill overlap features
        assert features['skill_overlap_count'] >= 0
        assert 0.0 <= features['skill_overlap_ratio'] <= 1.0
        assert 0.0 <= features['jaccard_similarity'] <= 1.0
        assert features['profile_skill_count'] >= 0
        assert features['job_skill_count'] >= 0
        
        # Check experience features
        assert features['experience_match'] in [0, 1]
        assert features['overqualified'] in [0, 1]
        assert features['underqualified'] in [0, 1]
        assert features['experience_ratio'] >= 0.0
        
        # Check other features
        assert 0.0 <= features['tfidf_similarity'] <= 1.0
        assert features['seniority_match'] in [0, 1]
    
    # Test Feature Vector Generation
    
    def test_generate_feature_vector_length(self, generator, sample_profile, sample_job):
        """Test that feature vector has correct length."""
        features = generator.generate_features(sample_profile, sample_job)
        vector = generator.generate_feature_vector(features)
        
        assert len(vector) == 12
        assert isinstance(vector, np.ndarray)
    
    def test_generate_feature_vector_order(self, generator):
        """Test that feature vector maintains consistent order."""
        features = {
            'skill_overlap_count': 5,
            'skill_overlap_ratio': 0.8,
            'jaccard_similarity': 0.6,
            'profile_skill_count': 10,
            'job_skill_count': 8,
            'experience_delta': 2.0,
            'experience_match': 1,
            'overqualified': 0,
            'underqualified': 0,
            'experience_ratio': 1.5,
            'tfidf_similarity': 0.7,
            'seniority_match': 1
        }
        
        vector = generator.generate_feature_vector(features)
        
        # Check order matches FEATURE_ORDER
        expected = [5, 0.8, 0.6, 10, 8, 2.0, 1, 0, 0, 1.5, 0.7, 1]
        np.testing.assert_array_almost_equal(vector, expected)
    
    def test_generate_feature_vector_missing_features(self, generator):
        """Test feature vector generation with missing features."""
        features = {'skill_overlap_count': 5}  # Only one feature
        
        vector = generator.generate_feature_vector(features)
        
        assert len(vector) == 12
        assert vector[0] == 5.0
        # All other features should default to 0.0
        assert all(v == 0.0 for v in vector[1:])
    
    # Test Feature Persistence
    
    def test_save_and_load_features(self, generator, sample_profile, sample_job, tmp_path):
        """Test saving and loading features."""
        # Use temporary directory
        generator.output_dir = tmp_path
        
        features = generator.generate_features(sample_profile, sample_job)
        
        # Save features
        generator.save_features(features, 'test_profile', 'test_job')
        
        # Load features
        loaded = generator.load_features('test_profile', 'test_job')
        
        assert loaded['profile_id'] == 'test_profile'
        assert loaded['job_id'] == 'test_job'
        assert loaded['features'] == features
    
    # Test Edge Cases
    
    def test_edge_case_empty_profile(self, generator):
        """Test with empty profile."""
        empty_profile = {
            'skills': [],
            'experience_years': 0,
            'seniority': '',
            'cleaned_text': ''
        }
        
        job = {
            'skills': ['python', 'java'],
            'experience': {'min_years': 3, 'max_years': 5},
            'qualifications': 'Need experienced developer'
        }
        
        features = generator.generate_features(empty_profile, job)
        
        # Should not crash, should return valid features
        assert len(features) == 12
        assert features['skill_overlap_count'] == 0
        assert features['underqualified'] == 1
    
    def test_edge_case_empty_job(self, generator):
        """Test with empty job."""
        profile = {
            'skills': ['python', 'java'],
            'experience_years': 5,
            'seniority': 'mid-level',
            'cleaned_text': 'Experienced developer'
        }
        
        empty_job = {
            'skills': [],
            'experience': {'min_years': 0, 'max_years': 0},
            'qualifications': ''
        }
        
        features = generator.generate_features(profile, empty_job)
        
        # Should not crash
        assert len(features) == 12
        assert features['skill_overlap_count'] == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])
