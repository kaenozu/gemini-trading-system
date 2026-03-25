from src.execution.portfolio_engine import PortfolioEngine
import pandas as pd
import plotly.graph_objects as go

def main():
    # 1. Setup Universe (NASDAQ 100 Main Tickers)
    # Selected for Rakuten-availability and Liquidity
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "PEP", "COST",
        "CSCO", "TMUS", "ADBE", "QCOM", "NFLX", "AMD", "INTC", "TXN", "AMAT", "HON",
        "ISRG", "BKNG", "VRTX", "GILD", "ADP", "SBUX", "MDLZ", "REGN", "PYPL", "ADI"
    ]
    benchmark = "SPY"
    start_date = "2020-01-01"
    end_date = "2023-12-31"

    engine = PortfolioEngine(initial_capital=100000.0, max_positions=10) # 10 trades at once
    
    # 2. Run Portfolio Backtest
    portfolio_log, total_equity = engine.run_multi(tickers, benchmark, start_date, end_date)

    # 3. Analyze Results
    print("\n" + "="*40)
    print("PORTFOLIO BACKTEST RESULTS (30 TICKERS)")
    print("="*40)
    
    if not portfolio_log.empty:
        closed_trades = portfolio_log[portfolio_log['Type'] == 'Sell']
        total_pnl = closed_trades['PnL'].sum()
        win_rate = (closed_trades['PnL'] > 0).mean() * 100
        
        print(f"Total Trades: {len(closed_trades)}")
        print(f"Portfolio Win Rate: {win_rate:.1f}%")
        print(f"Total Portfolio PnL: ${total_pnl:.2f}")
        print(f"Final Portfolio Value: ${total_equity.iloc[-1]:.2f}")
        
        # Calculate Max Drawdown
        peak = total_equity.expanding(min_periods=1).max()
        drawdown = (total_equity - peak) / peak
        max_drawdown = drawdown.min() * 100
        print(f"Max Portfolio Drawdown: {max_drawdown:.1f}%")

        # 4. Save Combined Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=total_equity.index, y=total_equity.values, name='Portfolio Equity'))
        fig.update_layout(title='Portfolio Equity Curve (30 Tickers)', xaxis_title='Date', yaxis_title='Equity ($)')
        fig.write_html("portfolio_result.html")
        print("Portfolio chart saved to portfolio_result.html")
    else:
        print("No trades executed across the universe.")

if __name__ == "__main__":
    main()
