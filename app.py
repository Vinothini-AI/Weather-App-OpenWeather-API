import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

st.set_page_config(page_title="Live Weather App", page_icon="🌦️", layout="centered")

def get_api_key():
    try:
        key = st.secrets.get("OPENWEATHER_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("OPENWEATHER_KEY", "")

def fetch_json(url, city, api_key):
    try:
        response = requests.get(url, params={"q": city, "appid": api_key, "units": "metric"}, timeout=10)
        if response.status_code == 404:
            return None, "City not found. Check the spelling and try again."
        if response.status_code == 401:
            return None, "The API key was rejected. Check your key; a new key may take time to activate."
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.Timeout:
        return None, "The weather service took too long to respond. Please try again."
    except requests.exceptions.RequestException:
        return None, "Could not connect to the weather service. Check your connection and try again."

def daily_forecast(data):
    selected = {}
    for item in data.get("list", []):
        stamp = datetime.fromtimestamp(item["dt"])
        date_key = stamp.strftime("%Y-%m-%d")
        if date_key not in selected or abs(stamp.hour - 12) < abs(datetime.fromtimestamp(selected[date_key]["dt"]).hour - 12):
            selected[date_key] = item
    rows = []
    for date_key, item in list(selected.items())[:5]:
        rows.append({
            "Date": datetime.strptime(date_key, "%Y-%m-%d").strftime("%a, %d %b"),
            "Temperature (°C)": round(item["main"]["temp"]),
            "Feels Like (°C)": round(item["main"]["feels_like"]),
            "Humidity (%)": item["main"]["humidity"],
            "Forecast": item["weather"][0]["description"].title(),
            "Wind (m/s)": round(item.get("wind", {}).get("speed", 0), 1),
        })
    return pd.DataFrame(rows)

st.title("🌦️ Live Weather App")
st.caption("Current weather and a 5-day forecast powered by OpenWeather.")
api_key = get_api_key()
if not api_key:
    st.warning("API key not found. For local use, add OPENWEATHER_KEY=your_key_here to a .env file. For Streamlit Cloud, add it under App Settings → Secrets.")
    st.code('OPENWEATHER_KEY = "your_openweather_api_key"', language="toml")
    st.stop()

with st.form("weather_form"):
    city = st.text_input("Enter a city", placeholder="e.g., Chennai, London, Tokyo")
    submitted = st.form_submit_button("Get Weather", type="primary")

if submitted:
    city = city.strip()
    if not city:
        st.error("Please enter a city name.")
        st.stop()
    with st.spinner(f"Fetching weather for {city}..."):
        current, error = fetch_json(CURRENT_URL, city, api_key)
    if error:
        st.error(error)
        st.stop()

    st.subheader(f"Current weather in {current.get('name', city)}, {current.get('sys', {}).get('country', '')}")
    weather = current.get("weather", [{}])[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{current.get('main', {}).get('temp', '—')} °C")
    col2.metric("Humidity", f"{current.get('main', {}).get('humidity', '—')}%")
    col3.metric("Wind speed", f"{current.get('wind', {}).get('speed', '—')} m/s")
    st.write(f"**Conditions:** {weather.get('description', 'Not available').title()}")
    st.write(f"**Feels like:** {current.get('main', {}).get('feels_like', '—')} °C")

    with st.spinner("Loading forecast..."):
        forecast, forecast_error = fetch_json(FORECAST_URL, city, api_key)
    if forecast_error:
        st.warning(f"Current weather loaded, but the forecast could not be retrieved. {forecast_error}")
    else:
        st.subheader("5-Day Forecast")
        forecast_df = daily_forecast(forecast)
        st.dataframe(forecast_df, use_container_width=True, hide_index=True)
        st.download_button("Download forecast as CSV", data=forecast_df.to_csv(index=False).encode("utf-8"),
                           file_name=f"{current.get('name', 'weather').lower().replace(' ', '_')}_forecast.csv",
                           mime="text/csv")

st.divider()
st.caption("Data provided by OpenWeather. Temperatures are shown in Celsius.")
