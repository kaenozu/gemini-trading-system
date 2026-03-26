import pandas as pd

class TradeFilter:
    """
    SPEC v4 compliant Filter.
    Strictly filters TRADES based on Regime, Liquidity, and Volatility.
    Goal: "Only trade in winning conditions."
    """
    def __init__(self, min_liquidity: float = 500_000, min_volatility_atr_pct: float = 0.005):
        """
        :param min_liquidity: Reduced to 500k from 1M.
        :param min_volatility_atr_pct: Reduced to 0.5% from 1%.
        """
        self.min_liquidity = min_liquidity
        self.min_volatility_atr_pct = min_volatility_atr_pct

    def check_regime(self, row: pd.Series) -> bool:
        """
        Checks if the market regime is favorable (Bullish).
        Assumes 'Regime' column exists (1=Bull, 0=Bear).
        """
        return row.get('Regime', 0) == 1

    def check_liquidity(self, row: pd.Series) -> bool:
        """
        Checks if the asset has enough liquidity.
        """
        # Close * Volume approximation for Dollar Volume
        # Ideally use Average Volume
        vol_sma = row.get('Vol_SMA_20', 0)
        close = row.get('Close', 0)
        dollar_vol = close * vol_sma
        return dollar_vol >= self.min_liquidity

    def check_volatility(self, row: pd.Series) -> bool:
        """
        Checks if the asset has enough volatility to be worth trading.
        """
        atr = row.get('ATR_14', 0)
        close = row.get('Close', 1) # Avoid div by zero
        if close == 0: return False
        
        return (atr / close) >= self.min_volatility_atr_pct

    def can_trade(self, row: pd.Series) -> bool:
        """
        Master filter check.
        Returns True if ALL conditions are met.
        """
        if not self.check_regime(row): return False
        if not self.check_liquidity(row): return False
        if not self.check_volatility(row): return False
        return True
