from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("alerts/", views.alerts_view, name="alerts"),
    path("simulation-results/", views.simulation_results_view, name="simulation_results"),
    
    # Simple JSON endpoints
    path("api/timeseries/", views.timeseries_api, name="timeseries_api"),
    path("api/alerts/", views.alerts_api, name="alerts_api"),
    path("api/alerts/acknowledge/", views.acknowledge_alert_api, name="acknowledge_alert_api"),
    path("api/alerts/resolve/", views.resolve_alert_api, name="resolve_alert_api"),
]
