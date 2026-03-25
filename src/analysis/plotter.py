import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_results(df: pd.DataFrame, trade_log: pd.DataFrame, equity_curve: list, ticker: str):
    """
    Visualizes the backtest results: Price, Trades, and Equity Curve.
    """
    # Create Equity DataFrame
    equity_df = pd.DataFrame(equity_curve)
    equity_df.set_index('Date', inplace=True)
    
    # Create Subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.7, 0.3],
                        subplot_titles=(f"{ticker} Price & Trades", "Equity Curve"))

    # 1. Price Chart
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'],
                                 name='Price'), row=1, col=1)

    # Add SMA
    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
    if 'SMA_200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='blue', width=1), name='SMA 200'), row=1, col=1)

    # 2. Trades (Markers)
    # Buy
    buys = trade_log[trade_log['Type'] == 'Buy']
    fig.add_trace(go.Scatter(x=buys['Date'], y=buys['Price'], mode='markers',
                             marker=dict(symbol='triangle-up', color='green', size=10),
                             name='Buy'), row=1, col=1)
    
    # Sell
    sells = trade_log[trade_log['Type'] == 'Sell']
    fig.add_trace(go.Scatter(x=sells['Date'], y=sells['Price'], mode='markers',
                             marker=dict(symbol='triangle-down', color='red', size=10),
                             name='Sell'), row=1, col=1)

    # 3. Equity Curve
    fig.add_trace(go.Scatter(x=equity_df.index, y=equity_df['Equity'], 
                             line=dict(color='green', width=2), name='Equity'), row=2, col=1)

    # Layout
    fig.update_layout(height=800, title_text=f"Backtest Analysis: {ticker}", xaxis_rangeslider_visible=False)
    
    # Save to HTML
    output_file = "backtest_result.html"
    fig.write_html(output_file)
    print(f"Chart saved to {output_file}")
