"""
Comprehensive test suite for Trading Strategies.
"""
import pytest
import pandas as pd
import numpy as np
from src.strategy.momentum import MomentumStrategy
from src.strategy.pullback import PullbackStrategy


class TestMomentumStrategy:
    """Tests for MomentumStrategy class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = MomentumStrategy()

    def create_sample_data(self, days: int = 250) -> pd.DataFrame:
        """Create sample OHLCV data with indicators."""
        dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
        np.random.seed(42)
        
        close = 100 + np.cumsum(np.random.randn(days) * 0.5)
        
        df = pd.DataFrame({
            'Open': close * (1 + np.random.randn(days) * 0.01),
            'High': close * (1 + np.abs(np.random.randn(days) * 0.02)),
            'Low': close * (1 - np.abs(np.random.randn(days) * 0.02)),
            'Close': close,
            'Volume': np.random.randint(1000000, 10000000, days),
        }, index=dates)
        
        # Add required SMAs
        df['SMA_200'] = df['Close'].rolling(200).mean()
        df['SMA_20'] = df['Close'].rolling(20).mean()
        
        return df

    def test_initialization(self):
        """Test strategy initialization."""
        assert self.strategy.trend_sma == 200
        assert self.strategy.breakout_window == 20
        assert self.strategy.exit_sma == 20
        assert self.strategy.stop_atr_mult == 2.0
        assert self.strategy.target_atr_mult == 6.0

    def test_custom_parameters(self):
        """Test initialization with custom parameters."""
        strategy = MomentumStrategy(
            trend_sma=100,
            breakout_window=30,
            exit_sma=10,
            stop_atr_mult=1.5,
            target_atr_mult=4.5
        )
        
        assert strategy.trend_sma == 100
        assert strategy.breakout_window == 30
        assert strategy.exit_sma == 10
        assert strategy.stop_atr_mult == 1.5
        assert strategy.target_atr_mult == 4.5

    def test_generate_signals(self):
        """Test signal generation."""
        df = self.create_sample_data()
        signals = self.strategy.generate_signals(df)
        
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_generate_signals_length(self):
        """Test signals have same length as input."""
        df = self.create_sample_data(300)
        signals = self.strategy.generate_signals(df)
        
        assert len(signals) == 300

    def test_calculate_stops(self):
        """Test stop and target calculation."""
        entry_price = 100.0
        atr = 5.0
        
        stop, target = self.strategy.calculate_stops(entry_price, atr)
        
        # Default: stop_atr_mult=2.0, target_atr_mult=6.0
        assert stop == 90.0  # 100 - (5 * 2)
        assert target == 130.0  # 100 + (5 * 6)

    def test_calculate_stops_custom_mult(self):
        """Test stop calculation with custom multipliers."""
        strategy = MomentumStrategy(stop_atr_mult=1.5, target_atr_mult=4.5)
        
        entry_price = 100.0
        atr = 5.0
        
        stop, target = strategy.calculate_stops(entry_price, atr)
        
        assert stop == 92.5  # 100 - (5 * 1.5)
        assert target == 122.5  # 100 + (5 * 4.5)


class TestPullbackStrategy:
    """Tests for PullbackStrategy class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = PullbackStrategy()

    def create_sample_data(self, days: int = 250) -> pd.DataFrame:
        """Create sample OHLCV data with indicators."""
        dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
        np.random.seed(42)
        
        close = 100 + np.cumsum(np.random.randn(days) * 0.5)
        
        df = pd.DataFrame({
            'Open': close * (1 + np.random.randn(days) * 0.01),
            'High': close * (1 + np.abs(np.random.randn(days) * 0.02)),
            'Low': close * (1 - np.abs(np.random.randn(days) * 0.02)),
            'Close': close,
            'Volume': np.random.randint(1000000, 10000000, days),
        }, index=dates)
        
        # Add required indicators
        df['SMA_100'] = df['Close'].rolling(100).mean()
        df['SMA_20'] = df['Close'].rolling(20).mean()
        # RSI between 30-70 for realistic testing
        df['RSI_14'] = 50 + np.random.randn(days) * 10
        df['RSI_14'] = df['RSI_14'].clip(30, 70)
        
        return df

    def test_initialization(self):
        """Test strategy initialization."""
        assert self.strategy.trend_sma == 100
        assert self.strategy.dip_sma == 20
        assert self.strategy.rsi_entry == 50
        assert self.strategy.rsi_exit == 75
        assert self.strategy.stop_atr_mult == 2.0
        assert self.strategy.target_atr_mult == 6.0

    def test_custom_parameters(self):
        """Test initialization with custom parameters."""
        strategy = PullbackStrategy(
            trend_sma=200,
            dip_sma=50,
            rsi_entry=40,
            rsi_exit=70,
            stop_atr_mult=1.5,
            target_atr_mult=4.5
        )
        
        assert strategy.trend_sma == 200
        assert strategy.dip_sma == 50
        assert strategy.rsi_entry == 40
        assert strategy.rsi_exit == 70

    def test_generate_signals(self):
        """Test signal generation."""
        df = self.create_sample_data()
        signals = self.strategy.generate_signals(df)
        
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_calculate_stops(self):
        """Test stop and target calculation."""
        entry_price = 100.0
        atr = 5.0
        
        stop, target = self.strategy.calculate_stops(entry_price, atr)
        
        assert stop == 90.0  # 100 - (5 * 2)
        assert target == 130.0  # 100 + (5 * 6)
