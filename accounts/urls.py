from django.urls import include, path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("settings/", views.settings_view, name="settings"),
    # Django's built-in views: login, logout, password_change, password_reset, ...
    # They look for templates in templates/registration/.
    path("", include("django.contrib.auth.urls")),
]
