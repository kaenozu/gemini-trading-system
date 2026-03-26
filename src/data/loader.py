import os
import pandas as pd
import yfinance as yf
from pathlib import Path

class DataLoader:
    """
    SPEC v4 compliant Data Loader.
    Handles data fetching from yfinance and local parquet caching.
    Ensures data integrity (no future data in raw fetch, but that's handled by source usually).
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, ticker: str) -> Path:
        return self.data_dir / f"{ticker}.parquet"

    def download(self, ticker: str, start: str = "2000-01-01", end: str = None) -> pd.DataFrame:
        """
        Downloads data from yfinance and saves to local parquet.
        Handles both US and international tickers (e.g., 7203.T).
        """
        print(f"Downloading {ticker}...")
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        
        if df.empty:
            print(f"Warning: No data found for {ticker}")
            return df

        # Ensure index is DatetimeIndex and sorted
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Save to parquet
        file_path = self._get_file_path(ticker.replace('.', '_'))
        df.to_parquet(file_path)
        print(f"Saved {ticker} to {file_path}")
        return df

    def load(self, ticker: str) -> pd.DataFrame:
        """
        Loads data from local parquet storage.
        """
        file_path = self._get_file_path(ticker.replace('.', '_'))
        if not file_path.exists():
            # Try downloading if not exists
            return self.download(ticker)
        
        return pd.read_parquet(file_path)

    def update(self, ticker: str) -> pd.DataFrame:
        """
        Updates local data with new data from yfinance.
        (Simplified version: just re-downloads for now to ensure consistency)
        """
        return self.download(ticker)
