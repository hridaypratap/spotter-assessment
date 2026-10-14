
import requests
from django.conf import settings


def geocode_place(place):
    if not settings.MAPBOX_ACCESS_TOKEN:
        raise ValueError("Mapbox token is not configured")

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(place)}.json"

    response = requests.get(
        url,
        params={
            "access_token": settings.MAPBOX_ACCESS_TOKEN,
            "limit": 1,
            "types": "place,locality,address",
        },
        timeout=15,
    )
    response.raise_for_status()

    features = response.json().get("features", [])
    if not features:
        raise ValueError(f"Place not found: {place}")

    return features[0]["center"]  # [longitude, latitude]

