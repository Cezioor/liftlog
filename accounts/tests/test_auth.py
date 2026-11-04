import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_signup_creates_user_and_logs_in(client):
    response = client.post(
        reverse("signup"),
        {
            "username": "ania",
            "email": "ania@example.com",
            "password1": "Squat-Heavy-2026",
            "password2": "Squat-Heavy-2026",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("home")
    user = User.objects.get(username="ania")
    assert user.email == "ania@example.com"
    # The session now belongs to the new user.
    assert int(client.session["_auth_user_id"]) == user.pk


@pytest.mark.django_db
def test_signup_requires_email(client):
    response = client.post(
        reverse("signup"),
        {"username": "ania", "password1": "Squat-Heavy-2026", "password2": "Squat-Heavy-2026"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["email"]
    assert not User.objects.exists()


@pytest.mark.django_db
def test_login_and_logout(client, django_user_model):
    django_user_model.objects.create_user(username="ania", password="Squat-Heavy-2026")

    response = client.post(reverse("login"), {"username": "ania", "password": "Squat-Heavy-2026"})
    assert response.status_code == 302
    assert response.url == reverse("home")

    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_home_requires_login(client):
    response = client.get(reverse("home"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["login", "signup", "password_reset"])
def test_auth_pages_render(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 200


@pytest.mark.django_db
def test_password_reset_sends_email(client, django_user_model, mailoutbox):
    django_user_model.objects.create_user(
        username="ania", email="ania@example.com", password="Squat-Heavy-2026"
    )

    response = client.post(reverse("password_reset"), {"email": "ania@example.com"})

    assert response.status_code == 302
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["ania@example.com"]
