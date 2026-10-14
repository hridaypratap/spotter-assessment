from django.urls import path
from .views import calculate_risk, analyze_routes_view

urlpatterns = [
    path("risk/", calculate_risk, name="calculate-risk"),
    path("analyze/", analyze_routes_view, name="analyze-routes"),
]