"""
リファクタリング済みコンポーネントのテスト
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategy.base import BaseStrategy, BaseBacktestResult
from src.strategy.momentum_v2 import MomentumV2Strategy
from src.strategy.mean_reversion_v2 import MeanReversionV2Strategy
from src.backtest.engine_v2 import BacktestEngineV2, Position, Trade
from src.config.strategy_config import (
    BacktestConfig,
    MomentumConfig,
    MeanReversionConfig,
    StrategyConfigFactory,
)
from src.utils.results import save_results, generate_report


def create_sample_data(days: int = 100) -> pd.DataFrame:
    """サンプル株価データを作成"""
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    # ランダムウォークで価格を生成
    np.random.seed(42)
    returns = np.random.randn(days).cumsum() / 10 + 0.05
    close = 100 * (1 + returns)
    
    # OHLCV データを作成
    data = {
        'Open': close * (1 + np.random.randn(days) * 0.01),
        'High': close * (1 + np.abs(np.random.randn(days) * 0.02)),
        'Low': close * (1 - np.abs(np.random.randn(days) * 0.02)),
        'Close': close,
        'Volume': np.random.randint(1000000, 10000000, days),
    }
    
    df = pd.DataFrame(data, index=dates)
    return df


class TestBaseStrategy:
    """BaseStrategy のテスト"""

    def test_abstract_methods(self):
        """抽象メソッドが定義されていることを確認"""
        assert hasattr(BaseStrategy, 'generate_signals')
        assert hasattr(BaseStrategy, 'calculate_position_size')

    def test_get_strategy_name(self):
        """戦略名が取得できることを確認"""
        strategy = MomentumV2Strategy()
        assert strategy.get_strategy_name() == 'MomentumV2Strategy'

    def test_reset(self):
        """リセットメソッドが呼び出せることを確認"""
        strategy = MomentumV2Strategy()
        strategy.reset()  # エラーにならないことを確認


class TestMomentumV2Strategy:
    """MomentumV2Strategy のテスト"""

    def test_initialization(self):
        """初期化を確認"""
        strategy = MomentumV2Strategy()
        assert strategy.rsi_period == 14
        assert strategy.rsi_max == 70.0
        assert strategy.max_holding_days == 60

    def test_custom_parameters(self):
        """カスタムパラメータでの初期化"""
        strategy = MomentumV2Strategy(rsi_period=10, rsi_max=65.0)
        assert strategy.rsi_period == 10
        assert strategy.rsi_max == 65.0

    def test_calculate_indicators(self):
        """指標計算のテスト"""
        df = create_sample_data(100)
        strategy = MomentumV2Strategy()
        
        result = strategy.calculate_indicators(df)
        
        assert 'SMA_200' in result.columns
        assert 'SMA_50' in result.columns
        assert 'RSI_14' in result.columns
        assert 'ATR_14' in result.columns

    def test_calculate_position_size(self):
        """ポジションサイズ計算のテスト"""
        strategy = MomentumV2Strategy()
        
        shares = strategy.calculate_position_size(
            capital=100000,
            entry_price=150.0,
            stop_price=140.0,
            risk_per_trade=0.01
        )
        
        assert shares > 0
        assert isinstance(shares, int)

    def test_generate_signals(self):
        """シグナル生成のテスト"""
        df = create_sample_data(100)
        spy_df = create_sample_data(100)
        strategy = MomentumV2Strategy()
        
        signals = strategy.generate_signals(df, spy_df)
        
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})

    def test_reset(self):
        """リセットのテスト"""
        strategy = MomentumV2Strategy()
        strategy._position_entry_date = pd.Timestamp('2024-01-01')
        strategy.reset()
        assert strategy._position_entry_date is None


class TestMeanReversionV2Strategy:
    """MeanReversionV2Strategy のテスト"""

    def test_initialization(self):
        """初期化を確認"""
        strategy = MeanReversionV2Strategy()
        assert strategy.rsi_period == 14
        assert strategy.rsi_entry_max == 35.0
        assert strategy.profit_target_pct == 0.06

    def test_custom_parameters(self):
        """カスタムパラメータでの初期化"""
        strategy = MeanReversionV2Strategy(rsi_period=10, profit_target_pct=0.05)
        assert strategy.rsi_period == 10
        assert strategy.profit_target_pct == 0.05

    def test_calculate_indicators(self):
        """指標計算のテスト"""
        df = create_sample_data(100)
        strategy = MeanReversionV2Strategy()
        
        result = strategy.calculate_indicators(df)
        
        assert 'SMA_200' in result.columns
        assert 'RSI_14' in result.columns
        assert 'BB_Lower' in result.columns

    def test_calculate_position_size(self):
        """ポジションサイズ計算のテスト"""
        strategy = MeanReversionV2Strategy()
        
        shares = strategy.calculate_position_size(
            capital=100000,
            entry_price=150.0,
            risk_per_trade=0.01
        )
        
        assert shares > 0
        assert isinstance(shares, int)

    def test_generate_signals(self):
        """シグナル生成のテスト"""
        df = create_sample_data(100)
        spy_df = create_sample_data(100)
        strategy = MeanReversionV2Strategy()
        
        signals = strategy.generate_signals(df, spy_df)
        
        assert len(signals) == len(df)
        assert set(signals.unique()).issubset({-1, 0, 1})


class TestBacktestEngineV2:
    """BacktestEngineV2 のテスト"""

    def test_initialization(self):
        """初期化を確認"""
        config = BacktestConfig()
        engine = BacktestEngineV2(config)
        
        assert engine.initial_capital == config.initial_capital
        assert engine.slippage_pct == config.slippage_pct

    def test_run_momentum(self):
        """モメンタム戦略のバックテスト"""
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngineV2(config)
        strategy = MomentumV2Strategy()
        
        df = create_sample_data(100)
        spy_df = create_sample_data(100)
        
        result = engine.run(strategy, df, spy_df, 'TEST')
        
        assert result is not None
        assert result.strategy_name == 'MomentumV2Strategy'
        assert result.ticker == 'TEST'

    def test_run_mean_reversion(self):
        """平均回帰戦略のバックテスト"""
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngineV2(config)
        strategy = MeanReversionV2Strategy()
        
        df = create_sample_data(100)
        spy_df = create_sample_data(100)
        
        result = engine.run(strategy, df, spy_df, 'TEST')
        
        assert result is not None
        assert result.strategy_name == 'MeanReversionV2Strategy'

    def test_calculate_metrics(self):
        """指標計算のテスト"""
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngineV2(config)
        
        # 空の状態では空の辞書を返す
        metrics = engine.calculate_metrics()
        assert metrics == {}

    def test_position_dataclass(self):
        """Position データクラスのテスト"""
        pos = Position(
            shares=100,
            entry_price=150.0,
            entry_date=pd.Timestamp('2024-01-01'),
            stop_price=140.0
        )
        
        assert pos.shares == 100
        assert pos.entry_price == 150.0
        assert pos.stop_price == 140.0

    def test_trade_dataclass(self):
        """Trade データクラスのテスト"""
        trade = Trade(
            type='Sell',
            date=pd.Timestamp('2024-01-10'),
            price=160.0,
            shares=100,
            pnl=900.0,
            reason='Take Profit'
        )
        
        assert trade.type == 'Sell'
        assert trade.pnl == 900.0
        assert trade.reason == 'Take Profit'


class TestStrategyConfig:
    """戦略設定のテスト"""

    def test_backtest_config(self):
        """BacktestConfig のテスト"""
        config = BacktestConfig()
        
        assert config.initial_capital == 100000.0
        assert config.slippage_pct == 0.0005
        assert config.commission_rate == 0.00495

    def test_momentum_config(self):
        """MomentumConfig のテスト"""
        config = MomentumConfig()
        
        assert config.rsi_period == 14
        assert config.rsi_max == 70.0
        assert config.breakout_window == 20

    def test_mean_reversion_config(self):
        """MeanReversionConfig のテスト"""
        config = MeanReversionConfig()
        
        assert config.rsi_period == 14
        assert config.rsi_entry_max == 35.0
        assert config.profit_target_pct == 0.06

    def test_config_to_dict(self):
        """設定の辞書変換テスト"""
        config = MomentumConfig(rsi_period=10)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['rsi_period'] == 10

    def test_strategy_config_factory(self):
        """ファクトリのテスト"""
        momentum_config = StrategyConfigFactory.create_config('momentum')
        assert isinstance(momentum_config, MomentumConfig)
        
        mean_rev_config = StrategyConfigFactory.create_config('mean_reversion')
        assert isinstance(mean_rev_config, MeanReversionConfig)

    def test_strategy_config_factory_with_overrides(self):
        """ファクトリ（オーバーライド）のテスト"""
        config = StrategyConfigFactory.create_config(
            'momentum',
            rsi_period=10,
            rsi_max=65.0
        )
        
        assert config.rsi_period == 10
        assert config.rsi_max == 65.0

    def test_strategy_config_factory_invalid(self):
        """無効な戦略名のテスト"""
        with pytest.raises(ValueError):
            StrategyConfigFactory.create_config('invalid_strategy')


class TestResultsUtils:
    """結果出力ユーティリティのテスト"""

    def test_generate_report(self):
        """レポート生成のテスト"""
        df = create_sample_data(50)
        spy_df = create_sample_data(50)
        
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngineV2(config)
        strategy = MomentumV2Strategy()
        
        result = engine.run(strategy, df, spy_df, 'TEST')
        metrics = engine.calculate_metrics()
        
        report = generate_report(result, metrics)
        
        assert 'BACKTEST REPORT' in report
        assert 'MomentumV2Strategy' in report
        assert 'TEST' in report

    def test_base_backtest_result(self):
        """BaseBacktestResult のテスト"""
        result = BaseBacktestResult(
            strategy_name='TestStrategy',
            ticker='TEST',
            initial_capital=100000,
            final_capital=110000,
            trades=pd.DataFrame(),
            equity_curve=pd.DataFrame({'Date': [1, 2], 'Equity': [100000, 110000]}),
        )
        
        assert result.strategy_name == 'TestStrategy'
        assert result.total_return == 0.10
        assert result.total_pnl == 10000

    def test_base_backtest_result_to_dict(self):
        """BaseBacktestResult の辞書変換テスト"""
        result = BaseBacktestResult(
            strategy_name='TestStrategy',
            ticker='TEST',
            initial_capital=100000,
            final_capital=110000,
            trades=pd.DataFrame(),
            equity_curve=pd.DataFrame(),
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['strategy_name'] == 'TestStrategy'
        assert result_dict['ticker'] == 'TEST'
        assert result_dict['total_return'] == 0.10
