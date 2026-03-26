import pandas as pd
from abc import ABC, abstractmethod
from src.features.engine import FeatureEngine
from src.strategy.pullback import PullbackStrategy
from src.filters.core import TradeFilter
from src.risk.manager import RiskManager

class BaseEngine(ABC):
    """
    Base Engine for shared logic.
    """
    def __init__(self, initial_capital: float = 10000.0, slippage_pct: float = 0.0005):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.slippage_pct = slippage_pct
        self.position = None
        self.trade_log = []
        self.equity_curve = []
        self.feature_engine = FeatureEngine()
        self.strategy = PullbackStrategy(trend_sma=100, dip_sma=20, rsi_entry=50, rsi_exit=75) 
        self.filter = TradeFilter() 
        self.risk_manager = RiskManager(atr_multiplier=1.5)

    @abstractmethod
    def _calculate_commission(self, cost: float) -> float:
        pass

    def run(self, df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
        df = self.feature_engine.add_indicators(df)
        df = self.feature_engine.add_regime(df, benchmark_df)
        df['Signal'] = self.strategy.generate_signals(df)

        for date, row in df.iterrows():
            self._process_bar(date, row)
            current_value = self.cash + (self.position['shares'] * row['Close'] if self.position else 0)
            self.equity_curve.append({'Date': date, 'Equity': current_value})
        return pd.DataFrame(self.trade_log)

    def _process_bar(self, date, row):
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
        elif row['Signal'] == 1 and self.filter.can_trade(row):
            self._open_position(date, row)

    def _open_position(self, date, row):
        entry = row['Close'] * (1 + self.slippage_pct)
        stop, target = self.risk_manager.calculate_stops(entry, row['ATR_14'])
        shares = self.risk_manager.calculate_position_size(self.cash, entry, stop)
        if shares > 0:
            cost = shares * entry
            comm = self._calculate_commission(cost)
            self.cash -= (cost + comm)
            self.position = {'shares': shares, 'entry_price': entry, 'stop_price': stop, 'target_price': target, 'commission_in': comm}
            self.trade_log.append({'Type': 'Buy', 'Date': date, 'Price': entry, 'Shares': shares, 'Commission': comm})

    def _close_position(self, date, price, reason):
        exit_p = price * (1 - self.slippage_pct)
        shares = self.position['shares']
        proceeds = shares * exit_p
        comm = self._calculate_commission(proceeds)
        self.cash += (proceeds - comm)
        pnl = (proceeds - comm) - (shares * self.position['entry_price'] + self.position['commission_in'])
        self.trade_log.append({'Type': 'Sell', 'Date': date, 'Price': exit_p, 'PnL': pnl, 'Commission': comm})
        self.position = None

class JPBacktestEngine(BaseEngine):
    def _calculate_commission(self, cost: float) -> float:
        return 0.0 

class USBacktestEngine(BaseEngine):
    def _calculate_commission(self, cost: float) -> float:
        return cost * 0.00495
