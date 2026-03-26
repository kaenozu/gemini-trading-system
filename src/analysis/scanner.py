import pandas as pd
from src.data.loader import DataLoader
from src.features.engine import FeatureEngine
from src.strategy.pullback import PullbackStrategy
from src.filters.core import TradeFilter

from src.strategy.pullback import PullbackStrategy
from src.strategy.momentum import MomentumStrategy

class Scanner:
    def __init__(self, tickers: list, benchmark: str = "SPY"):
        self.tickers = tickers
        self.benchmark = benchmark
        self.loader = DataLoader()
        self.fe = FeatureEngine()
        self.jp_strategy = PullbackStrategy(trend_sma=200, dip_sma=20, rsi_entry=40, rsi_exit=70)
        self.us_strategy = MomentumStrategy(trend_sma=200, breakout_window=20)
        self.filter = TradeFilter()
        self.cached_results = []

    def scan(self) -> pd.DataFrame:
        results = []
        bench_df = self.loader.download(self.benchmark, start="2023-01-01")
        
        for ticker in self.tickers:
            try:
                df = self.loader.download(ticker, start="2023-01-01")
                if df.empty: continue
                
                df = self.fe.add_indicators(df)
                df = self.fe.add_regime(df, bench_df)
                
                # Select Strategy based on market
                strategy = self.jp_strategy if ticker.endswith('.T') else self.us_strategy
                signals = strategy.generate_signals(df)
                
                last_row = df.iloc[-1]
                last_signal = signals.iloc[-1]
                
                if last_signal == 1 and self.filter.can_trade(last_row):
                    # For BUY, calculate stops (Strategy-specific method)
                    # We need to handle different method names if they exist
                    stop, target = strategy.calculate_stops(last_row['Close'], last_row['ATR_14'])
                    results.append({
                        'Ticker': ticker, 'Signal': 'BUY', 'Price': float(last_row['Close']),
                        'Stop': float(stop), 'Target': float(target), 'RSI': float(last_row['RSI_14']),
                        'Strategy': strategy.__class__.__name__
                    })
                elif last_signal == -1:
                    results.append({
                        'Ticker': ticker, 'Signal': 'SELL/EXIT', 'Price': float(last_row['Close']),
                        'RSI': float(last_row['RSI_14']), 'Strategy': strategy.__class__.__name__
                    })
            except Exception as e:
                print(f"Error scanning {ticker}: {e}")
                
        self.cached_results = results
        return pd.DataFrame(results)
