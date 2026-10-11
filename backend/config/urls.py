from django.urls import include, path

from config.views import health


urlpatterns = [
    path("api/health", health, name="health"),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.connections.urls")),
    path("api/", include("apps.dashboard.urls")),
]
