# Mean Reversion Trading Strategy Backtester

A sophisticated Streamlit-based application for backtesting and monitoring mean reversion trading strategies with comprehensive performance analytics and real-time signal notifications.

## Features

### 🏠 Strategy Backtester
- **Interactive Parameter Tuning**: Adjust RSI threshold, exit percentages, and red day requirements
- **Multi-Ticker Analysis**: Test strategies across multiple stocks simultaneously
- **Visual Analytics**: Interactive charts with buy/sell signals and RSI indicators
- **Performance Metrics**: Win rates, average returns, trade statistics, and profitability analysis

### 🎮 Strategy Playground
- **Parameter Optimization**: Advanced analysis of strategy parameter combinations
- **Performance Heatmaps**: Visual representation of parameter effectiveness
- **Risk Analysis**: Comprehensive risk metrics and drawdown analysis
- **Market Condition Analysis**: Performance across different market environments

### 🚨 Live Signal Monitoring
- **Real-Time Alerts**: Monitor live market data for trading signals
- **Multi-Channel Notifications**: SMS and email alerts when signals are detected
- **Auto-Refresh**: Continuous monitoring with configurable intervals
- **Signal History**: Track and review past signal occurrences

## Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Market Data**: Yahoo Finance API (yfinance)
- **Notifications**: Twilio (SMS), SMTP (Email)

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Twilio account (for SMS notifications)
- Gmail account with app password (for email notifications)

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd mean-reversion-backtester
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Variables**
Create a `.env` file with the following variables:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/trading_db
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

4. **Database Setup**
The application will automatically create required tables on first run.

5. **Run the application**
```bash
streamlit run app.py --server.port 5000
```

## Usage

### Basic Backtesting

1. **Configure Strategy Parameters**
   - Set RSI threshold (typically 20-40)
   - Define exit percentage (1-10%)
   - Choose red days requirement (1-5 days)

2. **Select Time Period**
   - Choose start and end dates for backtesting
   - Recommended: At least 1 year of data

3. **Enter Stock Symbols**
   - Add comma-separated ticker symbols
   - Example: `AAPL,MSFT,GOOGL,TSLA,AMZN`

4. **Run Strategy**
   - Click "Run Strategy" to execute backtest
   - View results in interactive charts and performance tables

### Live Signal Monitoring

1. **Configure Notifications**
   - Enable SMS/Email notifications in sidebar
   - Add your contact information
   - Set up Twilio credentials (for SMS)

2. **Set Watchlist**
   - Add tickers to monitor for live signals
   - Configure check intervals

3. **Monitor Signals**
   - Use "Check for Signals Now" for manual checks
   - Enable auto-refresh for continuous monitoring

## Strategy Logic

The mean reversion strategy implements the following rules:

### Buy Signal Conditions
- Stock has consecutive red days (configurable, default: 2)
- RSI falls below threshold (configurable, default: 30)
- Both conditions must be met simultaneously

### Sell Signal Conditions
- Stock price moves +/- exit percentage from buy price
- Automatic exit at specified gain/loss level

### Risk Management
- Position sizing based on portfolio allocation
- Stop-loss via exit percentage parameter
- No overnight positions (day trading focus)

## File Structure

```
├── app.py                    # Main Streamlit application
├── database.py              # Database models and operations
├── strategy.py              # Core strategy implementation
├── simple_strategy.py       # Simplified strategy variant
├── notifications.py         # SMS/Email notification system
├── utils.py                 # Utility functions
├── strategy_playground.py   # Advanced strategy analysis
├── test_data.py            # Data validation utilities
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Database Schema

### BacktestRun
Stores backtest configurations and summary results

### TradeRecord  
Individual trade records with entry/exit details

### TickerPerformance
Performance metrics per ticker per backtest

## Configuration

### Streamlit Configuration
Create `.streamlit/config.toml`:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

## API Keys and External Services

### Yahoo Finance
- No API key required
- Free market data access
- Rate limits may apply for high-frequency requests

### Twilio (SMS Notifications)
- Account SID and Auth Token required
- Phone number verification needed
- Pay-per-message pricing

### Email Notifications
- Gmail account with 2FA enabled
- App-specific password required
- SMTP configuration included

## Performance Optimization

- **Data Caching**: Results cached in session state
- **Batch Processing**: Multiple tickers processed efficiently
- **Database Indexing**: Optimized queries for historical data
- **Chart Limiting**: Maximum 5 charts displayed simultaneously

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and research purposes only. It is not intended as investment advice. Always conduct your own research and consult with financial professionals before making investment decisions. Past performance does not guarantee future results.

## Support

For issues and feature requests, please create an issue in the GitHub repository.

## Roadmap

- [ ] Machine learning signal enhancement
- [ ] Multi-timeframe analysis
- [ ] Portfolio optimization features
- [ ] Paper trading simulation
- [ ] Advanced charting tools
- [ ] Mobile app development