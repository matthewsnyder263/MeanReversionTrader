import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()

class BacktestRun(Base):
    """Store backtest run configurations and summary results"""
    __tablename__ = "backtest_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, default=datetime.utcnow)
    strategy_name = Column(String, default="Mean Reversion")
    
    # Strategy parameters
    rsi_threshold = Column(Integer)
    exit_percentage = Column(Float)
    red_days = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Tickers tested
    tickers = Column(Text)  # JSON string of ticker list
    
    # Summary metrics
    total_tickers = Column(Integer)
    successful_tickers = Column(Integer)
    total_trades = Column(Integer)
    avg_win_rate = Column(Float)
    avg_return = Column(Float)
    profitable_tickers = Column(Integer)

class TradeRecord(Base):
    """Store individual trade records"""
    __tablename__ = "trade_records"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer)
    
    # Trade details
    ticker = Column(String)
    buy_date = Column(DateTime)
    buy_price = Column(Float)
    sell_date = Column(DateTime)
    sell_price = Column(Float)
    return_pct = Column(Float)
    days_held = Column(Integer)
    exit_reason = Column(String)

class TickerPerformance(Base):
    """Store performance metrics per ticker per backtest"""
    __tablename__ = "ticker_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer)
    ticker = Column(String)
    
    # Performance metrics
    num_trades = Column(Integer)
    avg_return_pct = Column(Float)
    win_rate_pct = Column(Float)
    total_return_pct = Column(Float)
    best_trade_pct = Column(Float)
    worst_trade_pct = Column(Float)

def init_database():
    """Initialize database tables"""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
    else:
        raise Exception("Database not available")

def save_backtest_results(strategy_params, tickers, results_df, all_trades, chart_data):
    """
    Save backtest results to database
    
    Args:
        strategy_params (dict): Strategy configuration parameters
        tickers (list): List of tickers tested
        results_df (pd.DataFrame): Results summary dataframe
        all_trades (dict): Dictionary of trades by ticker
        chart_data (dict): Chart data by ticker
    
    Returns:
        int: ID of the saved backtest run
    """
    if SessionLocal is None:
        raise Exception("Database not available")
    
    db = SessionLocal()
    
    try:
        # Create backtest run record
        backtest_run = BacktestRun(
            rsi_threshold=strategy_params['rsi_threshold'],
            exit_percentage=strategy_params['exit_percentage'],
            red_days=strategy_params['red_days'],
            start_date=strategy_params['start_date'],
            end_date=strategy_params['end_date'],
            tickers=json.dumps(tickers),
            total_tickers=len(tickers),
            successful_tickers=len(results_df),
            total_trades=results_df['Trades'].sum() if not results_df.empty else 0,
            avg_win_rate=results_df['Win Rate (%)'].mean() if not results_df.empty else 0,
            avg_return=results_df['Avg Return (%)'].mean() if not results_df.empty else 0,
            profitable_tickers=len(results_df[results_df['Avg Return (%)'] > 0]) if not results_df.empty else 0
        )
        
        db.add(backtest_run)
        db.commit()
        db.refresh(backtest_run)
        
        # Save ticker performance records
        for _, row in results_df.iterrows():
            ticker_perf = TickerPerformance(
                backtest_run_id=backtest_run.id,
                ticker=row['Ticker'],
                num_trades=row['Trades'],
                avg_return_pct=row['Avg Return (%)'],
                win_rate_pct=row['Win Rate (%)'],
                total_return_pct=row['Total Return (%)'],
                best_trade_pct=row['Best Trade (%)'],
                worst_trade_pct=row['Worst Trade (%)']
            )
            db.add(ticker_perf)
        
        # Save individual trade records
        for ticker, trades in all_trades.items():
            for trade in trades:
                trade_record = TradeRecord(
                    backtest_run_id=backtest_run.id,
                    ticker=ticker,
                    buy_date=trade['buy_date'],
                    buy_price=trade['buy_price'],
                    sell_date=trade['sell_date'],
                    sell_price=trade['sell_price'],
                    return_pct=trade['return_pct'],
                    days_held=trade['days_held'],
                    exit_reason=trade['exit_reason']
                )
                db.add(trade_record)
        
        db.commit()
        return backtest_run.id
    
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_backtest_history(limit=10):
    """
    Retrieve recent backtest runs
    
    Args:
        limit (int): Number of recent runs to retrieve
    
    Returns:
        pd.DataFrame: Historical backtest runs
    """
    db = SessionLocal()
    
    try:
        runs = db.query(BacktestRun).order_by(BacktestRun.run_date.desc()).limit(limit).all()
        
        history_data = []
        for run in runs:
            history_data.append({
                'ID': run.id,
                'Date': run.run_date.strftime('%Y-%m-%d %H:%M'),
                'RSI Threshold': run.rsi_threshold,
                'Exit %': run.exit_percentage,
                'Red Days': run.red_days,
                'Period': f"{run.start_date.strftime('%Y-%m-%d')} to {run.end_date.strftime('%Y-%m-%d')}",
                'Tickers': len(json.loads(run.tickers)),
                'Successful': run.successful_tickers,
                'Total Trades': run.total_trades,
                'Avg Win Rate (%)': round(run.avg_win_rate, 1) if run.avg_win_rate else 0,
                'Avg Return (%)': round(run.avg_return, 2) if run.avg_return else 0,
                'Profitable Tickers': run.profitable_tickers
            })
        
        return pd.DataFrame(history_data)
    
    finally:
        db.close()

