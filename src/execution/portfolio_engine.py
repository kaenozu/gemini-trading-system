import pandas as pd
import numpy as np
from src.execution.engine import BacktestEngine
from src.data.loader import DataLoader

class PortfolioEngine:
    """
    SPEC v4 compliant Portfolio Engine.
    Runs backtests across multiple tickers and aggregates results.
    """
    def __init__(self, initial_capital: float = 100000.0, max_positions: int = 5):
        """
        :param initial_capital: Total capital for the portfolio.
        :param max_positions: Maximum number of simultaneous positions (SPEC v4 7.2).
        """
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.loader = DataLoader()
        self.results = {}

    def run_multi(self, tickers: list, benchmark: str, start: str, end: str):
        """
        Runs backtests for each ticker and stores results.
        Note: This is a simplified aggregate. A true cross-sectional backtest 
        would manage cash daily across all tickers.
        """
        all_trade_logs = []
        
        print(f"Starting Portfolio Backtest for {len(tickers)} tickers...")
        
        # Get Benchmark first
        try:
            bench_df = self.loader.load(benchmark)
        except:
            bench_df = self.loader.download(benchmark, start=start, end=end)

        for ticker in tickers:
            print(f"  Testing {ticker}...", end="\r")
            # Individual engine with a portion of total capital for simpler aggregation
            # Or use total capital to see capacity. Let's use total/max_positions per ticker.
            capital_per_ticker = self.initial_capital / self.max_positions
            engine = BacktestEngine(initial_capital=capital_per_ticker)
            
            try:
                df = self.loader.load(ticker)
            except:
                df = self.loader.download(ticker, start=start, end=end)
                
            trade_log = engine.run(df, bench_df)
            
            if not trade_log.empty:
                trade_log['Ticker'] = ticker
                all_trade_logs.append(trade_log)
                self.results[ticker] = {
                    'engine': engine,
                    'log': trade_log
                }

        if not all_trade_logs:
            return pd.DataFrame(), pd.DataFrame()

        # Combine all trade logs
        portfolio_log = pd.concat(all_trade_logs).sort_values('Date')
        
        # Aggregate Equity (Simplified: sum of cash + market value)
        # For a more accurate view, we align all equity curves by Date
        equity_frames = []
        for ticker, data in self.results.items():
            eq = pd.DataFrame(data['engine'].equity_curve)
            eq.set_index('Date', inplace=True)
            equity_frames.append(eq['Equity'].rename(ticker))
            
        portfolio_equity = pd.concat(equity_frames, axis=1).fillna(method='ffill').fillna(capital_per_ticker)
        # Total Equity = Sum of all allocated capital + PnL from each
        total_equity = portfolio_equity.sum(axis=1)
        
        return portfolio_log, total_equity
