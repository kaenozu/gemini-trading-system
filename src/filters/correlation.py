import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class CorrelationFilter:
    """
    SPEC v4 compliant Correlation Filter.
    Prevents holding highly correlated assets (e.g., two heavy tech stocks).
    """
    
    def __init__(self, threshold: float = 0.7):
        """
        Initialize correlation filter.
        
        Args:
            threshold: Correlation threshold (0.0-1.0). Assets above this are considered highly correlated.
        """
        self.threshold = threshold

    def is_highly_correlated(self, new_ticker: str, current_tickers: List[str], 
                             loader, data_cache: Optional[Dict[str, pd.DataFrame]] = None) -> bool:
        """
        Checks if the new ticker is highly correlated with any currently held ticker.
        Uses caching to avoid redundant disk I/O.
        
        Args:
            new_ticker: New ticker to check
            current_tickers: List of currently held tickers
            loader: DataLoader instance
            data_cache: Optional cache dictionary to store/reuse loaded data
            
        Returns:
            True if highly correlated, False otherwise
        """
        if not current_tickers:
            return False

        # Initialize cache if not provided
        if data_cache is None:
            data_cache = {}

        try:
            # Get latest 30 days of data for new ticker (with caching)
            if new_ticker not in data_cache:
                try:
                    data_cache[new_ticker] = loader.load(new_ticker)[['Close']].tail(30)
                except Exception as e:
                    logger.warning(f"Failed to load data for {new_ticker}: {e}")
                    return False  # Allow if data fetch fails
            new_df = data_cache[new_ticker]

            for ticker in current_tickers:
                # Load current ticker data (with caching)
                if ticker not in data_cache:
                    try:
                        data_cache[ticker] = loader.load(ticker)[['Close']].tail(30)
                    except Exception as e:
                        logger.warning(f"Failed to load data for {ticker}: {e}")
                        continue
                curr_df = data_cache[ticker]

                # Align data
                combined = pd.concat([new_df, curr_df], axis=1).dropna()
                if len(combined) < 20:
                    continue

                correlation = combined.corr().iloc[0, 1]
                if correlation >= self.threshold:
                    logger.info(f"{new_ticker} is highly correlated ({correlation:.2f}) with {ticker}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error in correlation check: {e}")
            return False  # Fallback to allowing if error occurs

        return False
