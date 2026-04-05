from django.urls import path, include

urlpatterns = [
    path("", include("dashboard.urls")),
    path("insights/", include("ai_regression_insights.dashboard_integration.urls")),
]
