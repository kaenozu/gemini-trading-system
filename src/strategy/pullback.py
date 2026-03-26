import pandas as pd

class PullbackStrategy:
    """
    SPEC v4 compliant Strategy: Pullback (Dip Buying).
    Goal: Higher win rate by buying dips in established uptrends.
    """
    def __init__(self, trend_sma: int = 100, dip_sma: int = 20, rsi_entry: int = 50, rsi_exit: int = 75):
        self.trend_sma = trend_sma
        self.dip_sma = dip_sma
        self.rsi_entry = rsi_entry
        self.rsi_exit = rsi_exit

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generates signals:
        - Buy: Close > SMA_200 (Uptrend) AND Close < SMA_20 (Dip) AND RSI < 40
        - Sell/Exit: RSI > 70 OR Close > SMA_20 (Mean Reversion)
        """
        signals = pd.Series(0, index=df.index)
        
        # Trend Condition
        uptrend = df['Close'] > df[f'SMA_{self.trend_sma}']
        
        # Dip Condition
        dip = (df['Close'] < df[f'SMA_{self.dip_sma}']) & (df['RSI_14'] < self.rsi_entry)
        
        # Exit Condition
        # We want to exit when price recovers to mean or gets overbought
        reversion = (df['Close'] > df[f'SMA_{self.dip_sma}']) | (df['RSI_14'] > self.rsi_exit)
        
        signals[uptrend & dip] = 1
        signals[reversion] = -1
        
        return signals
