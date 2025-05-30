import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

def calculate_rsi(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI) for a given price series.
    
    Args:
        prices (pd.Series): Series of closing prices
        period (int): Period for RSI calculation (default: 14)
    
    Returns:
        pd.Series: RSI values
    """
    # Calculate price changes
    delta = prices.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses using exponential moving average
    avg_gains = gains.ewm(span=period, adjust=False).mean()
    avg_losses = losses.ewm(span=period, adjust=False).mean()
    
    # Calculate relative strength
    rs = avg_gains / avg_losses
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def validate_ticker(ticker):
    """
    Validate if a ticker symbol exists and has data.
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        bool: True if ticker is valid, False otherwise
    """
    try:
        # Try to download a small amount of recent data
        data = yf.download(ticker, period="5d", progress=False)
        
        # Check if data exists and has content
        if data is None:
            return False
        
        # Handle both single and multi-level column DataFrames
        if hasattr(data, 'shape'):
            return data.shape[0] > 0
        else:
            return len(data) > 0
    
    except Exception:
        return False

def format_percentage(value, decimals=2):
    """
    Format a decimal value as a percentage string.
    
    Args:
        value (float): Decimal value (e.g., 0.05 for 5%)
        decimals (int): Number of decimal places
    
    Returns:
        str: Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"

def calculate_max_drawdown(returns):
    """
    Calculate the maximum drawdown from a series of returns.
    
    Args:
        returns (list or pd.Series): Series of returns
    
    Returns:
        float: Maximum drawdown as a percentage
    """
    if not returns:
        return 0
    
    # Convert to cumulative returns
    cum_returns = np.cumprod(1 + np.array(returns) / 100)
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(cum_returns)
    
    # Calculate drawdown
    drawdown = (cum_returns - running_max) / running_max
    
    # Return maximum drawdown as percentage
    return abs(np.min(drawdown)) * 100

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    Calculate the Sharpe ratio for a series of returns.
    
    Args:
        returns (list or pd.Series): Series of returns (as percentages)
        risk_free_rate (float): Annual risk-free rate (default: 2%)
    
    Returns:
        float: Sharpe ratio
    """
    if not returns or len(returns) < 2:
        return 0
    
    # Convert percentage returns to decimal
    decimal_returns = np.array(returns) / 100
    
    # Calculate excess returns (assuming returns are already annualized)
    excess_returns = decimal_returns - risk_free_rate / 252  # Daily risk-free rate
    
    # Calculate Sharpe ratio
    if np.std(excess_returns) == 0:
        return 0
    
    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    return sharpe

def get_stock_info(ticker):
    """
    Get basic information about a stock.
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        dict: Stock information or empty dict if error
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'beta': info.get('beta', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0)
        }
    
    except Exception:
        return {}

def calculate_volatility(prices, period=252):
    """
    Calculate the annualized volatility of a price series.
    
    Args:
        prices (pd.Series): Series of prices
        period (int): Number of periods for annualization (default: 252 trading days)
    
    Returns:
        float: Annualized volatility
    """
    if len(prices) < 2:
        return 0
    
    # Calculate daily returns
    returns = prices.pct_change().dropna()
    
    # Calculate annualized volatility
    volatility = returns.std() * np.sqrt(period)
    
    return volatility * 100  # Return as percentage

def format_currency(value, currency='USD'):
    """
    Format a numeric value as currency.
    
    Args:
        value (float): Numeric value
        currency (str): Currency code (default: 'USD')
    
    Returns:
        str: Formatted currency string
    """
    if currency == 'USD':
        return f"${value:,.2f}"
    else:
        return f"{value:,.2f} {currency}"

def calculate_trade_statistics(trades):
    """
    Calculate detailed statistics from a list of trades.
    
    Args:
        trades (list): List of trade dictionaries
    
    Returns:
        dict: Detailed trade statistics
    """
    if not trades:
        return {}
    
    returns = [trade['return_pct'] for trade in trades]
    days_held = [trade['days_held'] for trade in trades if trade['days_held'] is not None]
    
    winning_trades = [r for r in returns if r > 0]
    losing_trades = [r for r in returns if r < 0]
    
    stats = {
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': len(winning_trades) / len(trades) * 100 if trades else 0,
        'avg_win': np.mean(winning_trades) if winning_trades else 0,
        'avg_loss': np.mean(losing_trades) if losing_trades else 0,
        'largest_win': max(winning_trades) if winning_trades else 0,
        'largest_loss': min(losing_trades) if losing_trades else 0,
        'avg_days_held': np.mean(days_held) if days_held else 0,
        'profit_factor': abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else float('inf') if winning_trades else 0,
        'total_return': sum(returns),
        'avg_return': np.mean(returns),
        'median_return': np.median(returns),
        'return_std': np.std(returns),
        'max_drawdown': calculate_max_drawdown(returns),
        'sharpe_ratio': calculate_sharpe_ratio(returns)
    }
    
    return stats
