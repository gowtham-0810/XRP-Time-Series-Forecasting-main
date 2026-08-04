import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime, timedelta

# Coingecko API URL for price/volume data
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/ripple/market_chart/range"
# Model Prediction API URL
MODEL_URL = "https://fastapi-25548684-at3-latest.onrender.com/predict/ripple"

def fetch_ripple_data(date, days_before = 29):
    # Define the vs_currency
    vs_currency="usd"
    id = "ripple"
    # Convert input date
    target_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = target_date - timedelta(days = days_before) 
    
    # Convert to UNIX timestamps (seconds)
    start_ts = int(start_date.timestamp())
    end_ts = int((target_date + timedelta(days=1)).timestamp())

    # Make the API request
    headers = {"x-cg-demo-api-key": "CG-vwVud1BDECZZ8XoTFsN4RGhJ"}
    params = {
        "vs_currency": vs_currency,
        "from": start_ts,
        "to": end_ts
    }
    response = requests.get(COINGECKO_API_URL, headers=headers, params=params)

    # Check for error response
    if response.status_code != 200:
        raise Exception(f"Error fetching data from CoinGecko: {response.status_code}")
    
    # Fetch and process data
    data = response.json()

    # Convert lists to DataFrames
    prices = pd.DataFrame(data.get("prices", []), columns=["timestamp", "price"])
    volumes = pd.DataFrame(data.get("total_volumes", []), columns=["timestamp", "volume"])
    market_caps = pd.DataFrame(data.get("market_caps", []), columns=["timestamp", "marketCap"])

     # Merge into one DataFrame
    df = prices.merge(volumes, on="timestamp").merge(market_caps, on="timestamp")

    # Convert timestamp to datetime and set timezone to Australia/Sydney
    df["timestamp"] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df['timestamp'] = df['timestamp'].dt.tz_convert('Australia/Sydney')
    
    # Resample to daily OHLCVM
    df_daily = df.set_index("timestamp").resample("1D").agg({
        "price": ["first", "max", "min", "last"],
        "volume": "sum",
        "marketCap": "mean"
    })

    # Flatten MultiIndex columns
    df_daily.columns = ["open", "high", "low", "close", "volume", "marketCap"]
    df_daily = df_daily.reset_index()
        
    return df_daily

# Function to calculate Relative Strength Index (RSI)
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    # Calculate price changes
    delta = prices.diff()
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    # Calculate RSI
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to calculate Moving Average Convergence Divergence (MACD)
def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    # Calculate EMAs - Exponential Moving Averages
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    # Calculate MACD line and Signal line
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    # Plot MACD Histogram
    histogram = macd - signal_line
    return macd, signal_line, histogram

# Function to fetch model prediction
def fetch_model_prediction(date):
    """Fetch model prediction for Ripple high price on given date"""
    try:
        params = {"date": date}
        response = requests.get(MODEL_URL, params=params)
        if response.status_code != 200:
            return None
        return response.json()["prediction"]
    except Exception as e:
        st.error(f"Exception during model prediction fetch: {e}")
        return None

