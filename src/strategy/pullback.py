import pandas as pd
from typing import Tuple


class PullbackStrategy:
    """
    SPEC v4 compliant Strategy: Pullback (Dip Buying).
    Goal: Higher win rate by buying dips in established uptrends.
    """
    
    def __init__(self, trend_sma: int = 100, dip_sma: int = 20, 
                 rsi_entry: int = 50, rsi_exit: int = 75,
                 stop_atr_mult: float = 2.0, target_atr_mult: float = 6.0):
        """
        Initialize Pullback Strategy.
        
        Args:
            trend_sma: SMA period for trend detection (default: 100)
            dip_sma: SMA period for dip detection (default: 20)
            rsi_entry: RSI threshold for entry (default: 50)
            rsi_exit: RSI threshold for exit (default: 75)
            stop_atr_mult: ATR multiplier for stop loss (default: 2.0)
            target_atr_mult: ATR multiplier for take profit (default: 6.0)
        """
        self.trend_sma = trend_sma
        self.dip_sma = dip_sma
        self.rsi_entry = rsi_entry
        self.rsi_exit = rsi_exit
        self.stop_atr_mult = stop_atr_mult
        self.target_atr_mult = target_atr_mult

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generates signals:
        - Buy: Close > SMA_trend (Uptrend) AND Close < SMA_dip (Dip) AND RSI < rsi_entry
        - Sell/Exit: RSI > rsi_exit OR Close > SMA_dip (Mean Reversion)
        
        Args:
            df: DataFrame with OHLCV and indicators
            
        Returns:
            Series with signals (1 = Buy, -1 = Sell, 0 = Hold)
        """
        signals = pd.Series(0, index=df.index)

        # Trend Condition
        uptrend = df['Close'] > df[f'SMA_{self.trend_sma}']

        # Dip Condition
        dip = (df['Close'] < df[f'SMA_{self.dip_sma}']) & (df['RSI_14'] < self.rsi_entry)

        # Exit Condition
        # Exit when price recovers to mean or gets overbought
        reversion = (df['Close'] > df[f'SMA_{self.dip_sma}']) | (df['RSI_14'] > self.rsi_exit)

        signals[uptrend & dip] = 1
        signals[reversion] = -1

        return signals

    def calculate_stops(self, entry_price: float, atr: float) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels.
        
        Args:
            entry_price: Entry price for the position
            atr: Average True Range value
            
        Returns:
            Tuple of (stop_price, target_price)
        """
        stop_price = entry_price - (atr * self.stop_atr_mult)
        target_price = entry_price + (atr * self.target_atr_mult)
        return stop_price, target_price
