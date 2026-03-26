import pandas as pd
import numpy as np

class CorrelationFilter:
    """
    SPEC v4 compliant Correlation Filter.
    Prevents holding highly correlated assets (e.g., two heavy tech stocks).
    """
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    def is_highly_correlated(self, new_ticker: str, current_tickers: list, loader) -> bool:
        """
        Checks if the new ticker is highly correlated with any currently held ticker.
        """
        if not current_tickers:
            return False
            
        try:
            # Get latest 30 days of data for new ticker
            new_df = loader.load(new_ticker)[['Close']].tail(30)
            
            for ticker in current_tickers:
                curr_df = loader.load(ticker)[['Close']].tail(30)
                
                # Align data
                combined = pd.concat([new_df, curr_df], axis=1).dropna()
                if len(combined) < 20: continue
                
                correlation = combined.corr().iloc[0, 1]
                if correlation >= self.threshold:
                    return True
        except Exception:
            return False # Fallback to allowing if data fetch fails
            
        return False
