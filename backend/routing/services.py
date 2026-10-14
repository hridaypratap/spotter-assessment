
import requests
from django.conf import settings


def get_routes(origin, destination):
    token = settings.MAPBOX_ACCESS_TOKEN

    if not token:
        raise ValueError("Mapbox token is not configured")

    if (
        not isinstance(origin, (list, tuple))
        or len(origin) != 2
        or not isinstance(destination, (list, tuple))
        or len(destination) != 2
    ):
        raise ValueError(
            "Invalid coordinates. Expected [longitude, latitude]."
        )

    try:
        origin_lon, origin_lat = map(float, origin)
        destination_lon, destination_lat = map(float, destination)
    except (TypeError, ValueError):
        raise ValueError("Coordinates must be valid numbers.")

    for longitude, latitude in (
        (origin_lon, origin_lat),
        (destination_lon, destination_lat),
    ):
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180.")
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90.")

    coordinates = (
        f"{origin_lon},{origin_lat};"
        f"{destination_lon},{destination_lat}"
    )

    url = (
        "https://api.mapbox.com/directions/v5/"
        f"mapbox/driving/{coordinates}"
    )

    try:
        response = requests.get(
            url,
            params={
                "alternatives": "true",
                "geometries": "geojson",
                "overview": "full",
                "access_token": token,
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        raise ValueError(
            f"Could not connect to Mapbox Directions: {exc}"
        ) from exc

    if not response.ok:
        try:
            error_data = response.json()
            error_message = error_data.get(
                "message", "Unknown Mapbox error"
            )
            error_code = error_data.get("code", "Unknown")
        except ValueError:
            error_code = "Unknown"
            error_message = "Mapbox returned an unreadable error response"

        raise ValueError(
            f"Mapbox Directions error ({response.status_code}, "
            f"{error_code}): {error_message}"
        )

    data = response.json()
    routes = data.get("routes", [])

    if not routes:
        raise ValueError(
            "Mapbox found no driving routes between these locations."
        )

    return routes
