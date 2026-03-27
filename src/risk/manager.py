import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class RiskManager:
    """
    SPEC v4 compliant Risk Manager.
    Strictly controls POSITION SIZING and STOP LOSS.
    Goal: "Protect capital first."
    """
    
    def __init__(self, risk_per_trade_pct: float = 0.01, atr_multiplier: float = 1.5, risk_reward_ratio: float = 2.0):
        """
        Initialize Risk Manager.
        
        Args:
            risk_per_trade_pct: Risk per trade as a fraction of account (e.g., 0.01 = 1%)
            atr_multiplier: Multiplier for ATR-based stop loss
            risk_reward_ratio: Target Reward relative to Risk
        """
        self.risk_per_trade_pct = risk_per_trade_pct
        self.atr_multiplier = atr_multiplier
        self.risk_reward_ratio = risk_reward_ratio

    def update_trailing_stop(self, current_stop: float, current_price: float, atr: float, direction: str = 'long') -> float:
        """
        Updates the trailing stop price.
        For long positions, the stop only moves UP.
        
        Args:
            current_stop: Current stop price
            current_price: Current market price
            atr: Average True Range value
            direction: Position direction ('long' or 'short')
            
        Returns:
            Updated stop price
        """
        new_stop = current_stop
        stop_distance = atr * self.atr_multiplier

        if direction == 'long':
            # Calculate potential new stop based on current price
            potential_stop = current_price - stop_distance
            # Only move stop up
            new_stop = max(current_stop, potential_stop)
        else:
            # Calculate potential new stop based on current price
            potential_stop = current_price + stop_distance
            # Only move stop down
            new_stop = min(current_stop, potential_stop)

        return new_stop

    def calculate_stops(self, entry_price: float, atr: float, direction: str = 'long') -> Tuple[float, float]:
        """
        Calculates Stop Loss (SL) and Take Profit (TP) prices.
        
        Args:
            entry_price: Entry price for the position
            atr: Average True Range value
            direction: Position direction ('long' or 'short')
            
        Returns:
            Tuple of (stop_price, target_price)
        """
        stop_distance = atr * self.atr_multiplier

        if direction == 'long':
            stop_price = entry_price - stop_distance
            target_price = entry_price + (stop_distance * self.risk_reward_ratio)
        else:  # short
            stop_price = entry_price + stop_distance
            target_price = entry_price - (stop_distance * self.risk_reward_ratio)

        return stop_price, target_price

    def calculate_position_size(self, account_balance: float, entry_price: float, stop_price: float) -> int:
        """
        Calculates position size (number of shares) based on risk per trade.
        
        Formula: Shares = (Account * Risk%) / (Entry - Stop)
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price for the position
            stop_price: Stop loss price
            
        Returns:
            Number of shares to purchase (0 if invalid)
        """
        risk_amount = account_balance * self.risk_per_trade_pct
        price_risk_per_share = abs(entry_price - stop_price)

        if price_risk_per_share == 0:
            logger.warning(f"Zero price risk detected for entry={entry_price}, stop={stop_price}. Skipping position.")
            return 0

        shares = risk_amount / price_risk_per_share
        return int(shares)  # Round down to integer shares
