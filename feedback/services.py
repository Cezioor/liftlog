"""Feedback reports: device detection, the hourly limit, saving and the email to the owner."""

import logging
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone

from .models import Device, Feedback

logger = logging.getLogger(__name__)

HOURLY_LIMIT = 5


def device_from_user_agent(user_agent):
    """Rough device type from the browser's User-Agent; good enough to group reports.

    iPads that ask for desktop sites report as Macs, so they count as computers.
    """
    ua = (user_agent or "").lower()
    if not ua:
        return Device.UNKNOWN
    if "ipad" in ua or "tablet" in ua or ("android" in ua and "mobile" not in ua):
        return Device.TABLET
    if "iphone" in ua or "mobile" in ua or "android" in ua:
        return Device.PHONE
    return Device.COMPUTER


def page_path(url):
    """Only the path and query of the page ("/workouts/12/?add=3"), never another host."""
    parts = urlsplit(url or "")
    path = parts.path if parts.path.startswith("/") else ""
    if path.startswith("//"):
        path = ""
    query = f"?{parts.query}" if path and parts.query else ""
    return (path + query)[:500]


def over_limit(user):
    """True when the user already sent HOURLY_LIMIT reports in the last hour."""
    since = timezone.now() - timedelta(hours=1)
    return Feedback.objects.filter(user=user, created_at__gte=since).count() >= HOURLY_LIMIT


def save_feedback(user, kind, message, page, user_agent, site_url=""):
    """Store the report, then email it. A failed email never loses the report."""
    feedback = Feedback.objects.create(
        user=user,
        kind=kind,
        message=message,
        page=page_path(page),
        device=device_from_user_agent(user_agent),
        user_agent=(user_agent or "")[:300],
    )
    notify_owner(feedback, site_url)
    return feedback


def notify_owner(feedback, site_url=""):
    """Email the report to FEEDBACK_EMAIL (Brevo in production, console locally).

    Returns True if it was sent. Errors are logged with the report's id only, no
    personal data; the report is already saved.
    """
    to = settings.FEEDBACK_EMAIL
    if not to:
        logger.warning("Feedback #%s saved; FEEDBACK_EMAIL is not set, no email sent", feedback.pk)
        return False
    user = feedback.user
    who = f"{user.get_username()} <{user.email}>" if user else "(deleted account)"
    admin_url = site_url.rstrip("/") + reverse("admin:feedback_feedback_change", args=[feedback.pk])
    body = (
        f"Rodzaj: {feedback.get_kind_display()}\n"
        f"Użytkownik: {who}\n"
        f"Strona: {feedback.page or '–'}\n"
        f"Urządzenie: {feedback.get_device_display()}\n"
        f"Wysłano: {timezone.localtime(feedback.created_at):%Y-%m-%d %H:%M}\n"
        f"Panel admina: {admin_url}\n"
        f"\n{feedback.message}\n"
    )
    first_line = " ".join(feedback.message.split())[:60]
    message = EmailMessage(
        subject=f"[LiftLog] {feedback.get_kind_display()} #{feedback.pk}: {first_line}",
        body=body,
        to=[to],
        reply_to=[user.email] if user and user.email else None,
    )
    try:
        message.send()
    except Exception:
        logger.exception("Feedback #%s saved, but the email to the owner failed", feedback.pk)
        return False
    return True
