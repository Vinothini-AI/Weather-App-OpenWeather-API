import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_KEY")
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

def get_json(url, city):
    if not API_KEY:
        print("API key missing. Add OPENWEATHER_KEY=your_key_here to your .env file.")
        return None
    try:
        response = requests.get(url, params={"q": city, "appid": API_KEY, "units": "metric"}, timeout=10)
        if response.status_code == 404:
            print("City not found. Check the spelling.")
            return None
        if response.status_code == 401:
            print("API key rejected. Check your key; new keys may take time to activate.")
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        print(f"Network/API problem: {exc}")
        return None

def show_weather(city):
    current = get_json(CURRENT_URL, city)
    if not current:
        return
    main = current.get("main", {})
    weather = current.get("weather", [{}])[0]
    wind = current.get("wind", {})
    print(f"\nWeather for {current.get('name', city)}")
    print(f"Temperature : {main.get('temp', 'N/A')} °C")
    print(f"Feels like  : {main.get('feels_like', 'N/A')} °C")
    print(f"Humidity    : {main.get('humidity', 'N/A')}%")
    print(f"Conditions  : {weather.get('description', 'N/A').title()}")
    print(f"Wind speed  : {wind.get('speed', 'N/A')} m/s")
    forecast = get_json(FORECAST_URL, city)
    if not forecast:
        return
    print("\nForecast (one reading per day):")
    seen_dates = set()
    for item in forecast.get("list", []):
        date = item.get("dt_txt", "")[:10]
        if date and date not in seen_dates:
            seen_dates.add(date)
            temp = item.get("main", {}).get("temp", "N/A")
            desc = item.get("weather", [{}])[0].get("description", "N/A")
            print(f"  {date}: {temp} °C, {desc.title()}")
        if len(seen_dates) >= 5:
            break

def main():
    print("=== Live Weather App ===")
    while True:
        city = input("\nEnter a city (press Enter to quit): ").strip()
        if not city:
            print("Goodbye!")
            break
        show_weather(city)

if __name__ == "__main__":
    main()
