import numpy as np

class RiskManager:
    """
    SPEC v4 compliant Risk Manager.
    Strictly controls POSITION SIZING and STOP LOSS.
    Goal: "Protect capital first."
    """
    def __init__(self, risk_per_trade_pct: float = 0.01, atr_multiplier: float = 2.0, risk_reward_ratio: float = 2.0):
        """
        :param risk_per_trade_pct: Risk per trade as a fraction of account (e.g., 0.01 = 1%).
        :param atr_multiplier: Multiplier for ATR-based stop loss.
        :param risk_reward_ratio: Target Reward relative to Risk.
        """
        self.risk_per_trade_pct = risk_per_trade_pct
        self.atr_multiplier = atr_multiplier
        self.risk_reward_ratio = risk_reward_ratio

    def calculate_stops(self, entry_price: float, atr: float, direction: str = 'long') -> tuple[float, float]:
        """
        Calculates Stop Loss (SL) and Take Profit (TP) prices.
        Returns (stop_price, target_price).
        """
        stop_distance = atr * self.atr_multiplier
        
        if direction == 'long':
            stop_price = entry_price - stop_distance
            target_price = entry_price + (stop_distance * self.risk_reward_ratio)
        else: # short
            stop_price = entry_price + stop_distance
            target_price = entry_price - (stop_distance * self.risk_reward_ratio)
            
        return stop_price, target_price

    def calculate_position_size(self, account_balance: float, entry_price: float, stop_price: float) -> int:
        """
        Calculates position size (number of shares) based on risk per trade.
        Formula: Shares = (Account * Risk%) / (Entry - Stop)
        """
        risk_amount = account_balance * self.risk_per_trade_pct
        price_risk_per_share = abs(entry_price - stop_price)
        
        if price_risk_per_share == 0:
            return 0
            
        shares = risk_amount / price_risk_per_share
        return int(shares) # Round down to integer shares
