from django.urls import path

from apps.dashboard import views


urlpatterns = [
    path("dashboard/overview", views.dashboard_overview, name="dashboard-overview"),
]
