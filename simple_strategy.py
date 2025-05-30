import pandas as pd
import numpy as np
from datetime import datetime

def calculate_simple_rsi(prices, period=14):
    """Simple RSI calculation without pandas boolean operations"""
    prices = np.array(prices)
    deltas = np.diff(prices)
    
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Initialize RSI array with correct length
    rsi_values = [np.nan] * len(prices)
    
    # Calculate RSI starting from period+1 index
    for i in range(period, len(prices)):
        # Get gains and losses for the period
        period_gains = gains[i-period:i]
        period_losses = losses[i-period:i]
        
        avg_gain = np.mean(period_gains) if len(period_gains) > 0 else 0
        avg_loss = np.mean(period_losses) if len(period_losses) > 0 else 0
        
        if avg_loss == 0:
            rsi_values[i] = 100
        else:
            rs = avg_gain / avg_loss
            rsi_values[i] = 100 - (100 / (1 + rs))
    
    return rsi_values

def simple_backtest(data, rsi_threshold=30, exit_percentage=0.05, red_days=2):
    """Simple backtesting function without complex pandas operations"""
    if len(data) < 20:  # Need minimum data
        return []
    
    # Convert to simple arrays
    dates = data.index.tolist()
    closes = data['Close'].values
    
    # Calculate RSI
    rsi_values = calculate_simple_rsi(closes)
    
    # Calculate consecutive red days
    consecutive_red = [0]  # First day is 0
    for i in range(1, len(closes)):
        if closes[i] < closes[i-1]:  # Red day
            consecutive_red.append(consecutive_red[i-1] + 1)
        else:
            consecutive_red.append(0)
    
    # Find trading signals
    trades = []
    position = None
    
    for i in range(len(dates)):
        current_date = dates[i]
        current_price = closes[i]
        current_rsi = rsi_values[i]
        current_red_days = consecutive_red[i]
        
        # Skip if we don't have RSI data yet
        if np.isnan(current_rsi):
            continue
        
        # Check for buy signal
        if position is None:
            if current_red_days >= red_days and current_rsi < rsi_threshold:
                position = {
                    'buy_date': current_date,
                    'buy_price': current_price,
                    'ticker': 'STOCK'
                }
        
        # Check for sell signal
        elif position is not None:
            return_pct = (current_price - position['buy_price']) / position['buy_price']
            
            # Sell if we hit target or it's the last day
            if abs(return_pct) >= exit_percentage or i == len(dates) - 1:
                days_held = (current_date - position['buy_date']).days
                
                trade = {
                    'ticker': position['ticker'],
                    'buy_date': position['buy_date'],
                    'buy_price': position['buy_price'],
                    'sell_date': current_date,
                    'sell_price': current_price,
                    'return_pct': return_pct * 100,
                    'days_held': days_held,
                    'exit_reason': 'target_hit' if abs(return_pct) >= exit_percentage else 'end_of_data'
                }
                
                trades.append(trade)
                position = None
    
    return trades

class SimpleStrategy:
    """Simplified strategy class that avoids pandas boolean issues"""
    
    def __init__(self, rsi_threshold=30, exit_percentage=0.05, red_days=2):
        self.rsi_threshold = rsi_threshold
        self.exit_percentage = exit_percentage
        self.red_days = red_days
    
    def backtest(self, data, ticker):
        """Run simple backtest"""
        try:
            trades = simple_backtest(
                data, 
                self.rsi_threshold, 
                self.exit_percentage, 
                self.red_days
            )
            
            # Update ticker in trades
            for trade in trades:
                trade['ticker'] = ticker
            
            # Create simple signals dataframe
            signals = data.copy()
            rsi_values = calculate_simple_rsi(data['Close'].values)
            signals['RSI'] = rsi_values
            
            return trades, signals
        
        except Exception as e:
            print(f"Error in backtest for {ticker}: {e}")
            return [], data.copy()