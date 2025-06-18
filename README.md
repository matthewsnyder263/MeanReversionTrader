*Originally prototyped in Replit for rapid iteration. Currently being cleaned, extended, and prepared for deployment using Docker + conventional architecture.*

# Mean Reversion Trading Strategy Backtester

A Streamlit application for backtesting mean reversion trading strategies with real-time signal monitoring and notification capabilities.

## Overview

This application implements a mean reversion strategy that:
- Buys stocks after consecutive red days when RSI falls below a threshold
- Sells at specified gain/loss percentage targets
- Provides backtesting capabilities across multiple tickers
- Monitors live signals with SMS/email notifications

## Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install streamlit pandas numpy yfinance plotly sqlalchemy psycopg2-binary twilio python-dotenv
   ```

3. Configure environment variables:
   Create a `.env` file with:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/trading_db
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   ```

4. Run the application:
   ```bash
   streamlit run app.py --server.port 5000
   ```

## Usage

### Backtesting
1. Set strategy parameters (RSI threshold, exit percentage, red days requirement)
2. Select date range and enter ticker symbols
3. Run backtest to view performance metrics and charts

### Live Signal Monitoring
1. Configure notification settings in sidebar
2. Add tickers to watchlist
3. Enable auto-refresh or manually check for signals

## Strategy Logic

**Buy Conditions:**
- Stock has N consecutive red days (configurable)
- RSI below threshold (configurable)

**Sell Conditions:**
- Price moves +/- exit percentage from buy price

## File Structure

```
├── app.py                   # Main Streamlit application
├── database.py             # Database models and operations
├── strategy.py             # Core strategy implementation
├── simple_strategy.py      # Simplified strategy variant
├── notifications.py        # SMS/Email notification system
├── utils.py               # Utility functions
├── strategy_playground.py  # Advanced strategy analysis
└── test_data.py           # Data validation utilities
```

## Scripts

- `streamlit run app.py --server.port 5000` - Start the application
- Database tables are created automatically on first run

## Technology Stack

- **Backend:** Python, Streamlit, SQLAlchemy, PostgreSQL
- **Data:** Yahoo Finance API (yfinance), Pandas, NumPy
- **Visualization:** Plotly
- **Notifications:** Twilio (SMS), SMTP (Email)

## Configuration

The application supports configuration through:
- Environment variables (database, API keys)
- UI parameters (strategy settings, watchlists)
- Database storage (backtest history, performance metrics)

## License

MIT License - see LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Not intended as investment advice. Past performance does not guarantee future results.
