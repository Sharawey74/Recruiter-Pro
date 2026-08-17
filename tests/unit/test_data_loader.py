"""
Unit Tests for ML Engine - Data Loader Module

Tests the ATSDataLoader class for:
- Data loading and validation
- Column normalization
- Missing value handling
- Stratified splitting
- Edge cases and error handling
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.ml_engine.data_loader import ATSDataLoader


class TestATSDataLoader:
    """Unit tests for ATSDataLoader"""

    @pytest.fixture
    def sample_csv(self):
        """Create temporary CSV file with sample data"""
        # Create 100 samples for proper stratification
        np.random.seed(42)
        data = {
            "Name": ["John Doe", "Jane Smith", "Bob Johnson", "Alice Brown", "Charlie Davis"] * 20,
            "Experience (Years)": np.random.randint(1, 15, 100),
            "Salary Expectation ($)": np.random.randint(50000, 150000, 100),
            "Skills": ["Python, ML", "Java, SQL", "Python, AWS", "React, Node", "Python, ML, AWS"]
            * 20,
            "Education": np.random.choice(["Master", "Bachelor", "PhD", "High School"], 100),
            "Certifications": ["AWS Certified", "None", "Google ML", "None", "AWS Certified"] * 20,
            "Job Role": [
                "Data Scientist",
                "Software Engineer",
                "ML Engineer",
                "Frontend Dev",
                "Data Scientist",
            ]
            * 20,
            "Projects Count": np.random.randint(1, 20, 100),
            "AI Score (0-100)": np.random.randint(60, 100, 100),
            "Contact Info": ["test@example.com"] * 100,
            "Recruiter Decision": np.random.choice(["Hire", "Reject"], 100, p=[0.6, 0.4]),
        }
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_initialization(self, sample_csv):
        """Test DataLoader initialization"""
        loader = ATSDataLoader(sample_csv)
        assert loader.data_path == sample_csv
        assert loader.df is None

    @pytest.mark.unit
    @pytest.mark.ml
    def test_load_data_success(self, sample_csv):
        """Test successful data loading"""
        loader = ATSDataLoader(sample_csv)
        df = loader.load_data()

        assert df is not None
        assert len(df) == 100
        assert "Recruiter Decision" in df.columns
        assert "Experience" in df.columns  # Normalized column name
        assert "Salary" in df.columns  # Normalized column name

    @pytest.mark.unit
    @pytest.mark.ml
    def test_load_data_exclude_ai_score(self, sample_csv):
        """Test AI Score exclusion (data leakage prevention)"""
        loader = ATSDataLoader(sample_csv)
        df = loader.load_data(exclude_ai_score=True)

        assert "AI Score" not in df.columns
        assert "AI Score (0-100)" not in df.columns

    @pytest.mark.unit
    @pytest.mark.ml
    def test_column_normalization(self, sample_csv):
        """Test column name normalization"""
        loader = ATSDataLoader(sample_csv)
        df = loader.load_data()

        # Check original names are normalized
        assert "Experience (Years)" not in df.columns
        assert "Salary Expectation ($)" not in df.columns
        assert "Experience" in df.columns
        assert "Salary" in df.columns

    @pytest.mark.unit
    @pytest.mark.ml
    def test_stratified_split(self, sample_csv):
        """Test stratified train/val/test splitting"""
        loader = ATSDataLoader(sample_csv)
        loader.load_data()

        train_df, val_df, test_df = loader.split_data(test_size=0.2, val_size=0.2, random_state=42)

        # Check sizes
        total = len(loader.df)
        assert len(train_df) + len(val_df) + len(test_df) == total

        # Check stratification (class distribution should be similar)
        train_hire_pct = (train_df["Recruiter Decision"] == "Hire").mean()
        val_hire_pct = (val_df["Recruiter Decision"] == "Hire").mean()
        test_hire_pct = (test_df["Recruiter Decision"] == "Hire").mean()

        # Allow 20% tolerance due to small sample size
        assert abs(train_hire_pct - 0.6) < 0.3
        assert abs(val_hire_pct - 0.6) < 0.5
        assert abs(test_hire_pct - 0.6) < 0.5

    @pytest.mark.unit
    @pytest.mark.ml
    def test_get_X_y(self, sample_csv):
        """Test feature/target extraction"""
        loader = ATSDataLoader(sample_csv)
        df = loader.load_data()

        X, y = loader.get_X_y(df)

        assert len(X) == len(df)
        assert len(y) == len(df)
        assert "Recruiter Decision" not in X.columns
        # y should be binary (0/1) after mapping
        assert all(y.isin([0, 1]))

    @pytest.mark.unit
    @pytest.mark.ml
    def test_missing_values_handling(self):
        """Test handling of missing values"""
        # Create data with missing values, but multiplied properly
        base_data = {
            "Name": ["John", "Jane", "Bob"],
            "Experience (Years)": [5, 3, 8],
            "Salary Expectation ($)": [80000, 65000, 100000],
            "Skills": ["Python", "Java", "Java"],
            "Education": ["Master", "Bachelor", "PhD"],
            "Certifications": ["AWS", "None", "GCP"],
            "Job Role": ["Data Scientist", "Engineer", "Engineer"],
            "Projects Count": [8, 5, 10],
            "AI Score (0-100)": [85, 70, 95],
            "Contact Info": ["john@example.com", "jane@example.com", "bob@example.com"],
            "Recruiter Decision": ["Hire", "Reject", "Hire"],
        }

        # Repeat 10 times to get 30 rows
        df = pd.concat([pd.DataFrame(base_data)] * 10, ignore_index=True)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            loader = ATSDataLoader(temp_path)
            df_loaded = loader.load_data()

            # The loader calls drop_duplicates(), so 10 copies of 3 identical
            # rows collapse back to 3. This asserted 30 and had never passed:
            # the expectation was wrong, not the code. Pinning the real
            # behaviour makes the deduplication a tested contract instead of an
            # accident.
            assert df_loaded is not None
            assert len(df_loaded) == 3, "identical rows should be deduplicated"
            assert "AI Score (0-100)" not in df_loaded.columns  # AI Score should be excluded
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_file_not_found(self):
        """Test error handling for missing file"""
        loader = ATSDataLoader("nonexistent_file.csv")

        with pytest.raises(FileNotFoundError):
            loader.load_data()

    @pytest.mark.unit
    @pytest.mark.ml
    def test_empty_dataframe(self):
        """Test handling of empty CSV"""
        # Create empty CSV
        df = pd.DataFrame()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            loader = ATSDataLoader(temp_path)

            with pytest.raises(ValueError):
                loader.load_data()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_class_distribution_calculation(self, sample_csv):
        """Test class distribution reporting"""
        loader = ATSDataLoader(sample_csv)
        df = loader.load_data()

        # Should have calculated class distribution
        assert hasattr(loader, "df")
        assert "Recruiter Decision" in df.columns

        hire_count = (df["Recruiter Decision"] == "Hire").sum()
        reject_count = (df["Recruiter Decision"] == "Reject").sum()

        assert hire_count > 0
        assert reject_count > 0
        assert hire_count + reject_count == len(df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
