import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils import calculate_rsi

class MeanReversionStrategy:
    """
    Mean reversion strategy that buys after consecutive red days when RSI is below threshold
    and sells at specified gain/loss percentage.
    """
    
    def __init__(self, rsi_threshold=30, exit_percentage=0.05, red_days=2, rsi_period=14):
        """
        Initialize the strategy parameters.
        
        Args:
            rsi_threshold (int): RSI threshold below which to buy
            exit_percentage (float): Exit percentage (decimal, e.g., 0.05 for 5%)
            red_days (int): Number of consecutive red days before buy signal
            rsi_period (int): Period for RSI calculation
        """
        self.rsi_threshold = rsi_threshold
        self.exit_percentage = exit_percentage
        self.red_days = red_days
        self.rsi_period = rsi_period
    
    def identify_red_days(self, data):
        """
        Identify consecutive red days in the data.
        
        Args:
            data (pd.DataFrame): OHLCV data
            
        Returns:
            pd.Series: Number of consecutive red days for each date
        """
        # Calculate consecutive red days manually to avoid pandas boolean issues
        consecutive_red = []
        close_prices = data['Close'].values
        
        consecutive_red.append(0)  # First day has 0 consecutive red days
        
        for i in range(1, len(close_prices)):
            if close_prices[i] < close_prices[i-1]:  # Red day
                consecutive_red.append(consecutive_red[i-1] + 1)
            else:
                consecutive_red.append(0)
        
        return pd.Series(consecutive_red, index=data.index)
    
    def generate_signals(self, data):
        """
        Generate buy/sell signals based on the strategy rules.
        
        Args:
            data (pd.DataFrame): OHLCV data
            
        Returns:
            pd.DataFrame: Data with additional signal columns
        """
        # Calculate RSI
        rsi = calculate_rsi(data['Close'], period=self.rsi_period)
        
        # Identify consecutive red days
        consecutive_red = self.identify_red_days(data)
        
        # Generate buy signals using numpy arrays to avoid pandas boolean issues
        buy_signal = []
        rsi_values = rsi.values
        consecutive_red_values = consecutive_red.values
        
        for i in range(len(data)):
            signal = False
            if (not np.isnan(consecutive_red_values[i]) and consecutive_red_values[i] >= self.red_days and 
                not np.isnan(rsi_values[i]) and rsi_values[i] < self.rsi_threshold):
                signal = True
            buy_signal.append(signal)
        
        buy_signal = pd.Series(buy_signal, index=data.index)
        
        # Add signals to data
        signals_df = data.copy()
        signals_df['RSI'] = rsi
        signals_df['Consecutive_Red'] = consecutive_red
        signals_df['Buy_Signal'] = buy_signal
        
        return signals_df
    
    def backtest(self, data, ticker):
        """
        Perform backtesting of the strategy.
        
        Args:
            data (pd.DataFrame): OHLCV data
            ticker (str): Stock ticker symbol
            
        Returns:
            tuple: (trades_list, signals_dataframe)
        """
        # Generate signals
        signals = self.generate_signals(data)
        
        trades = []
        position = None  # Current position: None, or dict with buy info
        
        for i, (date, row) in enumerate(signals.iterrows()):
            # Skip if we don't have enough data for RSI
            if pd.isna(row['RSI']):
                continue
            
            # Check for buy signal
            if position is None and row['Buy_Signal']:
                position = {
                    'buy_date': date,
                    'buy_price': row['Close'],
                    'ticker': ticker
                }
            
            # Check for sell signal (if we have a position)
            elif position is not None:
                current_price = row['Close']
                buy_price = position['buy_price']
                
                # Calculate return percentage
                return_pct = (current_price - buy_price) / buy_price
                
                # Check if we should sell (hit target or stop loss)
                should_sell = abs(return_pct) >= self.exit_percentage
                
                # Also sell if it's the last day of data
                is_last_day = i == len(signals) - 1
                
                if should_sell or is_last_day:
                    # Calculate trade metrics
                    days_held = (date - position['buy_date']).days
                    
                    trade = {
                        'ticker': ticker,
                        'buy_date': position['buy_date'],
                        'buy_price': position['buy_price'],
                        'sell_date': date,
                        'sell_price': current_price,
                        'return_pct': return_pct * 100,  # Convert to percentage
                        'days_held': days_held,
                        'exit_reason': 'target_hit' if should_sell else 'end_of_data'
                    }
                    
                    trades.append(trade)
                    position = None  # Clear position
        
        # Handle open position at the end
        if position is not None:
            last_date = signals.index[-1]
            last_price = signals['Close'].iloc[-1]
            return_pct = (last_price - position['buy_price']) / position['buy_price']
            days_held = (last_date - position['buy_date']).days
            
            trade = {
                'ticker': ticker,
                'buy_date': position['buy_date'],
                'buy_price': position['buy_price'],
                'sell_date': last_date,
                'sell_price': last_price,
                'return_pct': return_pct * 100,
                'days_held': days_held,
                'exit_reason': 'end_of_data'
            }
            
            trades.append(trade)
        
        return trades, signals
    
    def calculate_performance_metrics(self, trades):
        """
        Calculate performance metrics from trades.
        
        Args:
            trades (list): List of trade dictionaries
            
        Returns:
            dict: Performance metrics
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'total_return': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'avg_days_held': 0
            }
        
        returns = [trade['return_pct'] for trade in trades]
        days_held = [trade['days_held'] for trade in trades if trade['days_held'] is not None]
        
        winning_trades = [r for r in returns if r > 0]
        
        metrics = {
            'total_trades': len(trades),
            'win_rate': len(winning_trades) / len(trades) * 100,
            'avg_return': np.mean(returns),
            'total_return': np.sum(returns),
            'best_trade': max(returns) if returns else 0,
            'worst_trade': min(returns) if returns else 0,
            'avg_days_held': np.mean(days_held) if days_held else 0,
            'median_return': np.median(returns) if returns else 0,
            'std_return': np.std(returns) if returns else 0
        }
        
        return metrics
