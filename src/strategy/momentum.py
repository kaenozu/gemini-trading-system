import pandas as pd

class MomentumStrategy:
    """
    SPEC v4 compliant Trend Following Strategy.
    Enters on breakout of 20-day high in long-term uptrend.
    Exits when short-term trend breaks (SMA 20).
    """
    def __init__(self, trend_sma: int = 200, breakout_window: int = 20, exit_sma: int = 20):
        self.trend_sma = trend_sma
        self.breakout_window = breakout_window
        self.exit_sma = exit_sma

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        
        # 20-day High
        rolling_high = df['Close'].rolling(window=self.breakout_window).max().shift(1)
        
        # Entry: Long-term uptrend + New High
        condition_buy = (df['Close'] > df[f'SMA_{self.trend_sma}']) & (df['Close'] > rolling_high)
        
        # Exit: Below SMA 20
        condition_exit = (df['Close'] < df[f'SMA_{self.exit_sma}'])
        
        signals[condition_buy] = 1
        signals[condition_exit] = -1
        
        return signals

    def calculate_stops(self, entry_price: float, atr: float) -> tuple[float, float]:
        """
        Standard Risk calc for momentum.
        Target is 3x Risk (RR 3.0).
        """
        stop_price = entry_price - (atr * 2.0)
        target_price = entry_price + (atr * 6.0)
        return stop_price, target_price
