from django.urls import path

from apps.connections import views


urlpatterns = [
    path("datasources", views.list_or_create_datasources, name="datasources"),
    path("datasources/<uuid:datasource_id>", views.datasource_detail, name="datasource-detail"),
    path("datasources/<uuid:datasource_id>/analysis", views.analyse_datasource, name="datasource-analysis"),
]
