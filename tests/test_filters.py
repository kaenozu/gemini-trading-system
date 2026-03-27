"""
Comprehensive test suite for Trade Filters.
"""
import pytest
import pandas as pd
from src.filters.core import TradeFilter


class TestTradeFilter:
    """Tests for TradeFilter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.filter = TradeFilter(
            min_liquidity=500000,
            min_volatility_atr_pct=0.005
        )

    def create_sample_row(self, **kwargs) -> pd.Series:
        """Create a sample row for testing."""
        defaults = {
            'Regime': 1,
            'Close': 100.0,
            'Vol_SMA_20': 5000000,
            'ATR_14': 2.0,
        }
        defaults.update(kwargs)
        return pd.Series(defaults)

    def test_can_trade_all_pass(self):
        """Test can_trade when all conditions pass."""
        row = self.create_sample_row()
        can_trade, reason = self.filter.can_trade(row)
        
        assert can_trade is True
        assert reason == "PASS"

    def test_can_trade_regime_fail(self):
        """Test can_trade when regime check fails."""
        row = self.create_sample_row(Regime=0)
        can_trade, reason = self.filter.can_trade(row)
        
        assert can_trade is False
        assert reason == "Regime"

    def test_can_trade_liquidity_fail(self):
        """Test can_trade when liquidity is too low."""
        row = self.create_sample_row(Vol_SMA_20=100000, Close=1.0)
        can_trade, reason = self.filter.can_trade(row)
        
        assert can_trade is False
        assert reason == "Liquidity"

    def test_can_trade_volatility_fail(self):
        """Test can_trade when volatility is too low."""
        row = self.create_sample_row(ATR_14=0.1, Close=100.0)
        can_trade, reason = self.filter.can_trade(row)
        
        assert can_trade is False
        assert reason == "Volatility"

    def test_check_regime(self):
        """Test regime check."""
        assert self.filter.check_regime({'Regime': 1}) is True
        assert self.filter.check_regime({'Regime': 0}) is False

    def test_check_liquidity_pass(self):
        """Test liquidity check passes."""
        row = {'Close': 100.0, 'Vol_SMA_20': 5000000}
        assert self.filter.check_liquidity(row) is True

    def test_check_liquidity_fail(self):
        """Test liquidity check fails."""
        row = {'Close': 1.0, 'Vol_SMA_20': 100000}
        assert self.filter.check_liquidity(row) is False

    def test_check_volatility_pass(self):
        """Test volatility check passes."""
        row = {'Close': 100.0, 'ATR_14': 2.0}
        assert self.filter.check_volatility(row) is True

    def test_check_volatility_fail(self):
        """Test volatility check fails."""
        row = {'Close': 100.0, 'ATR_14': 0.1}
        assert self.filter.check_volatility(row) is False
