
def classify_weather(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    # Wind risk
    if wind_mph >= 55:
        wind = "No Travel"
    elif wind_mph >= 45:
        wind = "No Travel" if load_lb > 30000 else "Severe"
    elif wind_mph >= 35:
        wind = "Severe" if load_lb > 40000 else "High"
    elif wind_mph >= 25:
        wind = "Moderate"
    else:
        wind = "Low"

    # Rain risk
    if rain_in_hr > 1.0:
        rain = "No Travel"
    elif rain_in_hr >= 0.5:
        rain = "Severe"
    elif rain_in_hr >= 0.25:
        rain = "High"
    elif rain_in_hr >= 0.10:
        rain = "Moderate"
    else:
        rain = "Low"

    # Snow risk
    if snow_in_hr > 3.0:
        snow = "No Travel"
    elif snow_in_hr >= 2.0:
        snow = "Severe"
    elif snow_in_hr >= 1.0:
        snow = "High"
    elif snow_in_hr >= 0.5:
        snow = "Moderate"
    else:
        snow = "Low"

    levels = ["Low", "Moderate", "High", "Severe", "No Travel"]
    risks = [wind, rain, snow]
    overall = max(risks, key=levels.index)

    return {
        "wind_risk": wind,
        "rain_risk": rain,
        "snow_risk": snow,
        "overall_risk": overall,
    }

