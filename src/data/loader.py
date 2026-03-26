import os
import pandas as pd
import yfinance as yf
from pathlib import Path
from src.data.models import OHLCVModel
from pydantic import ValidationError

class DataLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, ticker: str) -> Path:
        return self.data_dir / f"{ticker.replace('.', '_')}.parquet"

    def _validate_data(self, df: pd.DataFrame):
        """Validate dataframe rows using Pydantic model, ensuring float conversion."""
        for _, row in df.iterrows():
            try:
                # Extracting OHLCV values explicitly to avoid index/multiindex keys
                data = {
                    'Open': float(row['Open']),
                    'High': float(row['High']),
                    'Low': float(row['Low']),
                    'Close': float(row['Close']),
                    'Volume': float(row['Volume'])
                }
                OHLCVModel(**data)
            except (ValidationError, ValueError, TypeError) as e:
                raise ValueError(f"Data validation failed: {e}")

    def download(self, ticker: str, start: str = "2000-01-01", end: str = None) -> pd.DataFrame:
        print(f"Downloading {ticker}...")
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty: return df

        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Validation
        self._validate_data(df)
        
        file_path = self._get_file_path(ticker)
        df.to_parquet(file_path)
        return df

    def load(self, ticker: str) -> pd.DataFrame:
        file_path = self._get_file_path(ticker)
        if not file_path.exists():
            return self.download(ticker)
        
        df = pd.read_parquet(file_path)
        self._validate_data(df)
        return df

    def update(self, ticker: str) -> pd.DataFrame:
        return self.download(ticker)
