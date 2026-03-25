from src.data.loader import DataLoader
from src.execution.engine import BacktestEngine
from src.analysis.plotter import plot_results
import pandas as pd

def main():
    # 1. Setup
    loader = DataLoader()
    
    # テストしたい銘柄リスト
    tickers = ["NVDA", "TSLA", "MSFT"]
    benchmark = "SPY"
    start_date = "2020-01-01"
    end_date = "2023-12-31"

    for ticker in tickers:
        print(f"\n{'='*20} Testing: {ticker} {'='*20}")
        engine = BacktestEngine(initial_capital=10000.0)
        
        # 2. Get Data
        try:
            df = loader.load(ticker)
            bench = loader.load(benchmark)
        except FileNotFoundError:
            df = loader.download(ticker, start=start_date, end=end_date)
            bench = loader.download(benchmark, start=start_date, end=end_date)

        # 3. Run Backtest
        trade_log = engine.run(df, bench)

        # 4. Results
        print(f"--- Results for {ticker} ---")
        print(f"Final Capital: ${engine.cash:.2f}")
        if not trade_log.empty:
            closed_trades = trade_log[trade_log['Type'] == 'Sell']
            total_pnl = closed_trades['PnL'].sum()
            win_rate = (closed_trades['PnL'] > 0).mean() * 100
            
            print(f"Total PnL: ${total_pnl:.2f}")
            print(f"Win Rate: {win_rate:.1f}%")
            print(f"Total Trades: {len(closed_trades)}")
            
            # 5. Visualization (Overwrite for the last one or use ticker in name)
            plot_results(df, trade_log, engine.equity_curve, ticker)
        else:
            print("No trades executed.")

if __name__ == "__main__":
    main()
