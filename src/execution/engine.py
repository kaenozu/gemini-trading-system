import pandas as pd
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from src.features.engine import FeatureEngine
from src.strategy.pullback import PullbackStrategy
from src.strategy.momentum import MomentumStrategy
from src.filters.core import TradeFilter
from src.risk.manager import RiskManager
import logging

logger = logging.getLogger(__name__)


class BaseEngine(ABC):
    """
    Base Engine for shared logic.
    """
    
    def __init__(self, initial_capital: float = 10000.0, slippage_pct: float = 0.0005):
        self.initial_capital: float = initial_capital
        self.cash: float = initial_capital
        self.slippage_pct: float = slippage_pct
        self.position: Optional[Dict[str, Any]] = None
        self.trade_log: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.feature_engine: FeatureEngine = FeatureEngine()
        self.strategy: PullbackStrategy = PullbackStrategy(trend_sma=100, dip_sma=20, rsi_entry=50, rsi_exit=75)
        self.filter: TradeFilter = TradeFilter()
        self.risk_manager: RiskManager = RiskManager(atr_multiplier=1.5)

    @abstractmethod
    def _calculate_commission(self, cost: float) -> float:
        """Calculate commission for a trade."""
        pass

    def reset(self):
        """Reset engine state between backtest runs."""
        self.cash = self.initial_capital
        self.position = None
        self.trade_log = []
        self.equity_curve = []

    def run(self, df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
        """
        Run backtest on given data.
        
        Args:
            df: Price data for the ticker
            benchmark_df: Benchmark data for regime detection
            
        Returns:
            DataFrame with trade log
        """
        self.reset()
        
        df = self.feature_engine.add_indicators(df)
        df = self.feature_engine.add_regime(df, benchmark_df)
        df['Signal'] = self.strategy.generate_signals(df)

        for date, row in df.iterrows():
            self._process_bar(date, row)
            current_value = self.cash + (self.position['shares'] * row['Close'] if self.position else 0)
            self.equity_curve.append({'Date': date, 'Equity': current_value})
        return pd.DataFrame(self.trade_log)

    def _process_bar(self, date: pd.Timestamp, row: pd.Series):
        """Process a single bar of data."""
        if self.position:
            self.position['stop_price'] = self.risk_manager.update_trailing_stop(
                self.position['stop_price'], row['Close'], row['ATR_14']
            )
            if row['Low'] <= self.position['stop_price']:
                self._close_position(date, min(self.position['stop_price'], row['Open']), 'Trailing Stop')
                return
            if row['High'] >= self.position['target_price']:
                self._close_position(date, self.position['target_price'], 'Take Profit')
                return
            if row['Signal'] == -1:
                self._close_position(date, row['Close'], 'Strategy Exit')
                return

        if not self.position:
            if row['Signal'] == 1:
                can_trade, reason = self.filter.can_trade(row)
                if can_trade:
                    self._open_position(date, row)
                else:
                    logger.debug(f"Trade filter blocked {reason} for {date}")

    def _open_position(self, date: pd.Timestamp, row: pd.Series):
        """Open a new position."""
        entry = row['Close'] * (1 + self.slippage_pct)
        stop, target = self.risk_manager.calculate_stops(entry, row['ATR_14'])
        shares = self.risk_manager.calculate_position_size(self.cash, entry, stop)
        
        if shares > 0:
            cost = shares * entry
            comm = self._calculate_commission(cost)
            self.cash -= (cost + comm)
            self.position = {
                'shares': shares,
                'entry_price': entry,
                'stop_price': stop,
                'target_price': target,
                'commission_in': comm
            }
            self.trade_log.append({
                'Type': 'Buy',
                'Date': date,
                'Price': entry,
                'Shares': shares,
                'Commission': comm
            })
            logger.info(f"Opened position: {shares} shares at {entry}")

    def _close_position(self, date: pd.Timestamp, price: float, reason: str):
        """Close an existing position."""
        exit_p = price * (1 - self.slippage_pct)
        shares = self.position['shares']
        proceeds = shares * exit_p
        comm = self._calculate_commission(proceeds)
        self.cash += (proceeds - comm)
        pnl = (proceeds - comm) - (shares * self.position['entry_price'] + self.position['commission_in'])
        self.trade_log.append({
            'Type': 'Sell',
            'Date': date,
            'Price': exit_p,
            'PnL': pnl,
            'Commission': comm,
            'Reason': reason
        })
        self.position = None
        logger.info(f"Closed position: {reason}, PnL: {pnl:.2f}")


class JPBacktestEngine(BaseEngine):
    """Backtest engine for Japanese stocks."""
    
    def __init__(self, initial_capital: float = 100000.0, slippage_pct: float = 0.0005):
        super().__init__(initial_capital, slippage_pct)
        self.strategy = PullbackStrategy(trend_sma=200, dip_sma=20, rsi_entry=50, rsi_exit=70)
        self.risk_manager.atr_multiplier = 2.0

    def _calculate_commission(self, cost: float) -> float:
        """
        Calculate commission for Japanese stocks.
        Reference: Rakuten Securities commission structure (simplified)
        """
        if cost <= 50000:
            return 55.0  # Minimum fee
        elif cost <= 100000:
            return cost * 0.00099
        elif cost <= 200000:
            return cost * 0.00088
        elif cost <= 500000:
            return cost * 0.00077
        else:
            return cost * 0.00066


class USBacktestEngine(BaseEngine):
    """Backtest engine for US stocks."""
    
    def __init__(self, initial_capital: float = 100000.0, slippage_pct: float = 0.0005):
        super().__init__(initial_capital, slippage_pct)
        # US: Trend Following (Breakout) to capture move without waiting for deep pullback
        self.strategy = MomentumStrategy(trend_sma=200, breakout_window=20)
        self.risk_manager.atr_multiplier = 2.0

    def _calculate_commission(self, cost: float) -> float:
        """
        Calculate commission for US stocks.
        Reference: Typical US broker commission (0.495%)
        """
        return cost * 0.00495
