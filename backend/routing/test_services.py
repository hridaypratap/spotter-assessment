from routing.services import get_routes

origin = (-74.0060, 40.7128)       # New York
destination = (-71.0589, 42.3601)  # Boston

try:
    routes = get_routes(origin, destination)
    print("Routes received:", len(routes))

    for i, route in enumerate(routes, 1):
        print(
            f"Route {i}: "
            f"{route['distance'] / 1000:.1f} km, "
            f"{route['duration'] / 3600:.2f} hours"
        )
except Exception as e:
    print("Routing error:", e)