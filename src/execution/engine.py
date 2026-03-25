import pandas as pd
from src.features.engine import FeatureEngine
from src.strategy.pullback import PullbackStrategy
from src.filters.core import TradeFilter
from src.risk.manager import RiskManager

class BacktestEngine:
    """
    SPEC v4 compliant Backtest Engine.
    Orchestrates the pipeline: Data -> Feature -> Strategy -> Filter -> Risk -> Execution.
    Includes realistic slippage and commission.
    """
    def __init__(self, initial_capital: float = 10000.0, commission_per_share: float = 0.01, slippage_pct: float = 0.0005):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_per_share = commission_per_share
        self.slippage_pct = slippage_pct
        self.position = None # None or {'shares': int, 'entry_price': float, 'stop_price': float, 'target_price': float}
        self.trade_log = []
        self.equity_curve = []

        # Components
        self.feature_engine = FeatureEngine()
        # Strategy: Balanced Pullback
        self.strategy = PullbackStrategy(trend_sma=200, dip_sma=20, rsi_entry=35) 
        self.filter = TradeFilter() 
        # Risk: Balanced Stops (ATR 2.5)
        self.risk_manager = RiskManager(atr_multiplier=2.5)

    def run(self, df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs the backtest simulation.
        """
        # 1. Feature Engineering
        df = self.feature_engine.add_indicators(df)
        df = self.feature_engine.add_regime(df, benchmark_df)

        # 2. Pre-calculate Strategy Signals
        raw_signals = self.strategy.generate_signals(df)
        df['Signal'] = raw_signals

        # 3. Simulation Loop
        for date, row in df.iterrows():
            self._process_bar(date, row)
            
            # Track Equity
            current_value = self.cash
            if self.position:
                current_value += self.position['shares'] * row['Close']
            self.equity_curve.append({'Date': date, 'Equity': current_value})

        return pd.DataFrame(self.trade_log)

    def _process_bar(self, date, row):
        current_price = row['Close']
        high_price = row['High']
        low_price = row['Low']
        
        if self.position:
            # Check Stop Loss (Slippage applied to exit)
            if low_price <= self.position['stop_price']:
                exit_price = min(self.position['stop_price'], row['Open'])
                self._close_position(date, exit_price, 'Stop Loss')
                return

            # Check Take Profit
            if high_price >= self.position['target_price']:
                self._close_position(date, self.position['target_price'], 'Take Profit')
                return

            # Strategy Exit
            if row['Signal'] == -1:
                self._close_position(date, current_price, 'Strategy Exit')
                return

        if not self.position:
            if row['Signal'] == 1:
                if self.filter.can_trade(row):
                    self._open_position(date, row)

    def _open_position(self, date, row):
        # Apply Slippage to Entry (Buy higher)
        entry_price = row['Close'] * (1 + self.slippage_pct)
        atr = row['ATR_14']
        
        stop_price, target_price = self.risk_manager.calculate_stops(entry_price, atr)
        shares = self.risk_manager.calculate_position_size(self.cash, entry_price, stop_price)
        
        if shares > 0:
            cost = shares * entry_price
            commission = shares * self.commission_per_share
            self.cash -= (cost + commission)
            self.position = {
                'shares': shares,
                'entry_price': entry_price,
                'stop_price': stop_price,
                'target_price': target_price,
                'entry_date': date,
                'commission_in': commission
            }
            self.trade_log.append({
                'Type': 'Buy', 'Date': date, 'Price': entry_price, 
                'Shares': shares, 'Reason': 'Signal + Filter', 'Commission': commission
            })

    def _close_position(self, date, price, reason):
        # Apply Slippage to Exit (Sell lower)
        exit_price = price * (1 - self.slippage_pct)
        shares = self.position['shares']
        proceeds = shares * exit_price
        commission = shares * self.commission_per_share
        
        self.cash += (proceeds - commission)
        
        pnl = (proceeds - commission) - (shares * self.position['entry_price'] + self.position['commission_in'])
        pnl_pct = pnl / (shares * self.position['entry_price'])
        
        self.trade_log.append({
            'Type': 'Sell', 'Date': date, 'Price': exit_price, 
            'Shares': shares, 'Reason': reason, 'PnL': pnl, 
            'PnL_Pct': pnl_pct, 'Commission': commission
        })
        self.position = None
