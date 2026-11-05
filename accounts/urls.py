from django.urls import path

from . import views

# Included before allauth's URLs (config/urls.py), so the "confirm-email/" page below
# replaces allauth's own. Everything else (login, signup, logout, password reset,
# confirming the emailed link) comes from allauth.
urlpatterns = [
    path("settings/", views.settings_view, name="settings"),
    path(
        "confirm-email/",
        views.VerificationSentView.as_view(),
        name="account_email_verification_sent",
    ),
    path("confirm-email/resend/", views.resend_verification, name="resend_verification"),
]
