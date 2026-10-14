
import json
import traceback

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from routing.risk_engine import classify_weather
from routing.route_analysis import analyze_route


@csrf_exempt
@require_POST
def calculate_risk(request):
    try:
        data = json.loads(request.body)
        result = classify_weather(
            float(data["wind_mph"]),
            float(data["rain_in_hr"]),
            float(data["snow_in_hr"]),
            float(data["load_lb"]),
        )
        return JsonResponse(result)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@csrf_exempt
@require_POST
def analyze_routes_view(request):
    try:
        data = json.loads(request.body)
        results = analyze_route(
            origin_name=data["origin"],
            destination_name=data["destination"],
            departure_time=data["departure_time"],
            load_lb=float(data["load_lb"]),
            interval_miles=int(data.get("interval_miles", 25)),
        )
        return JsonResponse({"routes": results})

    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=502)
