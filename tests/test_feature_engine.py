"""
Comprehensive test suite for the Feature Engine.
"""
import pytest
import pandas as pd
import numpy as np
from src.features.engine import FeatureEngine


class TestFeatureEngine:
    """Tests for FeatureEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fe = FeatureEngine()

    def create_sample_data(self, days: int = 100) -> pd.DataFrame:
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
        np.random.seed(42)
        
        close = 100 + np.cumsum(np.random.randn(days) * 0.5)
        data = {
            'Open': close * (1 + np.random.randn(days) * 0.01),
            'High': close * (1 + np.abs(np.random.randn(days) * 0.02)),
            'Low': close * (1 - np.abs(np.random.randn(days) * 0.02)),
            'Close': close,
            'Volume': np.random.randint(1000000, 10000000, days),
        }
        
        return pd.DataFrame(data, index=dates)

    def test_handle_multiindex_single_level(self):
        """Test handling of single-level columns."""
        df = self.create_sample_data()
        result = self.fe._handle_multiindex(df)
        
        assert result.equals(df)

    def test_handle_multiindex_multi_level(self):
        """Test handling of multi-level columns."""
        df = self.create_sample_data()
        # Create multiindex columns
        df.columns = pd.MultiIndex.from_product([['Price'], df.columns])
        
        result = self.fe._handle_multiindex(df)
        
        # Should flatten to single level
        assert not isinstance(result.columns, pd.MultiIndex)

    def test_add_indicators(self):
        """Test adding technical indicators."""
        df = self.create_sample_data(250)
        result = self.fe.add_indicators(df)
        
        # Check all indicators are present
        assert 'SMA_20' in result.columns
        assert 'SMA_50' in result.columns
        assert 'SMA_100' in result.columns
        assert 'SMA_200' in result.columns
        assert 'Vol_SMA_20' in result.columns
        assert 'RSI_14' in result.columns
        assert 'ATR_14' in result.columns

    def test_add_indicators_rsi_range(self):
        """Test RSI values are in valid range (0-100)."""
        df = self.create_sample_data(250)
        result = self.fe.add_indicators(df)
        
        rsi = result['RSI_14'].dropna()
        assert (rsi >= 0).all()
        assert (rsi <= 100).all()

    def test_add_indicators_rsi_division_by_zero(self):
        """Test RSI handles division by zero (consecutive gains)."""
        # Create data with consecutive gains
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        close = pd.Series(range(100, 150), index=dates)  # Always increasing
        
        df = pd.DataFrame({
            'Open': close,
            'High': close * 1.02,
            'Low': close * 0.98,
            'Close': close,
            'Volume': [1000000] * 50
        })
        
        result = self.fe.add_indicators(df)
        
        # Should not have inf or NaN values (filled with 50)
        rsi = result['RSI_14'].fillna(50)
        assert not rsi.isin([np.inf, -np.inf]).any()

    def test_add_regime(self):
        """Test adding market regime."""
        df = self.create_sample_data(250)
        bench_df = self.create_sample_data(250)
        
        df = self.fe.add_indicators(df)
        bench_df = self.fe.add_indicators(bench_df)
        
        result = self.fe.add_regime(df, bench_df)
        
        assert 'Regime' in result.columns
        assert set(result['Regime'].unique()).issubset({0, 1})

    def test_add_regime_missing_data(self):
        """Test regime handles missing benchmark data."""
        df = self.create_sample_data(250)
        # Create benchmark with different date range
        bench_df = self.create_sample_data(100)
        
        df = self.fe.add_indicators(df)
        bench_df = self.fe.add_indicators(bench_df)
        
        result = self.fe.add_regime(df, bench_df)
        
        # Should fill missing values with 0
        assert not result['Regime'].isna().any()
