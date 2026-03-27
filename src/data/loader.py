import os
import pandas as pd
import yfinance as yf
from pathlib import Path
from src.data.models import OHLCVModel
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Data loader with vectorized validation for performance."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, ticker: str) -> Path:
        """Get the file path for a ticker's parquet file."""
        return self.data_dir / f"{ticker.replace('.', '_')}.parquet"

    def _validate_data(self, df: pd.DataFrame):
        """
        Vectorized data validation for performance.
        
        Args:
            df: DataFrame with OHLCV data
            
        Raises:
            ValueError: If data validation fails
        """
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check required columns exist
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
            if df[col].isna().any():
                raise ValueError(f"NaN values found in {col}")
            if (df[col] < 0).any():
                raise ValueError(f"Negative values found in {col}")
        
        # Check OHLCV logic relationships
        if (df['High'] < df['Low']).any():
            raise ValueError("High < Low detected")
        if (df['High'] < df['Open']).any():
            raise ValueError("High < Open detected")
        if (df['High'] < df['Close']).any():
            raise ValueError("High < Close detected")
        if (df['Low'] > df['Open']).any():
            raise ValueError("Low > Open detected")
        if (df['Low'] > df['Close']).any():
            raise ValueError("Low > Close detected")

    def download(self, ticker: str, start: str = "2000-01-01", end: str = None) -> pd.DataFrame:
        """
        Download data from Yahoo Finance.
        
        Args:
            ticker: Stock ticker symbol
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Downloading {ticker} from {start} to {end or 'present'}...")
        print(f"Downloading {ticker}...")
        
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            logger.warning(f"No data downloaded for {ticker}")
            return df

        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        # Validation
        try:
            self._validate_data(df)
        except ValueError as e:
            logger.error(f"Data validation failed for {ticker}: {e}")
            raise

        file_path = self._get_file_path(ticker)
        df.to_parquet(file_path)
        logger.info(f"Saved {ticker} to {file_path}")
        return df

    def load(self, ticker: str) -> pd.DataFrame:
        """
        Load data from local parquet file.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DataFrame with OHLCV data
        """
        file_path = self._get_file_path(ticker)
        if not file_path.exists():
            logger.info(f"Local data not found for {ticker}, downloading...")
            return self.download(ticker)

        df = pd.read_parquet(file_path)
        self._validate_data(df)
        return df

    def update(self, ticker: str) -> pd.DataFrame:
        """Update data by re-downloading."""
        return self.download(ticker)
