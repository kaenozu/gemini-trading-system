import pandas as pd
from src.data.loader import DataLoader
from src.features.engine import FeatureEngine
from src.strategy.pullback import PullbackStrategy
from src.filters.core import TradeFilter

class Scanner:
    """
    SPEC v4 Actionable Scanner.
    Scans current market for buy/sell opportunities.
    """
    def __init__(self, tickers: list, benchmark: str = "SPY"):
        self.tickers = tickers
        self.benchmark = benchmark
        self.loader = DataLoader()
        self.fe = FeatureEngine()
        self.strategy = PullbackStrategy(trend_sma=200, dip_sma=20, rsi_entry=35)
        self.filter = TradeFilter()

    def scan(self) -> pd.DataFrame:
        """
        Scans all tickers and identifies candidates for tomorrow.
        """
        results = []
        print(f"Scanning {len(self.tickers)} tickers for opportunities...")
        
        # Get latest benchmark
        bench_df = self.loader.download(self.benchmark, start="2023-01-01")
        
        for ticker in self.tickers:
            try:
                # Get latest data
                df = self.loader.download(ticker, start="2023-01-01")
                if df.empty: continue
                
                # Apply Engine
                df = self.fe.add_indicators(df)
                df = self.fe.add_regime(df, bench_df)
                
                # Debugging
                print(f"DEBUG: type(df)={type(df)}")
                
                # Get Signals
                # Using the instance method explicitly
                signals = self.strategy.generate_signals(df)
                
                # Check last row (Today)
                last_row = df.iloc[-1]
                
                # Ensure signals is a Series (or similar indexable object)
                if isinstance(signals, pd.Series):
                    last_signal = signals.iloc[-1]
                else:
                    last_signal = signals[-1]
                
                if last_signal == 1: # Buy Signal
                    # Check Filter
                    if self.filter.can_trade(last_row):
                        results.append({
                            'Ticker': ticker,
                            'Signal': 'BUY',
                            'Price': last_row['Close'],
                            'RSI': last_row['RSI_14'],
                            'Regime': 'Bullish'
                        })
                elif last_signal == -1:
                    results.append({
                        'Ticker': ticker,
                        'Signal': 'SELL/EXIT',
                        'Price': last_row['Close'],
                        'RSI': last_row['RSI_14']
                    })
            except Exception as e:
                print(f"Error scanning {ticker}: {e}")
                
        return pd.DataFrame(results)
