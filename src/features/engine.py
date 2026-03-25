import pandas as pd
import numpy as np

class FeatureEngine:
    """
    SPEC v4 compliant Feature Engine.
    Calculates technical indicators ensuring NO future data leakage.
    Implemented in pure Pandas to avoid dependency issues.
    """
    def __init__(self):
        pass

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds standard indicators for MVP strategy:
        - SMA (20, 50, 200)
        - RSI (14)
        - ATR (14)
        """
        # Ensure copy
        df = df.copy()

        # SMA
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Volume SMA
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

        # RSI (14) - Wilder's Smoothing
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        df['RSI_14'] = 100 - (100 / (1 + rs))

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
        """
        bench = benchmark_df.copy()
        bench['Bench_SMA_200'] = bench['Close'].rolling(window=200).mean()
        
        # Determine regime: 1 (Bull), 0 (Bear/Neutral)
        bench['Regime'] = (bench['Close'] > bench['Bench_SMA_200']).astype(int)
        
        # Merge regime back to main dataframe based on Date index
        # We assume indices are DatetimeIndex and aligned (or close enough)
        # Using join is safer
        if 'Regime' in df.columns:
            df = df.drop(columns=['Regime'])
            
        df = df.join(bench[['Regime']], how='left')
        
        # Fill NaN
        df['Regime'] = df['Regime'].fillna(0).astype(int)
        
        return df
