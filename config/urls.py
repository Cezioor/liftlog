from django.contrib import admin
from django.urls import include, path

from workouts.views import home

# /healthz/ (Render's health check) is answered by config.middleware.HealthCheckMiddleware.
urlpatterns = [
    path("", home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("exercises/", include("exercises.urls")),
    path("plans/", include("plans.urls")),
    path("workouts/", include("workouts.urls")),
    path("admin/", admin.site.urls),
]
