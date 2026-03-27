import pandas as pd
from typing import Tuple


class MomentumStrategy:
    """
    SPEC v4 compliant Trend Following Strategy.
    Enters on breakout of breakout_window-day high in long-term uptrend.
    Exits when short-term trend breaks (SMA exit_sma).
    """
    
    def __init__(self, trend_sma: int = 200, breakout_window: int = 20, exit_sma: int = 20,
                 stop_atr_mult: float = 2.0, target_atr_mult: float = 6.0):
        """
        Initialize Momentum Strategy.
        
        Args:
            trend_sma: SMA period for trend detection (default: 200)
            breakout_window: Window for breakout high (default: 20)
            exit_sma: SMA period for exit signal (default: 20)
            stop_atr_mult: ATR multiplier for stop loss (default: 2.0)
            target_atr_mult: ATR multiplier for take profit (default: 6.0)
        """
        self.trend_sma = trend_sma
        self.breakout_window = breakout_window
        self.exit_sma = exit_sma
        self.stop_atr_mult = stop_atr_mult
        self.target_atr_mult = target_atr_mult

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Entry: Long-term uptrend + New breakout high
        Exit: Price falls below exit_sma SMA
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            Series with signals (1 = Buy, -1 = Sell, 0 = Hold)
        """
        signals = pd.Series(0, index=df.index)

        # 20-day High (shifted to avoid lookahead bias)
        rolling_high = df['Close'].rolling(window=self.breakout_window).max().shift(1)

        # Entry: Long-term uptrend + New High
        condition_buy = (df['Close'] > df[f'SMA_{self.trend_sma}']) & (df['Close'] > rolling_high)

        # Exit: Below SMA exit_sma
        condition_exit = (df['Close'] < df[f'SMA_{self.exit_sma}'])

        signals[condition_buy] = 1
        signals[condition_exit] = -1

        return signals

    def calculate_stops(self, entry_price: float, atr: float) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels.
        Target is 3x Risk (RR 3.0).
        
        Args:
            entry_price: Entry price for the position
            atr: Average True Range value
            
        Returns:
            Tuple of (stop_price, target_price)
        """
        stop_price = entry_price - (atr * self.stop_atr_mult)
        target_price = entry_price + (atr * self.target_atr_mult)
        return stop_price, target_price
