import sys
import pandas as pd
from src.execution.portfolio_engine import PortfolioEngine
from src.analysis.scanner import Scanner

# Universe definition
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "PEP", "COST",
    "CSCO", "TMUS", "ADBE", "QCOM", "NFLX", "AMD", "INTC", "TXN", "AMAT", "HON",
    "ISRG", "BKNG", "VRTX", "GILD", "ADP", "SBUX", "MDLZ", "REGN", "PYPL", "ADI"
]

def run_backtest():
    print("Running Realistic Portfolio Backtest...")
    engine = PortfolioEngine(initial_capital=100000.0, max_positions=10)
    portfolio_log, total_equity = engine.run_multi(TICKERS, "SPY", "2020-01-01", "2023-12-31")
    
    if not portfolio_log.empty:
        closed = portfolio_log[portfolio_log['Type'] == 'Sell']
        win_rate = (closed['PnL'] > 0).mean() * 100
        total_pnl = closed['PnL'].sum()
        total_comm = portfolio_log['Commission'].sum()
        
        print("\n" + "="*40)
        print("FINAL REPORT (WITH COSTS)")
        print("="*40)
        print(f"Total Trades: {len(closed)}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Total PnL (Net): ${total_pnl:.2f}")
        print(f"Total Commission: ${total_comm:.2f}")
        print(f"Final Value: ${total_equity.iloc[-1]:.2f}")
    else:
        print("No trades found.")

def run_scan():
    print("Running Daily Market Scan...")
    scanner = Scanner(TICKERS)
    results = scanner.scan()
    
    print("\n" + "="*40)
    print("TODAY'S OPPORTUNITIES")
    print("="*40)
    if not results.empty:
        print(results)
    else:
        print("No active signals found today.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "backtest":
            run_backtest()
        elif mode == "scan":
            run_scan()
        else:
            print("Usage: python main.py [backtest|scan]")
    else:
        # Default to scan for actionability
        run_scan()
