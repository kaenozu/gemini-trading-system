import pandas as pd
from abc import ABC, abstractmethod
from operator import itemgetter
from typing import Optional

from src.features.engine import FeatureEngine
from src.strategy.base import BaseStrategy
from src.strategy.pullback import PullbackStrategy
from src.strategy.momentum import MomentumStrategy
from src.filters.core import TradeFilter
from src.risk.manager import RiskManager


class BaseEngine(ABC):
    """
    Base Engine for shared logic.
    """

    def __init__(self, strategy: BaseStrategy, initial_capital: float = 10000.0, slippage_pct: float = 0.0005):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.slippage_pct = slippage_pct
        self.position = None
        self.trade_log = []
        self.equity_curve = []
        self.feature_engine = FeatureEngine()
        self.strategy = strategy
        self.filter = TradeFilter()
        self.risk_manager = RiskManager(atr_multiplier=1.5)

    @abstractmethod
    def _calculate_commission(self, cost: float) -> float:
        pass

    def run(self, df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
        df = self.feature_engine.add_indicators(df)
        df = self.feature_engine.add_regime(df, benchmark_df)
        df["Signal"] = self.strategy.generate_signals(df)

        close_idx = df.columns.get_loc("Close")
        atr_idx = df.columns.get_loc("ATR_14")
        low_idx = df.columns.get_loc("Low")
        open_idx = df.columns.get_loc("Open")
        high_idx = df.columns.get_loc("High")
        signal_idx = df.columns.get_loc("Signal")
        regime_idx = df.columns.get_loc("Regime")
        vol_sma_idx = df.columns.get_loc("Vol_SMA_20")
        bar_value_getter = itemgetter(
            close_idx,
            atr_idx,
            low_idx,
            open_idx,
            high_idx,
            signal_idx,
        )

        for date, row_values in zip(df.index, df.itertuples(index=False, name=None)):
            close, atr, low, open_price, high, signal = bar_value_getter(row_values)

            if self.position:
                self._process_bar(date, close, atr, low, open_price, high, signal)
            elif signal == 1:
                row_context = self._build_trade_filter_context(
                    row_values,
                    regime_idx,
                    vol_sma_idx,
                    close,
                    atr,
                )
                if self.filter.can_trade(row_context):
                    self._open_position(date, close, atr)

            current_value = self._calculate_equity(close)
            self.equity_curve.append({"Date": date, "Equity": current_value})
        return pd.DataFrame(self.trade_log)

<<<<<<< HEAD
    def _build_trade_filter_context(self, row_values, regime_idx, vol_sma_idx, close, atr):
        return {
            "Regime": row_values[regime_idx],
            "Vol_SMA_20": row_values[vol_sma_idx],
            "Close": close,
            "ATR_14": atr,
        }

    def _process_bar(self, date, close, atr, low, open_price, high, signal):
        if self.position:
            self._update_position_stop(close, atr)
            if self._check_exit_conditions(date, close, low, open_price, high, signal):
                return

    def _update_position_stop(self, close, atr):
        self.position["stop_price"] = self.risk_manager.update_trailing_stop(
            self.position["stop_price"], close, atr
        )

    def _check_exit_conditions(self, date, close, low, open_price, high, signal):
        if low <= self.position["stop_price"]:
            self._close_position(
                date, min(self.position["stop_price"], open_price), "Trailing Stop"
            )
            return True
        if high >= self.position["target_price"]:
            self._close_position(date, self.position["target_price"], "Take Profit")
            return True
        if signal == -1:
            self._close_position(date, close, "Strategy Exit")
            return True
        return False

    def _calculate_equity(self, close):
        return self.cash + (self.position["shares"] * close if self.position else 0)

    def _build_open_position_payload(self, date, close, atr):
        entry = close * (1 + self.slippage_pct)
        stop, target = self.risk_manager.calculate_stops(entry, atr)
        shares = self.risk_manager.calculate_position_size(self.cash, entry, stop)
        if shares <= 0:
            return None

        cost = shares * entry
        commission = self._calculate_commission(cost)
        position = {
            "shares": shares,
            "entry_price": entry,
            "stop_price": stop,
            "target_price": target,
            "commission_in": commission,
        }
        trade = {
            "Type": "Buy",
            "Date": date,
            "Price": entry,
            "Shares": shares,
            "Commission": commission,
        }
        return cost, commission, position, trade

    def _calculate_close_position_values(self, price):
        exit_price = price * (1 - self.slippage_pct)
        shares = self.position["shares"]
        proceeds = shares * exit_price
        commission = self._calculate_commission(proceeds)
        pnl = (proceeds - commission) - (
            shares * self.position["entry_price"] + self.position["commission_in"]
        )
        return exit_price, proceeds, commission, pnl

    def _build_close_trade_payload(self, date, exit_price, pnl, commission):
        return {
            "Type": "Sell",
            "Date": date,
            "Price": exit_price,
            "PnL": pnl,
            "Commission": commission,
        }

    def _open_position(self, date, close, atr):
        payload = self._build_open_position_payload(date, close, atr)
        if payload is None:
            return

        cost, commission, position, trade = payload
        self.cash -= cost + commission
        self.position = position
        self.trade_log.append(trade)

    def _close_position(self, date, price, reason):
        exit_price, proceeds, commission, pnl = self._calculate_close_position_values(price)
        self.cash += proceeds - commission
        self.trade_log.append(
            self._build_close_trade_payload(date, exit_price, pnl, commission)
        )
        self.position = None


class JPBacktestEngine(BaseEngine):
    def __init__(self, strategy: Optional[BaseStrategy] = None, initial_capital: float = 100000.0, slippage_pct: float = 0.0005):
        if strategy is None:
            strategy = PullbackStrategy(
                trend_sma=200, dip_sma=20, rsi_entry=50, rsi_exit=70
            )
        super().__init__(strategy, initial_capital, slippage_pct)
        self.risk_manager.atr_multiplier = 2.0

    def _calculate_commission(self, cost: float) -> float:
        return 0.0


class USBacktestEngine(BaseEngine):
    def __init__(self, strategy: Optional[BaseStrategy] = None, initial_capital: float = 100000.0, slippage_pct: float = 0.0005):
        if strategy is None:
            # US: Trend Following (Breakout) to capture move without waiting for deep pullback
            strategy = MomentumStrategy(trend_sma=200, breakout_window=20)
        super().__init__(strategy, initial_capital, slippage_pct)
        self.risk_manager.atr_multiplier = 2.0

    def _calculate_commission(self, cost: float) -> float:
        return cost * 0.00495


# run_backtest.py などレガシーimport用（米国株プルに相当）
BacktestEngine = USBacktestEngine
