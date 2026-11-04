"""Tests for project-level settings and middleware."""

import pytest


def test_healthz_works_with_any_host_and_plain_http(client, settings):
    settings.SECURE_SSL_REDIRECT = True
    # Render may send the container's internal IP as Host.
    response = client.get("/healthz/", HTTP_HOST="10.0.0.12:10000")

    assert response.status_code == 200
    assert response.content == b"ok"


@pytest.mark.django_db
def test_unknown_host_is_rejected(client, settings):
    settings.ALLOWED_HOSTS = ["liftlog.onrender.com"]

    response = client.get("/accounts/login/", HTTP_HOST="evil.example")

    assert response.status_code == 400


@pytest.mark.django_db
def test_http_redirects_to_https_in_production(client, settings):
    settings.SECURE_SSL_REDIRECT = True

    response = client.get("/accounts/login/")

    assert response.status_code == 301
    assert response.url.startswith("https://")
