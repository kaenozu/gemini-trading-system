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
        """Validate dataframe using vectorized operations for performance."""
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # 必須カラムの存在チェック
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # 数値型への一括変換とバリデーション
        try:
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='raise')
        except (ValueError, TypeError) as e:
            raise ValueError(f"Data validation failed (non-numeric data): {e}")

        # 欠損値のチェック
        if df[required_columns].isnull().any().any():
            null_counts = df[required_columns].isnull().sum()
            raise ValueError(f"Data contains null values: {null_counts[null_counts > 0].to_dict()}")

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
