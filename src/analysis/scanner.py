from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence
from datetime import datetime

import pandas as pd
from src.data.loader import DataLoader
from src.features.engine import FeatureEngine
from src.filters.core import TradeFilter
from src.risk.manager import RiskManager
from src.analysis.strategy_selector import AutoStrategySelector
from src.strategy.base import BaseStrategy


def _generate_signals(strategy: BaseStrategy, df: pd.DataFrame, spy_df: pd.DataFrame) -> pd.Series:
    try:
        return strategy.generate_signals(df, spy_df)
    except TypeError:
        return strategy.generate_signals(df)


class Scanner:
    def __init__(
        self,
        tickers: list,
        benchmark: str = "SPY",
        auto_select_strategy: bool = True,
        *,
        lookback_days: int = 252,
        selector_initial_capital: float = 100_000.0,
        us_strategy_names: Optional[Sequence[str]] = None,
        jp_strategy_names: Optional[Sequence[str]] = None,
        selector_dd_penalty: float = 1.0,
        selector_walkforward_windows: int = 5,
        selector_walkforward_validation_days: int = 63,
        min_select_score: float = 0.005,
        switch_hysteresis: float = 0.01,
        start_date: str = "2023-01-01",
        refresh_data: bool = False,
        selection_log_path: str = "paper_trading_results/strategy_selection_log.csv",
    ):
        self.tickers = tickers
        self.benchmark = benchmark
        self.loader = DataLoader()
        self.fe = FeatureEngine()
        self.auto_select_strategy = auto_select_strategy
        self.strategy_selector = AutoStrategySelector(
            lookback_days=lookback_days,
            initial_capital=selector_initial_capital,
            us_candidate_names=us_strategy_names,
            jp_candidate_names=jp_strategy_names,
            dd_penalty=selector_dd_penalty,
            walkforward_windows=selector_walkforward_windows,
            walkforward_validation_days=selector_walkforward_validation_days,
        )
        self.min_select_score = float(min_select_score)
        self.switch_hysteresis = float(switch_hysteresis)
        self.start_date = start_date
        self.refresh_data = bool(refresh_data)
        self.selection_log_path = Path(selection_log_path)
        self._last_selected_strategy: dict[str, str] = {}
        self._last_selected_score: dict[str, float] = {}
        self.filter = TradeFilter()
        self.risk_manager = RiskManager(atr_multiplier=2.0)
        self.cached_results: List[dict] = []

    def _fetch_price(self, ticker: str) -> pd.DataFrame:
        """Load cached data when possible; optionally force refresh via download."""
        if self.refresh_data:
            return self.loader.download(ticker, start=self.start_date)

        load_fn = getattr(self.loader, "load", None)
        if callable(load_fn):
            try:
                return load_fn(ticker)
            except Exception:
                return self.loader.download(ticker, start=self.start_date)

        # Test stubs may expose only download().
        return self.loader.download(ticker, start=self.start_date)

    def _apply_hysteresis(
        self,
        ticker: str,
        candidate_scores: dict[str, float],
        selected_name: str,
        selected_score: float,
    ) -> tuple[str, float]:
        prev_name = self._last_selected_strategy.get(ticker)
        if not prev_name:
            return selected_name, selected_score
        prev_score = candidate_scores.get(prev_name, self._last_selected_score.get(ticker, float("-inf")))
        if pd.isna(prev_score) or pd.isna(selected_score):
            return selected_name, selected_score
        if selected_name != prev_name and (selected_score - prev_score) < self.switch_hysteresis:
            return prev_name, float(prev_score)
        return selected_name, selected_score

    def _append_selection_logs(self, rows: List[dict]) -> None:
        if not rows:
            return
        self.selection_log_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        write_header = not self.selection_log_path.exists()
        df.to_csv(self.selection_log_path, mode="a", header=write_header, index=False)

    def scan(self) -> pd.DataFrame:
        results = []
        selection_logs: List[dict] = []
        bench_df = self._fetch_price(self.benchmark)
        spy_features = self.fe.add_indicators(bench_df.copy())

        for ticker in self.tickers:
            try:
                df = self._fetch_price(ticker)
                if df.empty:
                    continue

                df = self.fe.add_indicators(df)
                df = self.fe.add_regime(df, bench_df)

                if self.auto_select_strategy:
                    candidate_scores = self.strategy_selector.score_candidates(ticker, df, spy_features)
                    strat_name, select_score = self.strategy_selector.select_best(
                        ticker, df, spy_features
                    )
                    strat_name, select_score = self._apply_hysteresis(
                        ticker,
                        candidate_scores,
                        strat_name,
                        select_score,
                    )
                else:
                    strat_name = self.strategy_selector.default_strategy_name(ticker)
                    select_score = float("nan")
                    candidate_scores = {strat_name: select_score}

                # しきい値未満は明示的に NoTrade を選択
                if not pd.isna(select_score) and select_score < self.min_select_score:
                    strat_name = "NoTradeStrategy"

                strategy = self.strategy_selector.build_strategy(ticker, strat_name)
                self._last_selected_strategy[ticker] = strat_name
                self._last_selected_score[ticker] = float(select_score) if not pd.isna(select_score) else float("nan")

                signals = _generate_signals(strategy, df, spy_features)

                last_row = df.iloc[-1]
                last_signal = signals.iloc[-1]
                signal_label = "HOLD"

                if last_signal == 1 and self.filter.can_trade(last_row):
                    stop, target = self.risk_manager.calculate_stops(
                        float(last_row["Close"]),
                        float(last_row["ATR_14"]),
                    )
                    results.append({
                        "Ticker": ticker,
                        "Signal": "BUY",
                        "Price": float(last_row["Close"]),
                        "Stop": float(stop),
                        "Target": float(target),
                        "RSI": float(last_row["RSI_14"]),
                        "Strategy": strategy.__class__.__name__,
                        "AutoSelectScore": select_score,
                    })
                    signal_label = "BUY"
                elif last_signal == -1:
                    results.append({
                        "Ticker": ticker,
                        "Signal": "SELL/EXIT",
                        "Price": float(last_row["Close"]),
                        "RSI": float(last_row["RSI_14"]),
                        "Strategy": strategy.__class__.__name__,
                        "AutoSelectScore": select_score,
                    })
                    signal_label = "SELL/EXIT"

                selection_logs.append({
                    "Timestamp": datetime.utcnow().isoformat(),
                    "Ticker": ticker,
                    "SelectedStrategy": strat_name,
                    "SelectedScore": select_score,
                    "MinSelectScore": self.min_select_score,
                    "AppliedSignal": signal_label,
                    "Candidates": "|".join(f"{k}:{v:.6f}" for k, v in candidate_scores.items() if not pd.isna(v)),
                })
            except Exception as e:
                print(f"Error scanning {ticker}: {e}")

        self._append_selection_logs(selection_logs)
        self.cached_results = results
        return pd.DataFrame(results)
