from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("alerts/", views.alerts_view, name="alerts"),
    
    # Simple JSON endpoints
    path("api/timeseries/", views.timeseries_api, name="timeseries_api"),
    path("api/alerts/", views.alerts_api, name="alerts_api"),
]
