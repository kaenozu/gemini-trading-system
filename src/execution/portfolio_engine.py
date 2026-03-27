import pandas as pd
import numpy as np
from src.execution.engine import JPBacktestEngine, USBacktestEngine
from src.data.loader import DataLoader
from src.filters.correlation import CorrelationFilter
import logging

logger = logging.getLogger(__name__)


class PortfolioEngine:
    """
    SPEC v4 compliant Portfolio Engine.
    Runs backtests across multiple tickers and aggregates results.
    """
    def __init__(self, initial_capital: float = 100000.0, max_positions: int = 5, sector_limit: int = 2):
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.sector_limit = sector_limit
        self.loader = DataLoader()
        self.results = {}
        self.corr_filter = CorrelationFilter(threshold=0.7)
        # Simple sector mapping for the defined universe
        self.sectors = {
            "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "AMZN": "Consumer", "NVDA": "Tech",
            "META": "Tech", "TSLA": "Consumer", "AVGO": "Tech", "ADBE": "Tech", "AMD": "Tech",
            "7203.T": "Auto", "6758.T": "Tech", "9984.T": "Finance", "6861.T": "Tech", "8035.T": "Tech",
            "6981.T": "Tech", "6501.T": "Industrial", "6098.T": "Finance", "9432.T": "Comms", "8306.T": "Finance",
            "7974.T": "Consumer", "4063.T": "Materials", "6702.T": "Tech", "6367.T": "Industrial", "6723.T": "Tech",
            "9983.T": "Consumer", "7741.T": "Tech", "4568.T": "Healthcare", "6594.T": "Industrial", "6146.T": "Industrial"
        }

    def run_multi(self, tickers: list, benchmark: str, start: str, end: str):
        all_trade_logs = []
        active_sectors = {}  # Tracks sector exposure
        held_tickers = []
        data_cache = {}  # Cache for correlation filter

        logger.info(f"Starting Portfolio Backtest for {len(tickers)} tickers (Sector Limit: {self.sector_limit})...")
        print(f"Starting Portfolio Backtest for {len(tickers)} tickers (Sector Limit: {self.sector_limit})...")
        
        # Load benchmark data with proper error handling
        try:
            bench_df = self.loader.load(benchmark) if self.loader._get_file_path(benchmark).exists() else self.loader.download(benchmark, start=start, end=end)
        except Exception as e:
            logger.error(f"Failed to load benchmark data for {benchmark}: {e}")
            return pd.DataFrame(), pd.DataFrame()

        for ticker in tickers:
            print(f"  Testing {ticker}...", end="\r")
            capital_per_ticker = self.initial_capital / self.max_positions

            # Filters
            sector = self.sectors.get(ticker, "Other")
            if active_sectors.get(sector, 0) >= self.sector_limit:
                continue
            if self.corr_filter.is_highly_correlated(ticker, held_tickers, self.loader, data_cache):
                continue

            engine = JPBacktestEngine(initial_capital=capital_per_ticker) if ticker.endswith('.T') else USBacktestEngine(initial_capital=capital_per_ticker)

            try:
                df = self.loader.load(ticker)
            except FileNotFoundError:
                logger.info(f"Local data not found for {ticker}, downloading...")
                try:
                    df = self.loader.download(ticker, start=start, end=end)
                except Exception as e:
                    logger.error(f"Failed to download {ticker}: {e}")
                    continue
            except Exception as e:
                logger.error(f"Failed to load {ticker}: {e}")
                continue

            if df.empty:
                logger.warning(f"Empty data for {ticker}, skipping")
                continue

            trade_log = engine.run(df, bench_df)

            if not trade_log.empty:
                active_sectors[sector] = active_sectors.get(sector, 0) + 1
                held_tickers.append(ticker)
                trade_log['Ticker'] = ticker
                all_trade_logs.append(trade_log)
                self.results[ticker] = {'engine': engine, 'log': trade_log}

        if not all_trade_logs:
            logger.warning("No trades executed across all tickers")
            return pd.DataFrame(), pd.DataFrame()

        portfolio_log = pd.concat(all_trade_logs).sort_values('Date')

        equity_frames = []
        for ticker, data in self.results.items():
            eq = pd.DataFrame(data['engine'].equity_curve).set_index('Date')
            equity_frames.append(eq['Equity'].rename(ticker))

        portfolio_equity = pd.concat(equity_frames, axis=1).ffill().fillna(capital_per_ticker)
        total_equity = portfolio_equity.sum(axis=1)

        return portfolio_log, total_equity