# Main rendering function
def render():
    st.title("Ripple (XRP) Price Analysis and Prediction")
    # Date picker
    max_date = datetime.now()
    min_date = max_date - timedelta(days = 335)
    selected_date = st.date_input("Select a date for analysis (Optional - By Default it shows the current)", max_value=max_date, min_value=min_date)

    # Check if date is within allowed range
    if not (min_date.date() <= selected_date <= max_date.date()):
        st.error(f"Please select a date within the allowed range: {min_date.date()} to {max_date.date()}.")
        return  # Stop rendering if out of range

    # Fetch data
    with st.spinner("Fetching Ripple data..."):
        df = fetch_ripple_data(selected_date.strftime("%Y-%m-%d"), days_before = 29)

    if df is not None and not df.empty:
                
        st.markdown("---")

        # Display header and metrics
        st.markdown(f"### Technical Analysis for Ripple (XRP) up to {selected_date.strftime('%Y-%m-%d')}")

        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Time Range", f"{len(df['timestamp'])} days")
        with col2:
            st.metric("Latest Price (USD)", f"${df['close'].iloc[-1]:,.2f}")
        with col3:
            st.metric("Period High (USD)", f"${df['high'].max():,.2f}")
        with col4:
            st.metric("Period Low (USD)", f"${df['low'].min():,.2f}")

        st.markdown("---")

        # Technical Indicators
        st.subheader("📊 Technical Indicators")

        # Calculate indicators
        df['RSI'] = calculate_rsi(df['close'])
        df['MACD'], df['Signal'], df['MACD_Histogram'] = calculate_macd(df['close'])

        # Indicator selection
        indicator = st.selectbox(
            "Select Technical Indicator",
            ["RSI (Relative Strength Index)", "MACD", "Candlestick Chart"]
        )

        if indicator == "RSI (Relative Strength Index)":
            st.markdown("**RSI Analysis** - Measures momentum on a scale of 0-100")
            st.markdown("- **Above 70:** Overbought (potential sell signal)")
            st.markdown("- **Below 30:** Oversold (potential buy signal)")

            fig_rsi = go.Figure()
            # Add RSI line
            fig_rsi.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI'], mode='lines', name='RSI'))

             # Add overbought/oversold lines
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")

            # Update layout
            fig_rsi.update_layout(
                title="RSI Indicator",
                xaxis_title="Time",
                yaxis_title="RSI",
                template='plotly_dark',
                height=400
            )
            st.plotly_chart(fig_rsi, use_container_width=True)

            # Current RSI status
            current_rsi = df['RSI'].iloc[-1]
            if current_rsi > 70:
                st.warning(f"⚠️ Current RSI: {current_rsi:.2f} - Overbought territory")
            elif current_rsi < 30:
                st.success(f"✅ Current RSI: {current_rsi:.2f} - Oversold territory")
            else:
                st.info(f"ℹ️ Current RSI: {current_rsi:.2f} - Neutral")

        elif indicator == "MACD":
            st.markdown("**MACD Analysis** - Shows relationship between two moving averages")
            st.markdown("- **MACD Line crosses above Signal Line:** Bullish signal")
            st.markdown("- **MACD Line crosses below Signal Line:** Bearish signal")

            fig_macd = go.Figure()
            # Add MACD and Signal lines
            fig_macd.add_trace(go.Scatter(x=df['timestamp'], y=df['MACD'], mode='lines', name='MACD'))
            fig_macd.add_trace(go.Scatter(x=df['timestamp'], y=df['Signal'], mode='lines', name='Signal Line'))

            # Add MACD Histogram
            fig_macd.add_trace(go.Bar(x=df['timestamp'], y=df['MACD_Histogram'], name='MACD Histogram'))

            # Update layout
            fig_macd.update_layout(
                title="MACD Indicator",
                xaxis_title="Time",
                yaxis_title="MACD",
                template='plotly_dark',
                height=400
            )
            st.plotly_chart(fig_macd, use_container_width=True)

            # Current MACD status
            if df['MACD'].iloc[-1] > df['Signal'].iloc[-1]:
                st.success("✅ Bullish signal - MACD Line is above Signal Line")
            else:
                st.warning("⚠️ Bearish signal - MACD Line is below Signal Line")
        
        else:
            # Plot Candlestick Chart
            st.markdown("**Candlestick Chart** - Visual representation of price movements")
            fig_candle = go.Figure(data=[go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])

            # Update layout
            fig_candle.update_layout(
                title="Candlestick Chart",
                xaxis_title="Time",
                yaxis_title="Price (USD)",
                template='plotly_dark',
                height=500
            )
            st.plotly_chart(fig_candle, use_container_width=True)
        
        st.markdown("---")

        # Volume Analysis
        st.subheader("📈 Volume Analysis")

        # Color volume bars based on price movement
        colors = ['green' if df['close'].iloc[i] >= df['open'].iloc[i] else 'red' for i in range(len(df))]

        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=df['timestamp'], 
            y=df['volume'], 
            name='Volume (USD)',
            marker_color = colors
        ))
        fig_volume.update_layout(
            title="Trading Volume Over Time",
            xaxis_title="Date",
            yaxis_title="Volume (USD)",
            hovermode="x unified",
            template='plotly_dark',
            height=400
        )
        st.plotly_chart(fig_volume, use_container_width=True)

        # Volume statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Volume (USD)", f"{df['volume'].mean()/1e9:,.2f}B")
        with col2:
            st.metric("Max Volume (USD)", f"{df['volume'].max()/1e9:,.2f}B")
        with col3:
            st.metric("Min Volume (USD)", f"{df['volume'].min()/1e9:,.2f}B")
        with col4:
            st.metric("Total Volume (USD)", f"{df['volume'].sum()/1e9:,.2f}B")
        
        st.markdown("---")

        # Prediction
        st.subheader("🤖 Price(High) Prediction")

        # Get the prediction for high on day + 1
        prediction_high = fetch_model_prediction(selected_date.strftime("%Y-%m-%d"))
        if prediction_high:
            # Display predictions
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Predicted Date", prediction_high["predicted_date"])
            with col2:
                prev_day_high = df['high'].tail(1).iloc[0]
                pred_high = prediction_high['prediction']
                price_change = pred_high - prev_day_high
                st.metric("Predicted High (USD)", f"${prediction_high['prediction']:,.3f}", delta = f"{price_change:,.3f} (from previous day)")
        else:
            st.warning("Prediction unavailable")
        
        st.markdown("---")

        st.warning(
            "⚠️ Disclaimer: The information and predictions shown here are for educational purposes only. "
            "They **should not** be used for actual financial or investment decisions."
        )