import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from datetime import datetime
import streamlit as st

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_sms_notification(to_phone_number, message):
    """Send SMS notification using Twilio"""
    try:
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            return False, "Twilio credentials not configured"
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        return True, f"SMS sent successfully with SID: {message.sid}"
    
    except Exception as e:
        return False, f"Failed to send SMS: {str(e)}"

def send_email_notification(to_email, subject, message, smtp_server="smtp.gmail.com", smtp_port=587, from_email=None, from_password=None):
    """Send email notification"""
    try:
        if not from_email or not from_password:
            return False, "Email credentials not provided"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'plain'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        return True, "Email sent successfully"
    
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def format_trading_signal(ticker, signal_type, price, rsi, red_days, strategy_params):
    """Format trading signal message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"""
🚨 TRADING SIGNAL ALERT 🚨

Ticker: {ticker}
Signal: {signal_type.upper()}
Price: ${price:.2f}
RSI: {rsi:.1f}
Consecutive Red Days: {red_days}

Strategy Parameters:
- RSI Threshold: {strategy_params['rsi_threshold']}
- Red Days Required: {strategy_params['red_days']}
- Exit Percentage: {strategy_params['exit_percentage']*100:.1f}%

Timestamp: {timestamp}

⚠️ This is an automated signal. Please conduct your own analysis before trading.
    """.strip()
    
    return message

def check_live_signals(tickers, strategy_params, notification_settings):
    """Check for live trading signals and send notifications"""
    import yfinance as yf
    from simple_strategy import calculate_simple_rsi
    import pandas as pd
    from datetime import datetime, timedelta
    
    signals_found = []
    
    for ticker in tickers:
        try:
            # Get recent data (last 30 days for RSI calculation)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if data is None or data.shape[0] < 15:
                continue
            
            # Fix multi-level columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            
            # Get latest data
            closes = data['Close'].values
            latest_price = closes[-1]
            
            # Calculate RSI
            rsi_values = calculate_simple_rsi(closes)
            latest_rsi = rsi_values[-1]
            
            if pd.isna(latest_rsi):
                continue
            
            # Calculate consecutive red days
            consecutive_red = 0
            for i in range(len(closes)-1, 0, -1):
                if closes[i] < closes[i-1]:
                    consecutive_red += 1
                else:
                    break
            
            # Check for buy signal
            if (consecutive_red >= strategy_params['red_days'] and 
                latest_rsi < strategy_params['rsi_threshold']):
                
                signal = {
                    'ticker': ticker,
                    'signal_type': 'BUY',
                    'price': latest_price,
                    'rsi': latest_rsi,
                    'red_days': consecutive_red,
                    'timestamp': datetime.now()
                }
                
                signals_found.append(signal)
                
                # Send notifications
                message = format_trading_signal(
                    ticker, 'BUY', latest_price, latest_rsi, 
                    consecutive_red, strategy_params
                )
                
                # Send SMS if configured
                if notification_settings.get('sms_enabled') and notification_settings.get('phone_number'):
                    send_sms_notification(notification_settings['phone_number'], message)
                
                # Send Email if configured
                if (notification_settings.get('email_enabled') and 
                    notification_settings.get('email_address') and
                    notification_settings.get('sender_email') and
                    notification_settings.get('sender_password')):
                    
                    send_email_notification(
                        notification_settings['email_address'],
                        f"Trading Signal: {ticker} BUY Alert",
                        message,
                        from_email=notification_settings['sender_email'],
                        from_password=notification_settings['sender_password']
                    )
        
        except Exception as e:
            print(f"Error checking signals for {ticker}: {e}")
            continue
    
    return signals_found

def render_notification_settings():
    """Render notification settings in Streamlit sidebar"""
    st.sidebar.header("📱 Notification Settings")
    
    # Initialize session state for notification settings
    if 'notification_settings' not in st.session_state:
        st.session_state.notification_settings = {
            'sms_enabled': False,
            'email_enabled': False,
            'phone_number': '',
            'email_address': '',
            'sender_email': '',
            'sender_password': '',
            'watchlist': [],
            'check_interval': 30
        }
    
    # SMS Settings
    sms_enabled = st.sidebar.checkbox(
        "📱 Enable SMS Notifications", 
        value=st.session_state.notification_settings['sms_enabled']
    )
    st.session_state.notification_settings['sms_enabled'] = sms_enabled
    
    if sms_enabled:
        phone_number = st.sidebar.text_input(
            "Phone Number (with country code)", 
            value=st.session_state.notification_settings['phone_number'],
            placeholder="+1234567890"
        )
        st.session_state.notification_settings['phone_number'] = phone_number
        
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            st.sidebar.warning("⚠️ Twilio credentials required for SMS notifications")
    
    # Email Settings
    email_enabled = st.sidebar.checkbox(
        "📧 Enable Email Notifications", 
        value=st.session_state.notification_settings['email_enabled']
    )
    st.session_state.notification_settings['email_enabled'] = email_enabled
    
    if email_enabled:
        email_address = st.sidebar.text_input(
            "Your Email Address", 
            value=st.session_state.notification_settings['email_address']
        )
        sender_email = st.sidebar.text_input(
            "Sender Gmail Address", 
            value=st.session_state.notification_settings['sender_email']
        )
        sender_password = st.sidebar.text_input(
            "Gmail App Password", 
            value=st.session_state.notification_settings['sender_password'],
            type="password",
            help="Use Gmail App Password, not regular password"
        )
        
        st.session_state.notification_settings['email_address'] = email_address
        st.session_state.notification_settings['sender_email'] = sender_email
        st.session_state.notification_settings['sender_password'] = sender_password
    
    # Watchlist for live monitoring
    watchlist_input = st.sidebar.text_area(
        "Live Monitoring Watchlist", 
        value=",".join(st.session_state.notification_settings['watchlist']),
        placeholder="AAPL,MSFT,GOOGL",
        help="Comma-separated list of tickers to monitor"
    )
    
    if watchlist_input:
        watchlist = [ticker.strip().upper() for ticker in watchlist_input.split(",") if ticker.strip()]
        st.session_state.notification_settings['watchlist'] = watchlist
    
    # Check interval
    check_interval = st.sidebar.selectbox(
        "Check Interval (minutes)", 
        [15, 30, 60, 120],
        index=[15, 30, 60, 120].index(st.session_state.notification_settings['check_interval'])
    )
    st.session_state.notification_settings['check_interval'] = check_interval
    
    return st.session_state.notification_settings