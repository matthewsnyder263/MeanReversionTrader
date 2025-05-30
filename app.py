import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from strategy import MeanReversionStrategy
from utils import calculate_rsi, format_percentage, validate_ticker
from database import init_database, save_backtest_results, get_backtest_history, get_backtest_details, get_ticker_statistics
from strategy_playground import render_strategy_playground

# Page configuration
st.set_page_config(
    page_title="Mean Reversion Strategy Backtester",
    page_icon="📈",
    layout="wide"
)

# Navigation
page = st.sidebar.radio("Navigation", ["🏠 Backtester", "🎮 Strategy Playground"], index=0)

if page == "🎮 Strategy Playground":
    render_strategy_playground()
else:
    # Title and description
    st.title("📈 Mean Reversion Strategy Backtester")
    st.markdown("""
    This app backtests a mean reversion strategy that buys after consecutive red days when RSI is below a threshold,
    and sells at a specified gain/loss percentage.
    """)

    # Initialize database
    try:
        init_database()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")

    # Initialize session state
    if 'results_data' not in st.session_state:
        st.session_state.results_data = None
    if 'chart_data' not in st.session_state:
        st.session_state.chart_data = {}
    if 'all_trades' not in st.session_state:
        st.session_state.all_trades = {}

    # Store current parameters in session state for playground
    if 'rsi_threshold' not in st.session_state:
        st.session_state.rsi_threshold = 30
    if 'exit_percentage' not in st.session_state:
        st.session_state.exit_percentage = 5.0
    if 'red_days' not in st.session_state:
        st.session_state.red_days = 2

    # Sidebar for strategy parameters
    st.sidebar.header("Strategy Parameters")

    # RSI Threshold
    rsi_threshold = st.sidebar.slider(
        "RSI Threshold", 
        min_value=10, 
        max_value=50, 
        value=st.session_state.rsi_threshold, 
        help="Buy when RSI is below this value"
    )
    st.session_state.rsi_threshold = rsi_threshold

    # Gain/Loss Exit Percentage
    exit_percentage = st.sidebar.slider(
        "Exit Gain/Loss %", 
        min_value=1.0, 
        max_value=10.0, 
        value=st.session_state.exit_percentage, 
        step=0.5,
        help="Sell when stock moves +/- this percentage from buy price"
    )
    st.session_state.exit_percentage = exit_percentage

    # Red Days Before Buy
    red_days = st.sidebar.slider(
        "Red Days Before Buy", 
        min_value=1, 
        max_value=5, 
        value=st.session_state.red_days,
        help="Number of consecutive red days before triggering a buy signal"
    )
    st.session_state.red_days = red_days

    # Date range selection
    st.sidebar.header("Backtest Period")
    col1, col2 = st.sidebar.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now()
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )

    # Watchlist input
    st.sidebar.header("Stock Selection")
    watchlist_input = st.sidebar.text_area(
    "Watchlist (comma-separated)",
    value="AAPL,MSFT,GOOGL,TSLA,AMZN",
    help="Enter stock symbols separated by commas"
)

    # Sort options
    sort_by = st.sidebar.selectbox(
    "Sort Results By",
    ["Average Return", "Win Rate", "Number of Trades"],
    help="How to sort the results table"
)

    # Run strategy button - make it more prominent
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Ready to Test?")
    run_strategy = st.sidebar.button("🚀 Run Strategy", type="primary", use_container_width=True)

    # Main content area
    if run_strategy:
    if start_date >= end_date:
        st.error("Start date must be before end date!")
    else:
        # Parse watchlist
        tickers = [ticker.strip().upper() for ticker in watchlist_input.split(",") if ticker.strip()]
        
        if not tickers:
            st.error("Please enter at least one ticker symbol!")
        else:
            # Initialize strategy
            strategy = MeanReversionStrategy(
                rsi_threshold=rsi_threshold,
                exit_percentage=exit_percentage / 100,  # Convert to decimal
                red_days=red_days
            )
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            chart_data = {}
            all_trades = {}
            
            for i, ticker in enumerate(tickers):
                status_text.text(f"Processing {ticker}...")
                progress_bar.progress((i + 1) / len(tickers))
                
                try:
                    # Validate ticker
                    if not validate_ticker(ticker):
                        st.warning(f"⚠️ Invalid or delisted ticker: {ticker}")
                        continue
                    
                    # Download data
                    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                    
                    if data is None or data.shape[0] == 0:
                        st.warning(f"⚠️ No data available for {ticker}")
                        continue
                    
                    # Run backtest
                    trades, signals = strategy.backtest(data, ticker)
                    
                    if trades:
                        # Calculate metrics
                        returns = [trade['return_pct'] for trade in trades]
                        avg_return = np.mean(returns)
                        win_rate = len([r for r in returns if r > 0]) / len(returns)
                        num_trades = len(trades)
                        total_return = np.sum(returns)
                        
                        results.append({
                            'Ticker': ticker,
                            'Trades': num_trades,
                            'Avg Return (%)': avg_return,
                            'Win Rate (%)': win_rate * 100,
                            'Total Return (%)': total_return,
                            'Best Trade (%)': max(returns),
                            'Worst Trade (%)': min(returns)
                        })
                        
                        # Store chart data and trades
                        chart_data[ticker] = {
                            'data': data,
                            'trades': trades,
                            'signals': signals
                        }
                        all_trades[ticker] = trades
                    
                except Exception as e:
                    st.warning(f"⚠️ Error processing {ticker}: {str(e)}")
                    continue
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            if results:
                # Store results in session state
                results_df = pd.DataFrame(results)
                st.session_state.results_data = results_df
                st.session_state.chart_data = chart_data
                st.session_state.all_trades = all_trades
                
                # Save to database
                try:
                    strategy_params = {
                        'rsi_threshold': rsi_threshold,
                        'exit_percentage': exit_percentage / 100,
                        'red_days': red_days,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    
                    backtest_id = save_backtest_results(
                        strategy_params, tickers, results_df, all_trades, chart_data
                    )
                    st.session_state.last_backtest_id = backtest_id
                    
                except Exception as e:
                    st.warning(f"Results saved locally but database save failed: {str(e)}")
                
                st.success(f"✅ Strategy completed! Processed {len(results)} tickers successfully.")
            else:
                st.error("❌ No successful backtests. Please check your ticker symbols and date range.")

    # Display results if available
    if st.session_state.results_data is not None:
    st.header("📊 Backtest Results")
    
    # Sort results
    results_df = st.session_state.results_data.copy()
    
    if sort_by == "Average Return":
        results_df = results_df.sort_values("Avg Return (%)", ascending=False)
    elif sort_by == "Win Rate":
        results_df = results_df.sort_values("Win Rate (%)", ascending=False)
    else:  # Number of Trades
        results_df = results_df.sort_values("Trades", ascending=False)
    
    # Format the dataframe for display
    display_df = results_df.copy()
    for col in ['Avg Return (%)', 'Win Rate (%)', 'Total Return (%)', 'Best Trade (%)', 'Worst Trade (%)']:
        if col in display_df.columns:
            if 'Win Rate' in col:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%")
            else:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")
    
    # Display results table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_win_rate = results_df['Win Rate (%)'].mean()
        st.metric("Average Win Rate", f"{avg_win_rate:.1f}%")
    
    with col2:
        avg_return = results_df['Avg Return (%)'].mean()
        st.metric("Average Return", f"{avg_return:.2f}%")
    
    with col3:
        total_trades = results_df['Trades'].sum()
        st.metric("Total Trades", f"{total_trades}")
    
    with col4:
        profitable_tickers = len(results_df[results_df['Avg Return (%)'] > 0])
        st.metric("Profitable Tickers", f"{profitable_tickers}/{len(results_df)}")
    
    # Chart section
    st.header("📈 Trading Charts")
    
    # Ticker selection for charts
    available_tickers = list(st.session_state.chart_data.keys())
    selected_tickers = st.multiselect(
        "Select tickers to display charts:",
        available_tickers,
        default=available_tickers[:3] if len(available_tickers) >= 3 else available_tickers,
        help="Select up to 5 tickers for chart display"
    )
    
    if selected_tickers:
        # Limit to 5 charts for performance
        if len(selected_tickers) > 5:
            st.warning("⚠️ Displaying only the first 5 selected tickers for performance reasons.")
            selected_tickers = selected_tickers[:5]
        
        for ticker in selected_tickers:
            st.subheader(f"{ticker} - Trading Signals")
            
            chart_info = st.session_state.chart_data[ticker]
            data = chart_info['data']
            trades = chart_info['trades']
            
            # Create plotly chart
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=[f'{ticker} Price with Signals', 'RSI'],
                row_heights=[0.7, 0.3]
            )
            
            # Price chart
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Price'
                ),
                row=1, col=1
            )
            
            # Add buy signals
            buy_dates = [trade['buy_date'] for trade in trades]
            buy_prices = [trade['buy_price'] for trade in trades]
            
            if buy_dates:
                fig.add_trace(
                    go.Scatter(
                        x=buy_dates,
                        y=buy_prices,
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=10, color='green'),
                        name='Buy Signal'
                    ),
                    row=1, col=1
                )
            
            # Add sell signals
            sell_dates = [trade['sell_date'] for trade in trades if trade['sell_date'] is not None]
            sell_prices = [trade['sell_price'] for trade in trades if trade['sell_price'] is not None]
            
            if sell_dates:
                fig.add_trace(
                    go.Scatter(
                        x=sell_dates,
                        y=sell_prices,
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=10, color='red'),
                        name='Sell Signal'
                    ),
                    row=1, col=1
                )
            
            # RSI chart
            rsi_values = calculate_rsi(data['Close'])
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=rsi_values,
                    name='RSI',
                    line=dict(color='purple')
                ),
                row=2, col=1
            )
            
            # Add RSI threshold line
            fig.add_hline(
                y=rsi_threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"RSI Threshold: {rsi_threshold}",
                row=2, col=1
            )
            
            # Add RSI overbought/oversold lines
            fig.add_hline(y=70, line_dash="dot", line_color="gray", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="gray", row=2, col=1)
            
            # Update layout
            fig.update_layout(
                height=600,
                showlegend=True,
                xaxis_rangeslider_visible=False
            )
            
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade details for this ticker
            ticker_trades = trades
            if ticker_trades:
                st.subheader(f"{ticker} - Trade Details")
                
                trade_details = []
                for trade in ticker_trades:
                    trade_details.append({
                        'Buy Date': trade['buy_date'].strftime('%Y-%m-%d') if trade['buy_date'] else 'N/A',
                        'Buy Price': f"${trade['buy_price']:.2f}",
                        'Sell Date': trade['sell_date'].strftime('%Y-%m-%d') if trade['sell_date'] else 'Open',
                        'Sell Price': f"${trade['sell_price']:.2f}" if trade['sell_price'] else 'N/A',
                        'Return (%)': f"{trade['return_pct']:.2f}%" if trade['return_pct'] is not None else 'N/A',
                        'Days Held': trade['days_held'] if trade['days_held'] is not None else 'N/A'
                    })
                
                st.dataframe(
                    pd.DataFrame(trade_details),
                    use_container_width=True,
                    hide_index=True
                )

    # Database History Section
    st.markdown("---")
    st.header("📚 Backtest History")

    try:
    history_df = get_backtest_history(limit=10)
    if not history_df.empty:
        st.subheader("Recent Backtests")
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No backtest history available yet. Run your first strategy above!")
    except Exception as e:
    st.info("Database history not available - results will be saved locally only.")

    # Footer
    st.markdown("---")
    st.markdown("""
**Strategy Summary:** Buy after {red_days} consecutive red days when RSI < {rsi_threshold}, 
sell at ±{exit_percentage}% gain/loss.
""".format(
    red_days=red_days if 'red_days' in locals() else 2,
    rsi_threshold=rsi_threshold if 'rsi_threshold' in locals() else 30,
    exit_percentage=exit_percentage if 'exit_percentage' in locals() else 5.0
))
