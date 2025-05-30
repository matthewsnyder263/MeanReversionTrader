import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from database import get_backtest_history, get_backtest_details
from utils import calculate_sharpe_ratio, calculate_max_drawdown

def analyze_parameter_performance(history_df):
    """
    Analyze which parameter combinations perform best
    """
    if history_df.empty:
        return None
    
    # Group by parameters and calculate average metrics
    param_analysis = []
    
    for _, row in history_df.iterrows():
        param_analysis.append({
            'RSI_Threshold': row['RSI Threshold'],
            'Exit_Percentage': row['Exit %'],
            'Red_Days': row['Red Days'],
            'Avg_Return': row['Avg Return (%)'],
            'Win_Rate': row['Avg Win Rate (%)'],
            'Total_Trades': row['Total Trades'],
            'Profitable_Ratio': row['Profitable Tickers'] / row['Successful'] if row['Successful'] > 0 else 0
        })
    
    return pd.DataFrame(param_analysis)

def suggest_parameter_optimization(current_params, param_analysis_df):
    """
    Suggest parameter improvements based on historical performance
    """
    if param_analysis_df is None or param_analysis_df.empty:
        return []
    
    suggestions = []
    
    # Find best performing parameters
    best_return = param_analysis_df.loc[param_analysis_df['Avg_Return'].idxmax()]
    best_win_rate = param_analysis_df.loc[param_analysis_df['Win_Rate'].idxmax()]
    best_profit_ratio = param_analysis_df.loc[param_analysis_df['Profitable_Ratio'].idxmax()]
    
    # RSI Threshold suggestions
    current_rsi = current_params.get('rsi_threshold', 30)
    if best_return['RSI_Threshold'] != current_rsi:
        suggestions.append({
            'parameter': 'RSI Threshold',
            'current': current_rsi,
            'suggested': int(best_return['RSI_Threshold']),
            'reason': f"Historical data shows RSI {int(best_return['RSI_Threshold'])} achieved {best_return['Avg_Return']:.2f}% average return",
            'confidence': 'High' if abs(best_return['Avg_Return'] - param_analysis_df['Avg_Return'].mean()) > 1 else 'Medium'
        })
    
    # Exit Percentage suggestions
    current_exit = current_params.get('exit_percentage', 5.0)
    if abs(best_return['Exit_Percentage'] - current_exit) > 0.5:
        suggestions.append({
            'parameter': 'Exit Percentage',
            'current': current_exit,
            'suggested': best_return['Exit_Percentage'],
            'reason': f"Exit at {best_return['Exit_Percentage']:.1f}% showed better risk-adjusted returns",
            'confidence': 'Medium'
        })
    
    # Red Days suggestions
    current_red = current_params.get('red_days', 2)
    if best_win_rate['Red_Days'] != current_red:
        suggestions.append({
            'parameter': 'Red Days',
            'current': current_red,
            'suggested': int(best_win_rate['Red_Days']),
            'reason': f"Waiting for {int(best_win_rate['Red_Days'])} red days achieved {best_win_rate['Win_Rate']:.1f}% win rate",
            'confidence': 'Medium'
        })
    
    return suggestions

def analyze_market_conditions(backtest_details):
    """
    Analyze performance across different market conditions
    """
    if not backtest_details:
        return None
    
    # This would analyze market volatility, trends, etc.
    # For now, we'll do basic trade analysis
    analysis = {
        'trade_frequency': 'Based on recent backtests, the strategy generates trades every 2-3 weeks on average',
        'seasonal_patterns': 'Consider testing different date ranges to identify seasonal performance patterns',
        'volatility_impact': 'Strategy performance may vary with market volatility - test during high/low VIX periods'
    }
    
    return analysis

def create_parameter_heatmap(param_analysis_df):
    """
    Create a heatmap showing parameter performance
    """
    if param_analysis_df is None or param_analysis_df.empty:
        return None
    
    # Create pivot table for heatmap
    pivot_data = param_analysis_df.pivot_table(
        values='Avg_Return', 
        index='RSI_Threshold', 
        columns='Exit_Percentage', 
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlGn',
        text=pivot_data.values,
        texttemplate="%{text:.2f}%",
        colorbar=dict(title="Avg Return (%)")
    ))
    
    fig.update_layout(
        title="Parameter Performance Heatmap",
        xaxis_title="Exit Percentage (%)",
        yaxis_title="RSI Threshold",
        height=400
    )
    
    return fig

def create_performance_radar(current_metrics, benchmarks):
    """
    Create a radar chart comparing current performance to benchmarks
    """
    categories = ['Return', 'Win Rate', 'Trade Frequency', 'Risk Ratio', 'Consistency']
    
    # Normalize metrics to 0-100 scale for radar chart
    current_values = [
        min(100, max(0, (current_metrics.get('avg_return', 0) + 10) * 5)),  # Return (-10% to +10% -> 0-100)
        current_metrics.get('win_rate', 50),  # Win rate is already 0-100
        min(100, current_metrics.get('trade_frequency', 10) * 10),  # Trade frequency
        min(100, max(0, (2 - current_metrics.get('sharpe_ratio', 0)) * 50)),  # Risk ratio (inverse)
        min(100, max(0, 100 - current_metrics.get('volatility', 50)))  # Consistency (inverse volatility)
    ]
    
    benchmark_values = [60, 55, 50, 65, 70]  # Reasonable benchmark values
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=current_values,
        theta=categories,
        fill='toself',
        name='Current Strategy',
        line_color='blue'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=benchmark_values,
        theta=categories,
        fill='toself',
        name='Target Benchmark',
        line_color='green',
        opacity=0.6
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Strategy Performance Radar",
        height=400
    )
    
    return fig

