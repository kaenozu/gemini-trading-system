import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FeatureEngine:
    """
    SPEC v4 compliant Feature Engine.
    Calculates technical indicators ensuring NO future data leakage.
    Implemented in pure Pandas to avoid dependency issues.
    """
    
    def __init__(self):
        pass

    def _handle_multiindex(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle multiindex columns from yfinance.
        
        Args:
            df: DataFrame with potential multiindex columns
            
        Returns:
            DataFrame with flattened columns
        """
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten by joining levels with underscore
            df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]
        return df

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicators
        """
        # Ensure copy
        df = self._handle_multiindex(df.copy())

        # SMA
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_100'] = df['Close'].rolling(window=100).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # Volume SMA
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

        # RSI (14) - Wilder's Smoothing
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

        # Handle division by zero explicitly
        rs = avg_gain / avg_loss.replace(0, np.inf)
        df['RSI_14'] = (100 - (100 / (1 + rs))).replace([np.inf, -np.inf], 100).fillna(50)

        # ATR (14) - Wilder's Smoothing
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR_14'] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

        return df

    def add_regime(self, df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds Market Regime filter based on Benchmark.
        
        Args:
            df: DataFrame with ticker data
            benchmark_df: DataFrame with benchmark data (e.g., SPY)
            
        Returns:
            DataFrame with added 'Regime' column (1 = bullish, 0 = bearish)
        """
        df = self._handle_multiindex(df.copy())
        bench = self._handle_multiindex(benchmark_df.copy())

        # Calculate Benchmark SMA
        bench_sma200 = bench['Close'].rolling(window=200).mean()

        # Determine regime
        regime_series = (bench['Close'] > bench_sma200).astype(int)
        regime_series.name = 'Regime'

        # Join using left join on index
        df = df.join(regime_series, how='left')

        # Handle missing regime data
        if df['Regime'].isna().any():
            missing_count = df['Regime'].isna().sum()
            logger.warning(f"Missing regime data for {missing_count} dates, filling forward/backward")

        # Fill forward regime, fill NA with 0 (safe default)
        df['Regime'] = df['Regime'].ffill().bfill().fillna(0).astype(int)

        return df
