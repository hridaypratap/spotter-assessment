
import requests


def get_weather(latitude, longitude, forecast_hours=48):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": (
                "wind_speed_10m,"
                "precipitation,"
                "rain,"
                "snowfall"
            ),
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "forecast_days": 2,
            "timezone": "UTC",
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()

    return data.get("hourly", {})