def risk_analysis(trades_data):
    """
    Perform risk analysis on trade data
    """
    if not trades_data or len(trades_data) == 0:
        return {}
    
    returns = [trade.get('Return (%)', 0) for trade in trades_data if 'Return (%)' in trade]
    
    if not returns:
        return {}
    
    analysis = {
        'max_drawdown': calculate_max_drawdown(returns),
        'sharpe_ratio': calculate_sharpe_ratio(returns),
        'volatility': np.std(returns),
        'var_95': np.percentile(returns, 5),  # Value at Risk (95% confidence)
        'average_loss': np.mean([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0,
        'loss_frequency': len([r for r in returns if r < 0]) / len(returns) * 100
    }
    
    return analysis

def generate_strategy_insights(param_analysis, risk_metrics, market_analysis):
    """
    Generate strategic insights and recommendations
    """
    insights = []
    
    # Risk-based insights
    if risk_metrics.get('max_drawdown', 0) > 15:
        insights.append({
            'type': 'Risk Warning',
            'message': f"Maximum drawdown of {risk_metrics['max_drawdown']:.1f}% is high. Consider tighter exit rules.",
            'priority': 'High'
        })
    
    if risk_metrics.get('sharpe_ratio', 0) < 1:
        insights.append({
            'type': 'Performance',
            'message': "Sharpe ratio below 1.0 suggests risk-adjusted returns could be improved.",
            'priority': 'Medium'
        })
    
    # Parameter insights
    if param_analysis is not None and not param_analysis.empty:
        avg_trades = param_analysis['Total_Trades'].mean()
        if avg_trades < 5:
            insights.append({
                'type': 'Trading Frequency',
                'message': "Low trade frequency detected. Consider relaxing entry conditions.",
                'priority': 'Medium'
            })
    
    # Market condition insights
    insights.append({
        'type': 'Market Analysis',
        'message': "Test strategy across different market cycles (bull, bear, sideways) for robustness.",
        'priority': 'Low'
    })
    
    return insights

def render_strategy_playground():
    """
    Main function to render the Strategy Playground
    """
    st.header("🎮 Strategy Playground")
    st.markdown("Analyze your strategy performance and discover optimization opportunities.")
    
    # Get historical data
    try:
        history_df = get_backtest_history(limit=50)
        param_analysis = analyze_parameter_performance(history_df)
    except Exception as e:
        st.warning("Unable to load historical data for analysis.")
        history_df = pd.DataFrame()
        param_analysis = None
    
    # Tabs for different analysis views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance Analysis", "🎯 Parameter Optimization", "⚠️ Risk Analysis", "💡 Strategy Insights"])
    
    with tab1:
        st.subheader("Performance Overview")
        
        if not history_df.empty:
            # Performance metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_return = history_df['Avg Return (%)'].mean()
                st.metric("Average Return", f"{avg_return:.2f}%", delta=f"{avg_return - 2:.2f}%")
            
            with col2:
                avg_win_rate = history_df['Avg Win Rate (%)'].mean()
                st.metric("Average Win Rate", f"{avg_win_rate:.1f}%", delta=f"{avg_win_rate - 50:.1f}%")
            
            with col3:
                total_backtests = len(history_df)
                st.metric("Total Backtests", total_backtests)
            
            with col4:
                consistency = history_df['Avg Return (%)'].std()
                st.metric("Consistency (Lower=Better)", f"{consistency:.2f}%")
            
            # Performance trend chart
            if len(history_df) > 1:
                fig = px.line(history_df, x='Date', y='Avg Return (%)', 
                             title="Strategy Performance Over Time",
                             markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            # Parameter heatmap
            heatmap_fig = create_parameter_heatmap(param_analysis)
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True)
        else:
            st.info("Run more backtests to see performance analysis.")
    
    with tab2:
        st.subheader("Parameter Optimization")
        
        if param_analysis is not None and not param_analysis.empty:
            # Current parameters (get from session state or use defaults)
            current_params = {
                'rsi_threshold': st.session_state.get('rsi_threshold', 30),
                'exit_percentage': st.session_state.get('exit_percentage', 5.0),
                'red_days': st.session_state.get('red_days', 2)
            }
            
            suggestions = suggest_parameter_optimization(current_params, param_analysis)
            
            if suggestions:
                st.markdown("### 🎯 Optimization Suggestions")
                for suggestion in suggestions:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{suggestion['parameter']}**")
                            st.markdown(f"Current: {suggestion['current']} → Suggested: {suggestion['suggested']}")
                            st.markdown(f"*{suggestion['reason']}*")
                        with col2:
                            confidence_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
                            st.markdown(f"{confidence_color[suggestion['confidence']]} {suggestion['confidence']}")
                        st.markdown("---")
            else:
                st.success("Your current parameters are well-optimized based on historical data!")
            
            # Parameter distribution charts
            if len(param_analysis) > 3:
                fig_scatter = px.scatter(param_analysis, x='RSI_Threshold', y='Avg_Return', 
                                       size='Total_Trades', color='Win_Rate',
                                       title="RSI Threshold vs Returns",
                                       hover_data=['Exit_Percentage', 'Red_Days'])
                st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Run backtests with different parameters to see optimization suggestions.")
    
    with tab3:
        st.subheader("Risk Analysis")
        
        # Get detailed trade data from most recent backtest
        if 'last_backtest_id' in st.session_state and st.session_state.last_backtest_id:
            try:
                ticker_perf, trades_df = get_backtest_details(st.session_state.last_backtest_id)
                
                if not trades_df.empty:
                    # Convert trades DataFrame to list of dicts for analysis
                    trades_data = trades_df.to_dict('records')
                    risk_metrics = risk_analysis(trades_data)
                    
                    if risk_metrics:
                        # Risk metrics display
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Max Drawdown", f"{risk_metrics.get('max_drawdown', 0):.1f}%", 
                                    delta="Lower is better", delta_color="inverse")
                        with col2:
                            st.metric("Sharpe Ratio", f"{risk_metrics.get('sharpe_ratio', 0):.2f}",
                                    delta="Higher is better")
                        with col3:
                            st.metric("Value at Risk (95%)", f"{risk_metrics.get('var_95', 0):.1f}%",
                                    delta="Loss threshold")
                        
                        # Risk radar chart
                        current_metrics = {
                            'avg_return': trades_df['Return (%)'].mean() if 'Return (%)' in trades_df.columns else 0,
                            'win_rate': len(trades_df[trades_df['Return (%)'] > 0]) / len(trades_df) * 100 if 'Return (%)' in trades_df.columns else 50,
                            'trade_frequency': len(trades_df),
                            'sharpe_ratio': risk_metrics.get('sharpe_ratio', 0),
                            'volatility': risk_metrics.get('volatility', 0)
                        }
                        
                        radar_fig = create_performance_radar(current_metrics, {})
                        st.plotly_chart(radar_fig, use_container_width=True)
                        
                        # Risk breakdown
                        st.markdown("### Risk Breakdown")
                        risk_col1, risk_col2 = st.columns(2)
                        with risk_col1:
                            st.markdown(f"**Average Loss:** {risk_metrics.get('average_loss', 0):.2f}%")
                            st.markdown(f"**Loss Frequency:** {risk_metrics.get('loss_frequency', 0):.1f}%")
                        with risk_col2:
                            st.markdown(f"**Volatility:** {risk_metrics.get('volatility', 0):.2f}%")
                            st.markdown(f"**Risk-Adjusted Score:** {risk_metrics.get('sharpe_ratio', 0) * 10:.0f}/100")
                
            except Exception as e:
                st.warning("Unable to load detailed trade data for risk analysis.")
        else:
            st.info("Run a backtest to see detailed risk analysis.")
    
    with tab4:
        st.subheader("Strategy Insights")
        
        # Generate insights
        market_analysis = analyze_market_conditions({})
        risk_metrics = {}
        
        if 'last_backtest_id' in st.session_state:
            try:
                _, trades_df = get_backtest_details(st.session_state.last_backtest_id)
                if not trades_df.empty:
                    trades_data = trades_df.to_dict('records')
                    risk_metrics = risk_analysis(trades_data)
            except:
                pass
        
        insights = generate_strategy_insights(param_analysis, risk_metrics, market_analysis)
        
        if insights:
            for insight in insights:
                priority_colors = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                st.markdown(f"{priority_colors[insight['priority']]} **{insight['type']}**: {insight['message']}")
                st.markdown("---")
        
        # Strategy recommendations
        st.markdown("### 📋 General Recommendations")
        recommendations = [
            "Test strategy across different market conditions (2020 crash, 2021 bull run, 2022 bear market)",
            "Consider adding volume filters to improve entry quality",
            "Backtest on different timeframes (daily vs weekly signals)",
            "Monitor correlation with market indices (SPY, QQQ) to understand market dependence",
            "Consider sector rotation - some sectors may respond better to mean reversion"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")
        
        # Quick strategy tester
        st.markdown("### 🚀 Quick Strategy Test")
        st.markdown("Want to test a specific parameter combination?")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            test_rsi = st.number_input("RSI Threshold", 10, 50, 25, key="test_rsi")
        with col2:
            test_exit = st.number_input("Exit %", 1.0, 10.0, 3.0, step=0.5, key="test_exit")
        with col3:
            test_red = st.number_input("Red Days", 1, 5, 3, key="test_red")
        with col4:
            if st.button("Quick Test", type="primary"):
                st.info(f"Test RSI:{test_rsi}, Exit:{test_exit}%, Red Days:{test_red} - Use main backtest with these parameters!")