"""
Comprehensive test suite for the Data Loader.
"""
import pytest
import pandas as pd
from pathlib import Path
from src.data.loader import DataLoader


class TestDataLoader:
    """Tests for DataLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = DataLoader(data_dir="test_data")

    def teardown_method(self):
        """Clean up test files."""
        import shutil
        test_dir = Path("test_data")
        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_initialization(self):
        """Test DataLoader initialization."""
        assert self.loader.data_dir.exists()
        assert self.loader.data_dir.name == "test_data"

    def test_get_file_path(self):
        """Test file path generation."""
        path = self.loader._get_file_path("AAPL")
        assert path.name == "AAPL.parquet"
        
        path = self.loader._get_file_path("7203.T")
        assert path.name == "7203_T.parquet"

    def test_validate_data_valid(self):
        """Test validation with valid data."""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [105.0, 106.0, 107.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [103.0, 104.0, 105.0],
            'Volume': [1000000, 1100000, 1200000]
        })
        
        # Should not raise
        self.loader._validate_data(df)

    def test_validate_data_missing_column(self):
        """Test validation fails with missing column."""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [105.0],
            # Missing Low, Close, Volume
        })
        
        with pytest.raises(ValueError, match="Missing required column"):
            self.loader._validate_data(df)

    def test_validate_data_nan_values(self):
        """Test validation fails with NaN values."""
        df = pd.DataFrame({
            'Open': [100.0, None],
            'High': [105.0, 106.0],
            'Low': [99.0, 100.0],
            'Close': [103.0, 104.0],
            'Volume': [1000000, 1100000]
        })
        
        with pytest.raises(ValueError, match="NaN values"):
            self.loader._validate_data(df)

    def test_validate_data_negative_values(self):
        """Test validation fails with negative values."""
        df = pd.DataFrame({
            'Open': [100.0, -50.0],
            'High': [105.0, 106.0],
            'Low': [99.0, 100.0],
            'Close': [103.0, 104.0],
            'Volume': [1000000, 1100000]
        })
        
        with pytest.raises(ValueError, match="Negative values"):
            self.loader._validate_data(df)

    def test_validate_data_high_less_than_low(self):
        """Test validation fails when High < Low."""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [95.0],  # High < Low
            'Low': [100.0],
            'Close': [103.0],
            'Volume': [1000000]
        })
        
        with pytest.raises(ValueError, match="High < Low"):
            self.loader._validate_data(df)

    def test_validate_data_high_less_than_close(self):
        """Test validation fails when High < Close."""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [95.0],  # High < Close (but will fail High < Open first)
            'Low': [90.0],
            'Close': [103.0],
            'Volume': [1000000]
        })
        
        # This will fail on "High < Open" check first since 95 < 100
        with pytest.raises(ValueError, match="High < Open"):
            self.loader._validate_data(df)

    def test_validate_data_low_greater_than_open(self):
        """Test validation fails when Low > Open."""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [110.0],
            'Low': [105.0],  # Low > Open
            'Close': [103.0],
            'Volume': [1000000]
        })
        
        with pytest.raises(ValueError, match="Low > Open"):
            self.loader._validate_data(df)