def get_backtest_details(backtest_id):
    """
    Get detailed results for a specific backtest run
    
    Args:
        backtest_id (int): ID of the backtest run
    
    Returns:
        tuple: (ticker_performance_df, trades_df)
    """
    db = SessionLocal()
    
    try:
        # Get ticker performance
        ticker_perfs = db.query(TickerPerformance).filter(
            TickerPerformance.backtest_run_id == backtest_id
        ).all()
        
        ticker_data = []
        for perf in ticker_perfs:
            ticker_data.append({
                'Ticker': perf.ticker,
                'Trades': perf.num_trades,
                'Avg Return (%)': perf.avg_return_pct,
                'Win Rate (%)': perf.win_rate_pct,
                'Total Return (%)': perf.total_return_pct,
                'Best Trade (%)': perf.best_trade_pct,
                'Worst Trade (%)': perf.worst_trade_pct
            })
        
        # Get trade records
        trades = db.query(TradeRecord).filter(
            TradeRecord.backtest_run_id == backtest_id
        ).all()
        
        trade_data = []
        for trade in trades:
            trade_data.append({
                'Ticker': trade.ticker,
                'Buy Date': trade.buy_date.strftime('%Y-%m-%d'),
                'Buy Price': trade.buy_price,
                'Sell Date': trade.sell_date.strftime('%Y-%m-%d') if trade.sell_date else 'Open',
                'Sell Price': trade.sell_price if trade.sell_price else 'N/A',
                'Return (%)': trade.return_pct,
                'Days Held': trade.days_held,
                'Exit Reason': trade.exit_reason
            })
        
        return pd.DataFrame(ticker_data), pd.DataFrame(trade_data)
    
    finally:
        db.close()

def get_ticker_statistics(ticker, days=30):
    """
    Get performance statistics for a specific ticker over recent backtests
    
    Args:
        ticker (str): Stock ticker symbol
        days (int): Number of days to look back
    
    Returns:
        dict: Ticker statistics
    """
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - pd.Timedelta(days=days)
        
        # Get recent performance records for this ticker
        performances = db.query(TickerPerformance).join(BacktestRun).filter(
            TickerPerformance.ticker == ticker,
            BacktestRun.run_date >= cutoff_date
        ).all()
        
        if not performances:
            return {}
        
        returns = [p.avg_return_pct for p in performances]
        win_rates = [p.win_rate_pct for p in performances]
        
        return {
            'ticker': ticker,
            'backtest_count': len(performances),
            'avg_return': round(sum(returns) / len(returns), 2),
            'avg_win_rate': round(sum(win_rates) / len(win_rates), 1),
            'best_performance': round(max(returns), 2),
            'worst_performance': round(min(returns), 2),
            'consistency_score': round(100 - (pd.Series(returns).std() * 10), 1)  # Lower std = higher consistency
        }
    
    finally:
        db.close()