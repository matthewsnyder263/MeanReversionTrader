import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Test data fetching
def test_data_fetch():
    print("Testing Yahoo Finance data fetching...")
    
    # Test with a simple ticker
    ticker = "AAPL"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        print(f"Fetching {ticker} data from {start_date.date()} to {end_date.date()}")
        data = yf.download(ticker, start=start_date, end=end_date)
        
        print(f"Data shape: {data.shape}")
        print(f"Columns: {data.columns.tolist()}")
        print(f"Date range: {data.index.min()} to {data.index.max()}")
        print(f"Sample data:")
        print(data.head())
        print(f"Last few rows:")
        print(data.tail())
        
        # Check for missing data
        print(f"Missing values: {data.isnull().sum().sum()}")
        
        # Check price range
        if 'Close' in data.columns:
            print(f"Close price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
        
        return data
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    test_data_fetch()