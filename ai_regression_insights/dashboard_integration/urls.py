from django.urls import path
from . import views

urlpatterns = [
    path("", views.ai_insights_view, name="ai_insights_view"),
]