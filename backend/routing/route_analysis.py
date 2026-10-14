
import math
from datetime import datetime, timezone

import requests

from routing.services import get_routes
from routing.geocoding import geocode_place
from routing.risk_engine import classify_weather


WEATHER_BATCH_SIZE = 10
METERS_PER_MILE = 1609.344
EARTH_RADIUS_MILES = 3958.7613

RISK_SCORE = {
    "Low": 0,
    "Moderate": 1,
    "High": 2,
    "Severe": 3,
    "No Travel": 4,
}


def haversine_miles(point_a, point_b):
    """Calculate distance between two [longitude, latitude] points."""
    lon1, lat1 = point_a
    lon2, lat2 = point_b

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    return 2 * EARTH_RADIUS_MILES * math.asin(
        math.sqrt(min(1.0, a))
    )


def interpolate_route_point(coordinates, target_mile, cumulative_miles):
    """Find a coordinate at a specified distance along the route."""
    if target_mile <= 0:
        return coordinates[0]

    if target_mile >= cumulative_miles[-1]:
        return coordinates[-1]

    low = 0
    high = len(cumulative_miles) - 1

    while low < high:
        mid = (low + high) // 2

        if cumulative_miles[mid] < target_mile:
            low = mid + 1
        else:
            high = mid

    index = low

    previous_distance = cumulative_miles[index - 1]
    next_distance = cumulative_miles[index]
    segment_length = next_distance - previous_distance

    if segment_length <= 0:
        return coordinates[index]

    fraction = (
        (target_mile - previous_distance) / segment_length
    )

    start_lon, start_lat = coordinates[index - 1]
    end_lon, end_lat = coordinates[index]

    longitude = start_lon + fraction * (end_lon - start_lon)
    latitude = start_lat + fraction * (end_lat - start_lat)

    return [longitude, latitude]


def get_weather_batch(locations):
    """Fetch hourly forecasts for locations in API-sized batches."""
    forecasts = []

    for start in range(0, len(locations), WEATHER_BATCH_SIZE):
        batch = locations[start:start + WEATHER_BATCH_SIZE]

        params = {
            "latitude": ",".join(str(lat) for lat, lon in batch),
            "longitude": ",".join(str(lon) for lat, lon in batch),
            "hourly": "wind_speed_10m,rain,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "forecast_days": 2,
            "timezone": "UTC",
        }

        try:
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params=params,
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise ValueError(
                f"Weather forecast request failed: {exc}"
            ) from exc

        if isinstance(data, dict):
            if data.get("error"):
                raise ValueError(
                    data.get("reason", "Weather API returned an error")
                )
            data = [data]

        if not isinstance(data, list) or len(data) != len(batch):
            raise ValueError(
                "Weather API returned an unexpected number of forecasts"
            )

        for item in data:
            hourly = item.get("hourly", {})

            times = hourly.get("time", [])
            wind = hourly.get("wind_speed_10m", [])
            rain = hourly.get("rain", [])
            snow = hourly.get("snowfall", [])

            if not times or not (
                len(times) == len(wind) == len(rain) == len(snow)
            ):
                raise ValueError(
                    "Weather API returned incomplete hourly forecast data"
                )

            forecasts.append({
                "time": times,
                "wind_speed_10m": wind,
                "rain": rain,
                "snowfall": snow,
            })

    return forecasts


