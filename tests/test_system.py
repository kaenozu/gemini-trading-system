"""
System integration tests.
"""
import pytest
import pandas as pd
import numpy as np
from src.risk.manager import RiskManager
from src.features.engine import FeatureEngine
from src.execution.engine import USBacktestEngine


class _StrategyStub:
    """Mock strategy for testing."""
    def generate_signals(self, df: pd.DataFrame):
        return pd.Series(0, index=df.index)


def test_risk_manager_position_sizing():
    """Test risk manager position sizing calculation."""
    manager = RiskManager(risk_per_trade_pct=0.01)
    shares = manager.calculate_position_size(100000, 100, 90)
    
    # Risk amount = 100000 * 0.01 = 1000
    # Price risk = 100 - 90 = 10
    # Shares = 1000 / 10 = 100
    assert shares == 100


def test_feature_engine_rsi():
    """Test RSI calculation in feature engine."""
    fe = FeatureEngine()
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    df = pd.DataFrame({
        'Open': close,
        'High': close * 1.02,
        'Low': close * 0.98,
        'Close': close,
        'Volume': [1000000] * 100
    }, index=dates)
    
    df_with_ind = fe.add_indicators(df)
    assert 'RSI_14' in df_with_ind.columns
    assert not df_with_ind['RSI_14'].isna().iloc[-1]


def test_backtest_engine_reset_clears_state():
    """Test that reset method clears all state."""
    engine = USBacktestEngine(initial_capital=1000.0)
    engine.cash = 500.0
    engine.position = {'shares': 10}
    engine.trade_log = [{'Type': 'Buy'}]
    engine.equity_curve = [{'Date': '2026-01-01', 'Equity': 500}]

    engine.reset()

    assert engine.cash == 1000.0
    assert engine.position is None
    assert engine.trade_log == []
    assert engine.equity_curve == []


def test_backtest_engine_run_returns_trade_log():
    """Test that run method returns a trade log DataFrame."""
    engine = USBacktestEngine(initial_capital=100000.0)
    
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(50) * 0.5)
    
    df = pd.DataFrame({
        'Open': close,
        'High': close * 1.02,
        'Low': close * 0.98,
        'Close': close,
        'Volume': [1000000] * 50
    }, index=dates)
    
    benchmark_df = df.copy()
    
    result = engine.run(df, benchmark_df)
    
    assert isinstance(result, pd.DataFrame)
    assert len(engine.equity_curve) == 50


def test_backtest_engine_commission_calculation():
    """Test commission calculation in US engine."""
    engine = USBacktestEngine(initial_capital=100000.0)
    
    # US commission is 0.495%
    assert engine._calculate_commission(100000) == pytest.approx(495.0, rel=0.01)
