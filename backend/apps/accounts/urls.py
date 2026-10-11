from django.urls import path

from apps.accounts import views


urlpatterns = [
    path("session", views.current_session, name="current-session"),
    path("signup", views.signup, name="signup"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("users/count", views.user_count, name="user-count"),
]
