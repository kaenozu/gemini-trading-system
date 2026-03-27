import pytest
import pandas as pd
import numpy as np
from src.risk.manager import RiskManager
from src.features.engine import FeatureEngine
from src.execution.engine import USBacktestEngine


class _StrategyStub:
    def generate_signals(self, df: pd.DataFrame):
        return pd.Series(0, index=df.index)

def test_risk_manager_position_sizing():
    manager = RiskManager(risk_per_trade_pct=0.01)
    # 100k capital, entry 100, stop 90 (risk 10 per share)
    # 1% risk = 1000. Shares = 1000 / 10 = 100
    shares = manager.calculate_position_size(100000, 100, 90)
    assert shares == 100

def test_feature_engine_rsi():
    fe = FeatureEngine()
    df = pd.DataFrame({'Close': [100, 101, 102, 101, 100, 99, 98, 99, 100, 101, 102, 103, 104, 105, 106]}, 
                      index=pd.date_range('2026-01-01', periods=15))
    df['High'] = df['Close'] + 1
    df['Low'] = df['Close'] - 1
    df['Volume'] = 1000
    
    df_with_ind = fe.add_indicators(df)
    assert 'RSI_14' in df_with_ind.columns
    assert not df_with_ind['RSI_14'].isna().iloc[-1]


def test_backtest_engine_open_position_records_state_and_trade_log():
    engine = USBacktestEngine(strategy=_StrategyStub(), initial_capital=1000.0, slippage_pct=0.01)
    engine.risk_manager.calculate_stops = lambda entry, atr: (entry - 5.0, entry + 10.0)
    engine.risk_manager.calculate_position_size = lambda cash, entry, stop: 3

    trade_date = pd.Timestamp('2026-01-20')
    engine._open_position(trade_date, 100.0, 2.0)

    entry_price = 101.0
    expected_commission = 3 * entry_price * 0.00495

    assert engine.cash == pytest.approx(1000.0 - (3 * entry_price) - expected_commission)
    assert engine.position == {
        'shares': 3,
        'entry_price': entry_price,
        'stop_price': 96.0,
        'target_price': 111.0,
        'commission_in': pytest.approx(expected_commission),
    }
    assert engine.trade_log[-1] == {
        'Type': 'Buy',
        'Date': trade_date,
        'Price': entry_price,
        'Shares': 3,
        'Commission': pytest.approx(expected_commission),
    }


def test_backtest_engine_close_position_records_cash_and_pnl():
    engine = USBacktestEngine(strategy=_StrategyStub(), initial_capital=1000.0, slippage_pct=0.01)
    engine.cash = 400.0
    engine.position = {
        'shares': 3,
        'entry_price': 101.0,
        'stop_price': 96.0,
        'target_price': 111.0,
        'commission_in': 3 * 101.0 * 0.00495,
    }

    trade_date = pd.Timestamp('2026-01-21')
    engine._close_position(trade_date, 120.0, 'Strategy Exit')

    exit_price = 118.8
    proceeds = 3 * exit_price
    expected_commission = proceeds * 0.00495
    expected_pnl = (proceeds - expected_commission) - (3 * 101.0 + (3 * 101.0 * 0.00495))

    assert engine.cash == pytest.approx(400.0 + proceeds - expected_commission)
    assert engine.position is None
    assert engine.trade_log[-1] == {
        'Type': 'Sell',
        'Date': trade_date,
        'Price': exit_price,
        'PnL': pytest.approx(expected_pnl),
        'Commission': pytest.approx(expected_commission),
    }


def test_backtest_engine_open_position_with_zero_shares_keeps_state_unchanged():
    engine = USBacktestEngine(strategy=_StrategyStub(), initial_capital=1000.0, slippage_pct=0.01)
    engine.cash = 777.0
    engine.position = {
        'shares': 1,
        'entry_price': 100.0,
        'stop_price': 95.0,
        'target_price': 110.0,
        'commission_in': 0.5,
    }
    engine.trade_log = [{'Type': 'Buy'}]

    engine.risk_manager.calculate_stops = lambda entry, atr: (entry - 5.0, entry + 10.0)
    engine.risk_manager.calculate_position_size = lambda cash, entry, stop: 0

    previous_cash = engine.cash
    previous_position = dict(engine.position)
    previous_trade_log = list(engine.trade_log)

    engine._open_position(pd.Timestamp('2026-01-22'), 100.0, 2.0)

    assert engine.cash == previous_cash
    assert engine.position == previous_position
    assert engine.trade_log == previous_trade_log


def test_backtest_engine_check_exit_conditions_prioritizes_trailing_stop_over_others():
    engine = USBacktestEngine(strategy=_StrategyStub(), initial_capital=1000.0, slippage_pct=0.0)
    engine.position = {
        'shares': 2,
        'entry_price': 100.0,
        'stop_price': 95.0,
        'target_price': 105.0,
        'commission_in': 0.0,
    }

    closed = []
    engine._close_position = lambda date, price, reason: closed.append((date, price, reason))

    trade_date = pd.Timestamp('2026-01-23')
    exited = engine._check_exit_conditions(
        trade_date,
        close=100.0,
        low=94.0,
        open_price=96.0,
        high=106.0,
        signal=-1,
    )

    assert exited is True
    assert closed == [(trade_date, 95.0, 'Trailing Stop')]


def test_backtest_engine_check_exit_conditions_prioritizes_take_profit_over_strategy_exit():
    engine = USBacktestEngine(strategy=_StrategyStub(), initial_capital=1000.0, slippage_pct=0.0)
    engine.position = {
        'shares': 2,
        'entry_price': 100.0,
        'stop_price': 95.0,
        'target_price': 105.0,
        'commission_in': 0.0,
    }

    closed = []
    engine._close_position = lambda date, price, reason: closed.append((date, price, reason))

    trade_date = pd.Timestamp('2026-01-24')
    exited = engine._check_exit_conditions(
        trade_date,
        close=102.0,
        low=96.0,
        open_price=101.0,
        high=106.0,
        signal=-1,
    )

    assert exited is True
    assert closed == [(trade_date, 105.0, 'Take Profit')]


def test_backtest_engine_calculate_equity_without_position_returns_cash_only():
    engine = USBacktestEngine(strategy=_StrategyStub(), initial_capital=1000.0, slippage_pct=0.0)
    engine.cash = 876.5
    engine.position = None

    assert engine._calculate_equity(close=123.0) == pytest.approx(876.5)


def test_backtest_engine_calculate_equity_with_position_includes_mark_to_market_value():
    engine = USBacktestEngine(strategy=_StrategyStub(), initial_capital=1000.0, slippage_pct=0.0)
    engine.cash = 500.0
    engine.position = {
        'shares': 3,
        'entry_price': 100.0,
        'stop_price': 95.0,
        'target_price': 110.0,
        'commission_in': 0.0,
    }

    assert engine._calculate_equity(close=120.0) == pytest.approx(860.0)
