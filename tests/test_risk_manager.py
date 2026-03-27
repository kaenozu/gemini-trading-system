"""
Comprehensive test suite for the Risk Manager.
"""
import pytest
from src.risk.manager import RiskManager


class TestRiskManager:
    """Tests for RiskManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.risk_manager = RiskManager(
            risk_per_trade_pct=0.01,
            atr_multiplier=2.0,
            risk_reward_ratio=3.0
        )

    def test_initialization(self):
        """Test RiskManager initialization."""
        assert self.risk_manager.risk_per_trade_pct == 0.01
        assert self.risk_manager.atr_multiplier == 2.0
        assert self.risk_manager.risk_reward_ratio == 3.0

    def test_calculate_stops_long_position(self):
        """Test stop and target calculation for long positions."""
        entry_price = 100.0
        atr = 5.0
        
        stop, target = self.risk_manager.calculate_stops(entry_price, atr, 'long')
        
        # stop_distance = 5 * 2 = 10
        # stop = 100 - 10 = 90
        # target = 100 + (10 * 3) = 130
        assert stop == 90.0
        assert target == 130.0

    def test_calculate_stops_short_position(self):
        """Test stop and target calculation for short positions."""
        entry_price = 100.0
        atr = 5.0
        
        stop, target = self.risk_manager.calculate_stops(entry_price, atr, 'short')
        
        # stop_distance = 5 * 2 = 10
        # stop = 100 + 10 = 110
        # target = 100 - (10 * 3) = 70
        assert stop == 110.0
        assert target == 70.0

    def test_calculate_position_size_normal(self):
        """Test position size calculation with valid inputs."""
        account_balance = 100000.0
        entry_price = 100.0
        stop_price = 90.0
        
        shares = self.risk_manager.calculate_position_size(
            account_balance, entry_price, stop_price
        )
        
        # Risk amount = 100000 * 0.01 = 1000
        # Price risk = 100 - 90 = 10
        # Shares = 1000 / 10 = 100
        assert shares == 100

    def test_calculate_position_size_zero_risk(self):
        """Test position size when stop equals entry (zero risk)."""
        account_balance = 100000.0
        entry_price = 100.0
        stop_price = 100.0  # Same as entry
        
        shares = self.risk_manager.calculate_position_size(
            account_balance, entry_price, stop_price
        )
        
        assert shares == 0

    def test_update_trailing_stop_long_moves_up(self):
        """Test trailing stop only moves up for long positions."""
        current_stop = 90.0
        current_price = 100.0
        atr = 5.0
        
        new_stop = self.risk_manager.update_trailing_stop(
            current_stop, current_price, atr, 'long'
        )
        
        # Stop distance = 5 * 2 = 10
        # Potential stop = 100 - 10 = 90
        # Should stay at 90 (not move down)
        assert new_stop == 90.0

    def test_update_trailing_stop_long_moves_higher(self):
        """Test trailing stop moves up when price increases."""
        current_stop = 90.0
        current_price = 110.0  # Price moved up
        atr = 5.0
        
        new_stop = self.risk_manager.update_trailing_stop(
            current_stop, current_price, atr, 'long'
        )
        
        # Stop distance = 5 * 2 = 10
        # Potential stop = 110 - 10 = 100
        # Should move up to 100
        assert new_stop == 100.0

    def test_update_trailing_stop_short_moves_down(self):
        """Test trailing stop only moves down for short positions."""
        current_stop = 110.0
        current_price = 100.0
        atr = 5.0
        
        new_stop = self.risk_manager.update_trailing_stop(
            current_stop, current_price, atr, 'short'
        )
        
        # Stop distance = 5 * 2 = 10
        # Potential stop = 100 + 10 = 110
        # Should stay at 110 (not move up)
        assert new_stop == 110.0
