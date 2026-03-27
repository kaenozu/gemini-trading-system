"""
Comprehensive test suite for Execution Engines.
"""
import pytest
import pandas as pd
import numpy as np
from src.execution.engine import JPBacktestEngine, USBacktestEngine


class MockStrategy:
    """Mock strategy for testing."""
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(0, index=df.index)


class TestJPBacktestEngine:
    """Tests for JPBacktestEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = JPBacktestEngine(initial_capital=100000.0)
        self.engine.strategy = MockStrategy()

    def create_sample_data(self, days: int = 50) -> pd.DataFrame:
        """Create sample OHLCV data."""
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

    def test_initialization(self):
        """Test JP engine initialization."""
        assert self.engine.initial_capital == 100000.0
        assert self.engine.risk_manager.atr_multiplier == 2.0

    def test_reset(self):
        """Test reset method."""
        self.engine.cash = 50000.0
        self.engine.position = {'shares': 100}
        self.engine.trade_log = [{'Type': 'Buy'}]
        self.engine.equity_curve = [{'Date': '2024-01-01', 'Equity': 50000}]
        
        self.engine.reset()
        
        assert self.engine.cash == 100000.0
        assert self.engine.position is None
        assert self.engine.trade_log == []
        assert self.engine.equity_curve == []

    def test_run(self):
        """Test backtest run."""
        df = self.create_sample_data()
        benchmark_df = self.create_sample_data()
        
        result = self.engine.run(df, benchmark_df)
        
        assert isinstance(result, pd.DataFrame)
        assert len(self.engine.equity_curve) == len(df)

    def test_calculate_commission_tiered(self):
        """Test Japanese commission calculation (tiered)."""
        # Minimum fee
        assert self.engine._calculate_commission(50000) == 55.0
        
        # Tier 1: 0.099%
        assert self.engine._calculate_commission(100000) == pytest.approx(99.0, rel=0.01)
        
        # Tier 2: 0.088%
        assert self.engine._calculate_commission(200000) == pytest.approx(176.0, rel=0.01)
        
        # Tier 3: 0.077%
        assert self.engine._calculate_commission(500000) == pytest.approx(385.0, rel=0.01)
        
        # Tier 4: 0.066%
        assert self.engine._calculate_commission(1000000) == pytest.approx(660.0, rel=0.01)


class TestUSBacktestEngine:
    """Tests for USBacktestEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = USBacktestEngine(initial_capital=100000.0)
        self.engine.strategy = MockStrategy()

    def create_sample_data(self, days: int = 50) -> pd.DataFrame:
        """Create sample OHLCV data."""
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

    def test_initialization(self):
        """Test US engine initialization."""
        assert self.engine.initial_capital == 100000.0
        assert self.engine.risk_manager.atr_multiplier == 2.0

    def test_reset(self):
        """Test reset method."""
        self.engine.cash = 50000.0
        self.engine.position = {'shares': 100}
        self.engine.trade_log = [{'Type': 'Buy'}]
        self.engine.equity_curve = [{'Date': '2024-01-01', 'Equity': 50000}]
        
        self.engine.reset()
        
        assert self.engine.cash == 100000.0
        assert self.engine.position is None
        assert self.engine.trade_log == []
        assert self.engine.equity_curve == []

    def test_run(self):
        """Test backtest run."""
        df = self.create_sample_data()
        benchmark_df = self.create_sample_data()
        
        result = self.engine.run(df, benchmark_df)
        
        assert isinstance(result, pd.DataFrame)
        assert len(self.engine.equity_curve) == len(df)

    def test_calculate_commission(self):
        """Test US commission calculation (0.495%)."""
        assert self.engine._calculate_commission(100000) == pytest.approx(495.0, rel=0.01)
        assert self.engine._calculate_commission(50000) == pytest.approx(247.5, rel=0.01)
        assert self.engine._calculate_commission(10000) == pytest.approx(49.5, rel=0.01)
