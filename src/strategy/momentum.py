import pandas as pd

class MomentumStrategy:
    """
    SPEC v4 compliant Strategy.
    Generates raw signals based on Momentum.
    Does NOT consider Risk or Filters (those are separate layers).
    """
    def __init__(self, sma_period: int = 20, rsi_period: int = 14, rsi_threshold: int = 50):
        self.sma_period = sma_period
        self.rsi_period = rsi_period
        self.rsi_threshold = rsi_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generates 1 (Buy), -1 (Sell), 0 (Neutral) signal.
        Logic:
        - Buy: Close > SMA_20 AND RSI > 50
        - Sell/Exit: Close < SMA_20
        """
        signals = pd.Series(0, index=df.index)
        
        # Vectorized conditions
        condition_buy = (df['Close'] > df[f'SMA_{self.sma_period}']) & (df[f'RSI_{self.rsi_period}'] > self.rsi_threshold)
        condition_exit = (df['Close'] < df[f'SMA_{self.sma_period}'])
        
        # Apply signals
        # Note: In a strict event-loop, we check this row by row. 
        # But for vectorized pre-calculation, we can set them here.
        signals[condition_buy] = 1
        signals[condition_exit] = -1 # Or 0 depending on implementation. Let's say -1 is explicit Sell signal.
        
        return signals
