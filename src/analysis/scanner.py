import pandas as pd
from src.data.loader import DataLoader
from src.features.engine import FeatureEngine
from src.strategy.pullback import PullbackStrategy
from src.strategy.momentum import MomentumStrategy
from src.filters.core import TradeFilter
import logging

logger = logging.getLogger(__name__)


class Scanner:
    """Market scanner for identifying trading opportunities."""
    
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
        """
        Scan all tickers for trading signals.
        
        Returns:
            DataFrame with trading signals
        """
        results = []
        logger.info(f"Starting market scan for {len(self.tickers)} tickers...")
        bench_df = self.loader.download(self.benchmark, start="2023-01-01")

        for ticker in self.tickers:
            try:
                df = self.loader.download(ticker, start="2023-01-01")
                if df.empty:
                    logger.warning(f"Empty data for {ticker}, skipping")
                    continue

                df = self.fe.add_indicators(df)
                df = self.fe.add_regime(df, bench_df)

                # Select strategy based on market
                strategy = self.jp_strategy if ticker.endswith('.T') else self.us_strategy
                signals = strategy.generate_signals(df)

                last_row = df.iloc[-1]
                last_signal = signals.iloc[-1]

                if last_signal == 1 and self.filter.can_trade(last_row):
                    # For BUY, calculate stops (Strategy-specific method)
                    stop, target = strategy.calculate_stops(last_row['Close'], last_row['ATR_14'])
                    results.append({
                        'Ticker': ticker, 'Signal': 'BUY', 'Price': float(last_row['Close']),
                        'Stop': float(stop), 'Target': float(target), 'RSI': float(last_row['RSI_14']),
                        'Strategy': strategy.__class__.__name__
                    })
                    logger.info(f"BUY signal for {ticker} at {last_row['Close']}")
                elif last_signal == -1:
                    results.append({
                        'Ticker': ticker, 'Signal': 'SELL/EXIT', 'Price': float(last_row['Close']),
                        'RSI': float(last_row['RSI_14']), 'Strategy': strategy.__class__.__name__
                    })
                    logger.info(f"SELL/EXIT signal for {ticker} at {last_row['Close']}")
            except Exception as e:
                logger.error(f"Error scanning {ticker}: {e}")
                print(f"Error scanning {ticker}: {e}")

        self.cached_results = results
        logger.info(f"Scan complete. Found {len(results)} signals.")
        return pd.DataFrame(results)