def parse_forecast_time(value):
    """Parse an ISO timestamp and ensure it is timezone-aware."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def analyze_route(
    origin_name,
    destination_name,
    departure_time,
    load_lb,
    interval_miles=25,
):
    if interval_miles not in (10, 25, 50):
        raise ValueError("interval_miles must be 10, 25, or 50")

    try:
        load_lb = float(load_lb)
    except (TypeError, ValueError) as exc:
        raise ValueError("Load weight must be a valid number") from exc

    if not math.isfinite(load_lb) or load_lb < 0:
        raise ValueError("Load weight must be a non-negative number")

    origin = geocode_place(origin_name)
    destination = geocode_place(destination_name)
    routes = get_routes(origin, destination)

    if not routes:
        raise ValueError("No driving routes found between these locations")

    try:
        departure = datetime.fromisoformat(
            departure_time.replace("Z", "+00:00")
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Invalid departure time") from exc

    if departure.tzinfo is None:
        departure = departure.replace(tzinfo=timezone.utc)

    departure = departure.astimezone(timezone.utc)
    departure_timestamp = departure.timestamp()
    forecast_end = departure_timestamp + 48 * 60 * 60

    route_data = []
    all_locations = []

    for index, route in enumerate(routes, 1):
        coordinates = route["geometry"]["coordinates"]

        if not coordinates:
            continue

        distance_miles = route["distance"] / METERS_PER_MILE
        duration_seconds = route["duration"]

        if distance_miles <= 0 or duration_seconds < 0:
            continue

        cumulative_miles = [0.0]

        for point_index in range(1, len(coordinates)):
            segment_distance = haversine_miles(
                coordinates[point_index - 1],
                coordinates[point_index],
            )
            cumulative_miles.append(
                cumulative_miles[-1] + segment_distance
            )

        geometry_distance = cumulative_miles[-1]

        if geometry_distance <= 0:
            continue

        checkpoint_miles = list(
            range(0, int(distance_miles), interval_miles)
        )

        if not checkpoint_miles:
            checkpoint_miles = [0]

        if abs(checkpoint_miles[-1] - distance_miles) > 0.01:
            checkpoint_miles.append(distance_miles)

        checkpoint_data = []

        for mile in checkpoint_miles:
            fraction = min(mile / distance_miles, 1.0)

            coordinate = interpolate_route_point(
                coordinates,
                fraction * geometry_distance,
                cumulative_miles,
            )

            longitude, latitude = coordinate

            estimated_arrival = (
                departure_timestamp + duration_seconds * fraction
            )

            location_index = len(all_locations)
            all_locations.append((latitude, longitude))

            checkpoint_data.append({
                "mile": round(mile, 1),
                "latitude": latitude,
                "longitude": longitude,
                "estimated_arrival": estimated_arrival,
                "location_index": location_index,
            })

        route_data.append({
            "route_number": index,
            "distance_miles": round(distance_miles, 1),
            "duration_hours": round(duration_seconds / 3600, 2),
            "geometry": route["geometry"],
            "checkpoint_data": checkpoint_data,
        })

    if not route_data:
        raise ValueError("Routes contained no usable coordinates")

    forecasts = get_weather_batch(all_locations)
    results = []

    for route in route_data:
        checkpoints = []

        for point in route["checkpoint_data"]:
            forecast = forecasts[point["location_index"]]
            forecast_times = [
                parse_forecast_time(value)
                for value in forecast["time"]
            ]

            if not forecast_times:
                continue

            target_time = datetime.fromtimestamp(
                point["estimated_arrival"], timezone.utc
            ).replace(minute=0, second=0, microsecond=0)

            weather_index = min(
                range(len(forecast_times)),
                key=lambda j: abs(
                    (forecast_times[j] - target_time).total_seconds()
                ),
            )

            wind = forecast["wind_speed_10m"][weather_index]
            rain = forecast["rain"][weather_index]
            snow = forecast["snowfall"][weather_index]

            risk = classify_weather(wind, rain, snow, load_lb)
            hourly_forecast = []

            for j, forecast_time in enumerate(forecast_times):
                forecast_timestamp = forecast_time.timestamp()

                if not (
                    departure_timestamp
                    <= forecast_timestamp
                    <= forecast_end
                ):
                    continue

                hour_wind = forecast["wind_speed_10m"][j]
                hour_rain = forecast["rain"][j]
                hour_snow = forecast["snowfall"][j]

                hour_risk = classify_weather(
                    hour_wind,
                    hour_rain,
                    hour_snow,
                    load_lb,
                )

                hourly_forecast.append({
                    "time": forecast_time.isoformat(),
                    "weather": {
                        "wind_mph": hour_wind,
                        "rain_in_hr": hour_rain,
                        "snow_in_hr": hour_snow,
                    },
                    **hour_risk,
                })

            checkpoints.append({
                "mile": point["mile"],
                "latitude": point["latitude"],
                "longitude": point["longitude"],
                "hourly_forecast": hourly_forecast,
                "arrival_utc": datetime.fromtimestamp(
                    point["estimated_arrival"], timezone.utc
                ).isoformat(),
                "weather": {
                    "wind_mph": wind,
                    "rain_in_hr": rain,
                    "snow_in_hr": snow,
                },
                **risk,
            })

        risk_counts = {
            level: sum(
                1
                for point in checkpoints
                if point["overall_risk"] == level
            )
            for level in RISK_SCORE
        }

        average_risk = (
            sum(
                RISK_SCORE[point["overall_risk"]]
                for point in checkpoints
            ) / len(checkpoints)
            if checkpoints
            else float("inf")
        )

        results.append({
            "route_number": route["route_number"],
            "distance_miles": route["distance_miles"],
            "duration_hours": route["duration_hours"],
            "geometry": route["geometry"],
            "checkpoints": checkpoints,
            "risk_summary": {
                "low_checkpoints": risk_counts["Low"],
                "moderate_checkpoints": risk_counts["Moderate"],
                "high_checkpoints": risk_counts["High"],
                "severe_checkpoints": risk_counts["Severe"],
                "no_travel_checkpoints": risk_counts["No Travel"],
                "average_risk_score": round(average_risk, 2),
            },
        })

    def ranking_key(route):
        summary = route["risk_summary"]

        return (
            summary["no_travel_checkpoints"],
            summary["severe_checkpoints"],
            summary["high_checkpoints"],
            summary["average_risk_score"],
            route["duration_hours"],
        )

    results.sort(key=ranking_key)
    recommended_route_number = results[0]["route_number"]

    for route in results:
        route["recommended"] = (
            route["route_number"] == recommended_route_number
        )

    return results
