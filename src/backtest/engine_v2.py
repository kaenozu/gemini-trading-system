"""
共通バックテストエンジン v2

戦略に依存しない共通のバックテスト処理を実装
"""
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.strategy.base import BaseStrategy, BaseBacktestResult
from src.config.strategy_config import BacktestConfig


@dataclass
class Position:
    """
    ポジション情報
    """
    shares: int
    entry_price: float
    entry_date: pd.Timestamp
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    trailing_stop: Optional[float] = None
    commission_in: float = 0.0
    partial_exited: bool = False
    partial_exit_shares: int = 0
    profit_target: Optional[float] = None  # 平均回帰用
    stop_loss: Optional[float] = None  # 平均回帰用


@dataclass
class Trade:
    """
    トレード記録
    """
    type: str  # Buy, Sell, Sell (50%)
    date: pd.Timestamp
    price: float
    shares: int
    pnl: Optional[float] = None
    commission: float = 0.0
    reason: str = ""
    ticker: str = "N/A"
    holding_days: int = 0


class BacktestEngineV2:
    """
    共通バックテストエンジン
    
    責務:
    - ポジション管理
    - 損益計算
    - 資産曲線記録
    - 結果出力
    """

    def __init__(self, config: BacktestConfig):
        """
        バックテストエンジンの初期化
        
        Args:
            config: バックテスト設定
        """
        self.config = config
        self.initial_capital = config.initial_capital
        self.slippage_pct = config.slippage_pct
        self.commission_rate = config.commission_rate
        self.risk_per_trade = config.risk_per_trade
        self.max_position_pct = config.max_position_pct

        # 状態管理
        self.cash: float = config.initial_capital
        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict[str, Any]] = []

    def run(
        self,
        strategy: BaseStrategy,
        df: pd.DataFrame,
        spy_df: pd.DataFrame,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> BaseBacktestResult:
        """
        バックテストを実行
        
        Args:
            strategy: 戦略インスタンス
            df: 銘柄の株価データ
            spy_df: ベンチマーク（SPY）データ
            ticker: 銘柄コード
            start_date: 開始日
            end_date: 終了日
            **kwargs: 戦略固有のパラメータ
            
        Returns:
            BaseBacktestResult: バックテスト結果
        """
        # 期間フィルタ
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        if df.empty:
            return self._create_empty_result(strategy, ticker)

        # 状態リセット
        self._reset()
        strategy.reset()

        # シグナルを一括計算 (O(N) への最適化)
        try:
            # v2 戦略用（spy_df を必要とする）
            all_signals = strategy.generate_signals(df, spy_df, **kwargs)
        except TypeError:
            # 旧戦略用（df のみ）
            all_signals = strategy.generate_signals(df, **kwargs)

        # 各日付を処理
        for i, (date, row) in enumerate(df.iterrows()):
            # シグナル取得（一括計算した結果から参照）
            signal = all_signals.iloc[i] if i < len(all_signals) else 0

            # ポジション処理
            if self.position:
                self._process_position(date, row, signal, strategy, **kwargs)
            elif signal == 1:
                self._open_position(date, row, strategy, ticker, **kwargs)

            # 資産記録
            equity = self._calculate_equity(row)
            self.equity_curve.append({'Date': date, 'Equity': equity})

        # 未決済ポジションを強制決済
        if self.position and not df.empty:
            last_row = df.iloc[-1]
            self._close_position(
                df.index[-1],
                last_row['Close'],
                'Backtest End',
                ticker
            )

        return self._create_result(strategy, ticker)

    def _reset(self):
        """状態をリセット"""
        self.cash = self.initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = []

    def _open_position(
        self,
        date: pd.Timestamp,
        row: pd.Series,
        strategy: BaseStrategy,
        ticker: str,
        **kwargs
    ):
        """
        ポジションをオープン
        
        Args:
            date: 日付
            row: 株価データ
            strategy: 戦略インスタンス
            ticker: 銘柄コード
            **kwargs: 戦略固有のパラメータ
        """
        entry_price = row['Close'] * (1 + self.slippage_pct)

        # ポジションサイズ計算
        shares = self._calculate_shares(strategy, entry_price, row, **kwargs)

        if shares <= 0:
            return

        # コスト計算
        cost = shares * entry_price
        commission = cost * self.commission_rate

        # 現金更新
        self.cash -= (cost + commission)

        # ポジション記録
        self.position = Position(
            shares=shares,
            entry_price=entry_price,
            entry_date=date,
            commission_in=commission,
        )

        # トレードログ
        self.trades.append(Trade(
            type='Buy',
            date=date,
            price=entry_price,
            shares=shares,
            commission=commission,
            ticker=ticker,
        ))

    def _calculate_shares(
        self,
        strategy: BaseStrategy,
        entry_price: float,
        row: pd.Series,
        **kwargs
    ) -> int:
        """
        購入株数を計算
        
        Args:
            strategy: 戦略インスタンス
            entry_price: エントリー価格
            row: 株価データ
            **kwargs: 戦略固有のパラメータ
            
        Returns:
            int: 購入株数
        """
        # リスクベース計算
        risk_amount = self.cash * self.risk_per_trade

        # stop_price があればそれを使用
        stop_price = kwargs.get('stop_price')
        if stop_price and stop_price < entry_price:
            risk_per_share = entry_price - stop_price
            if risk_per_share > 0:
                shares = int(risk_amount / risk_per_share)
            else:
                shares = int(self.cash * self.max_position_pct / entry_price)
        else:
            # デフォルト：ポジションサイズの最大値まで
            shares = int(self.cash * self.max_position_pct / entry_price)

        return shares

    def _process_position(
        self,
        date: pd.Timestamp,
        row: pd.Series,
        signal: int,
        strategy: BaseStrategy,
        **kwargs
    ):
        """
        ポジションを処理
        
        Args:
            date: 日付
            row: 株価データ
            signal: シグナル
            strategy: 戦略インスタンス
            **kwargs: 戦略固有のパラメータ
        """
        if not self.position:
            return

        # エグジットシグナルで決済
        if signal == -1:
            reason = self._get_exit_reason(row, strategy, **kwargs)
            self._close_position(date, row['Close'], reason, row.get('Ticker', 'N/A'))

    def _get_exit_reason(
        self,
        row: pd.Series,
        strategy: BaseStrategy,
        **kwargs
    ) -> str:
        """
        エグジット理由を取得
        
        Args:
            row: 株価データ
            strategy: 戦略インスタンス
            **kwargs: 戦略固有のパラメータ
            
        Returns:
            str: エグジット理由
        """
        if not self.position:
            return ''

        # 保有日数チェック
        holding_days = (row.name - self.position.entry_date).days
        max_holding_days = kwargs.get('max_holding_days', 60)
        
        if holding_days >= max_holding_days:
            return f'Time Exit ({max_holding_days}D)'

        return 'Strategy Exit'

    def _close_position(
        self,
        date: pd.Timestamp,
        price: float,
        reason: str,
        ticker: str
    ):
        """
        ポジションをクローズ
        
        Args:
            date: 日付
            price: 決済価格
            reason: 理由
            ticker: 銘柄コード
        """
        if not self.position:
            return

        shares = self.position.shares
        exit_price = price * (1 - self.slippage_pct)
        proceeds = shares * exit_price
        commission = proceeds * self.commission_rate

        self.cash += (proceeds - commission)

        # PnL 計算
        total_cost = shares * self.position.entry_price + self.position.commission_in
        pnl = (proceeds - commission) - total_cost

        # 保有日数計算
        holding_days = (date - self.position.entry_date).days

        # トレードログ
        self.trades.append(Trade(
            type='Sell',
            date=date,
            price=exit_price,
            shares=shares,
            pnl=pnl,
            commission=commission,
            reason=reason,
            ticker=ticker,
            holding_days=holding_days,
        ))

        self.position = None

    def _calculate_equity(self, row: pd.Series) -> float:
        """
        資産を計算
        
        Args:
            row: 株価データ
            
        Returns:
            float: 総資産
        """
        if self.position:
            return self.cash + (self.position.shares * row['Close'])
        return self.cash

    def _create_empty_result(
        self,
        strategy: BaseStrategy,
        ticker: str
    ) -> BaseBacktestResult:
        """
        空の結果を作成
        
        Args:
            strategy: 戦略インスタンス
            ticker: 銘柄コード
            
        Returns:
            BaseBacktestResult: 空の結果
        """
        return BaseBacktestResult(
            strategy_name=strategy.get_strategy_name(),
            ticker=ticker,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            trades=pd.DataFrame(),
            equity_curve=pd.DataFrame(),
        )

    def _create_result(
        self,
        strategy: BaseStrategy,
        ticker: str
    ) -> BaseBacktestResult:
        """
        結果を作成
        
        Args:
            strategy: 戦略インスタンス
            ticker: 銘柄コード
            
        Returns:
            BaseBacktestResult: バックテスト結果
        """
        # トレードログを DataFrame に変換
        trades_df = self._trades_to_dataframe()

        return BaseBacktestResult(
            strategy_name=strategy.get_strategy_name(),
            ticker=ticker,
            initial_capital=self.initial_capital,
            final_capital=self.cash,
            trades=trades_df,
            equity_curve=pd.DataFrame(self.equity_curve),
        )

    def _trades_to_dataframe(self) -> pd.DataFrame:
        """
        トレードリストを DataFrame に変換
        
        Returns:
            pd.DataFrame: トレードログ
        """
        if not self.trades:
            return pd.DataFrame()

        data = []
        for trade in self.trades:
            data.append({
                'Type': trade.type,
                'Date': trade.date,
                'Price': trade.price,
                'Shares': trade.shares,
                'PnL': trade.pnl,
                'Commission': trade.commission,
                'Reason': trade.reason,
                'Ticker': trade.ticker,
                'HoldingDays': trade.holding_days,
            })

        return pd.DataFrame(data)

    def calculate_metrics(self) -> Dict[str, Any]:
        """
        パフォーマンス指標を計算
        
        Returns:
            Dict[str, Any]: パフォーマンス指標
        """
        if not self.trades:
            return {}

        trades_df = pd.DataFrame([
            {
                'type': t.type,
                'pnl': t.pnl,
                'holding_days': t.holding_days,
            }
            for t in self.trades
        ])

        # 決済トレードのみ
        sell_trades = trades_df[trades_df['type'].str.contains('Sell')]

        if sell_trades.empty:
            return {}

        # 基本指標
        total_pnl = sell_trades['pnl'].sum()
        winning_trades = sell_trades[sell_trades['pnl'] > 0]
        losing_trades = sell_trades[sell_trades['pnl'] <= 0]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        total_trades = len(sell_trades)

        win_rate = win_count / total_trades if total_trades > 0 else 0

        gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 0

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        avg_win = gross_profit / win_count if win_count > 0 else 0
        avg_loss = gross_loss / loss_count if loss_count > 0 else 0

        # 平均保有日数
        avg_holding_days = sell_trades['holding_days'].mean() if 'holding_days' in sell_trades.columns else 0

        # 最大ドローダウン
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            equity_df['Peak'] = equity_df['Equity'].cummax()
            equity_df['Drawdown'] = (equity_df['Equity'] - equity_df['Peak']) / equity_df['Peak']
            max_drawdown = equity_df['Drawdown'].min()
        else:
            max_drawdown = 0

        # 総リターン
        total_return = (self.cash - self.initial_capital) / self.initial_capital

        return {
            'Total PnL': total_pnl,
            'Total Return': f"{total_return:.2%}",
            'Win Rate': f"{win_rate:.2%}",
            'Profit Factor': f"{profit_factor:.2f}",
            'Total Trades': total_trades,
            'Winning Trades': win_count,
            'Losing Trades': loss_count,
            'Avg Win': f"${avg_win:.2f}",
            'Avg Loss': f"${avg_loss:.2f}",
            'Avg Holding Days': f"{avg_holding_days:.1f}",
            'Max Drawdown': f"{max_drawdown:.2%}",
            'Final Capital': f"${self.cash:.2f}",
        }
