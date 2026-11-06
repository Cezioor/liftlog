from allauth.account.decorators import secure_admin_login
from django.contrib import admin
from django.urls import include, path

from workouts.views import home

# The admin logs in through the app's own login (email, rate limits) instead of its own
# username form; only staff accounts get in.
admin.site.login = secure_admin_login(admin.site.login)
admin.site.site_header = "LiftLog: administracja"

# /healthz/ (Render's health check) is answered by config.middleware.HealthCheckMiddleware.
urlpatterns = [
    path("", home, name="home"),
    # Our account pages first: they override some of allauth's at the same URLs.
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("exercises/", include("exercises.urls")),
    path("plans/", include("plans.urls")),
    path("workouts/", include("workouts.urls")),
    path("feedback/", include("feedback.urls")),
    path("admin/", admin.site.urls),
]
