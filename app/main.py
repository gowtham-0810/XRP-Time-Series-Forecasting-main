import streamlit as st
import pandas as pd
import requests

import plotly.graph_objects as go
import plotly.express as px

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Import student modules
from students import ripple_25548684

# Page configuration
st.set_page_config(
    page_title="Crypto Investment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cryptocurrency options
CRYPTOS = {
    'Ripple': 'XRP',
}

def fetch_coingecko_data(coin_id, days=30):
    """Fetch market data from CoinGecko API"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"       
        headers = {"x-cg-demo-api-key": "CG-vwVud1BDECZZ8XoTFsN4RGhJ"}
        params = {'vs_currency': 'usd', 'days': days}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
            market_caps = pd.DataFrame(data['market_caps'], columns=['timestamp', 'market_cap'])
            
            prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')
            volumes['timestamp'] = pd.to_datetime(volumes['timestamp'], unit='ms')
            market_caps['timestamp'] = pd.to_datetime(market_caps['timestamp'], unit='ms')

            df = prices.merge(volumes, on='timestamp').merge(market_caps, on='timestamp')
            return df
    except Exception as e:
        st.error(f"Error fetching CoinGecko data: {e}")
        return None

def main():
    # Main Header
    st.markdown('<h1 class="main-header">📈 Cryptocurrency Investment Dashboard</h1>', unsafe_allow_html=True)
    # Subheader
    st.markdown("### Historical Analysis & ML-Powered Predictions")
    
    # Sidebar for navigation
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/bitcoin.png", width=80)
        # st.title("Navigation")

        # Select Cryptocurrency using a dropdown
        selected_crypto_token = st.selectbox(
            "Select Cryptocurrency",
            options=list(CRYPTOS.keys()),
            index=0
        )

        # Select Date Range
        allowed_days = [1, 7, 14, 30, 90, 180, 365]
        selected_days = st.sidebar.select_slider("Select Days of Data", options = allowed_days, value = 30)

        # Get the selected cryptocurrency symbol
        selected_crypto = CRYPTOS[selected_crypto_token]

        # Display selected cryptocurrency
        st.markdown("---")
        st.info(f"**Selected Crypto**: {selected_crypto_token} ({selected_crypto})\n\n **Days of Data**: {selected_days} days")

        # Data refresh
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
    
    # Main tabs
    tabs = st.tabs(["📊 Overview", "🪙 RIPPLE"])

    # Overview Tab
    with tabs[0]:
        st.header(f"{selected_crypto_token} Overview Dashboard")
        
        
        # Fetch data
        with st.spinner("Fetching data..."):
            coingecko_id = selected_crypto_token.lower()
            df = fetch_coingecko_data(coingecko_id, days = selected_days)
        
        if df is not None:           

            current_price = df['price'].iloc[-1]
            prev_price = df['price'].iloc[-2]
            price_change = (current_price - prev_price) / prev_price * 100
            print(f"Current Price: {current_price}, Previous Price: {prev_price}")

            st.markdown("---")

            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            # Current Price
            with col1:
                st.metric(
                    label = "Current Price (USD)",
                    value = f"${current_price:,.2f}",
                    delta = f"{price_change:.2f} %"
                )
            
            # 24h High
            with col2:
                st.metric(
                    label = "24h High (USD)",
                    value = f"${df['price'].tail(24).max():,.2f}"
                )

            # 24h Low
            with col3:
                st.metric(
                    label = "24h Low (USD)",
                    value = f"${df['price'].tail(24).min():,.2f}"
                )

            # Market Cap
            with col4:
                st.metric(
                    label = "Market Cap (USD)",
                    value = f"${df['market_cap'].iloc[-1]/1e9:,.2f}B"
                )

            st.markdown("---")
            
            # Price chart
            st.subheader(f"Price History ({selected_days} Days)")

            # Create price line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'], 
                y=df['price'], 
                mode='lines',
                name='Price (USD)',
                line=dict(color='royalblue', width=2)
            ))
            fig.update_layout(
                title=f"{selected_crypto_token} Price Over Last {selected_days} Days",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                hovermode="x unified",
                template='plotly_dark',
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # Volume chart
            st.subheader(f"Trading Volume History ({selected_days} Days)")
            fig_volume = go.Figure()
            fig_volume.add_trace(go.Bar(
                x=df['timestamp'], 
                y=df['volume'], 
                name='Volume (USD)',
                marker_color="#6D44CB"
            ))
            fig_volume.update_layout(
                title=f"{selected_crypto_token} Trading Volume Over Last {selected_days} Days",
                xaxis_title="Date",
                yaxis_title="Volume (USD)",
                hovermode="x unified",
                height=500
            )
            st.plotly_chart(fig_volume, use_container_width=True)

            st.markdown("---")

            # Display raw data - Statistics

            col1, col2 = st.columns([2, 3])

            with col1:
                st.subheader(f"{selected_days}-Day Statistical Summary")
                # Display statistics as dataframe
                stats = pd.DataFrame({
                    'Metric': ['Mean Price', 'Median Price', 'Std Deviation', 'Min Price', 'Max Price'],
                    'Value (USD)': [
                        f"${df['price'].mean():,.2f}",
                        f"${df['price'].median():,.2f}",
                        f"${df['price'].std():,.2f}",
                        f"${df['price'].min():,.2f}",
                        f"${df['price'].max():,.2f}"
                    ]
                })
                st.dataframe(stats, hide_index = True, use_container_width = True)

            with col2:
                st.subheader(f"Daily Aggregate for last 10 Days")

                # Convert timestamp to datetime
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

                # Resample to daily frequency
                df_daily = (
                    df.set_index("timestamp")
                    .resample("1D")
                    .agg({
                        "price": ["first", "max", "min", "last"],
                        "volume": "sum",
                        "market_cap": "mean"
                    })
                )

                # Convert to billions for readability
                df_daily["volume"] = (df_daily["volume"] / 1e9).round(2)
                df_daily["market_cap"] = (df_daily["market_cap"] / 1e9).round(2)

                # Flatten MultiIndex columns
                df_daily.columns = ["Open($)", "High($)", "Low($)", "Close($)", "Volume(B$)", "Market Cap(B$)"]

                # Round values for better readability
                df_daily['Open($)'] = df_daily['Open($)'].round(2)
                df_daily['High($)'] = df_daily['High($)'].round(2)
                df_daily['Low($)'] = df_daily['Low($)'].round(2)
                df_daily['Close($)'] = df_daily['Close($)'].round(2)

                # Display last 10 days - Daily aggregates as dataframe
                st.dataframe(df_daily.tail(10).reset_index(), hide_index = True, use_container_width=True)

    # Ripple Tab
    with tabs[1]:
        ripple_25548684.render()

        


if __name__ == "__main__":
    main()
