# Setup Guide for GitHub

## Quick Start

1. **Clone or download the repository**
2. **Install Python 3.8+** if not already installed
3. **Install dependencies**:
   ```bash
   pip install streamlit pandas numpy yfinance plotly sqlalchemy psycopg2-binary twilio trafilatura openai python-dotenv
   ```
4. **Set up environment variables** (copy `.env.example` to `.env` and fill in your values)
5. **Run the application**:
   ```bash
   streamlit run app.py --server.port 5000
   ```

## Environment Setup

### Required
- `DATABASE_URL`: PostgreSQL connection string
  - Example: `postgresql://user:password@localhost:5432/trading_db`
  - For local setup: Install PostgreSQL and create a database

### Optional (for notifications)
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token  
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number

### Getting Twilio Credentials
1. Sign up at [twilio.com](https://www.twilio.com)
2. Get a phone number in the console
3. Find your Account SID and Auth Token in the dashboard

## Database Setup

The application will automatically create tables on first run. No manual SQL setup required.

## File Structure for GitHub

```
your-repo/
├── app.py                    # Main application
├── database.py              # Database models
├── strategy.py              # Trading strategy
├── simple_strategy.py       # Simplified strategy
├── notifications.py         # Notification system
├── utils.py                 # Utility functions
├── strategy_playground.py   # Strategy analysis
├── test_data.py            # Data testing
├── README.md               # Documentation
├── LICENSE                 # MIT License
├── .gitignore             # Git ignore rules
├── .env.example           # Environment template
├── dependencies.md        # Package list
└── SETUP.md              # This file
```

## Running on Different Platforms

### Local Development
```bash
streamlit run app.py
```

### Heroku
1. Add `Procfile`: `web: streamlit run app.py --server.port=$PORT`
2. Add PostgreSQL addon
3. Set environment variables in Heroku dashboard

### Docker
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["streamlit", "run", "app.py", "--server.port=5000"]
```

## Troubleshooting

### Common Issues
- **Database connection**: Ensure PostgreSQL is running and DATABASE_URL is correct
- **Package conflicts**: Use virtual environment: `python -m venv venv && source venv/bin/activate`
- **Port conflicts**: Change port in streamlit command: `--server.port=8501`