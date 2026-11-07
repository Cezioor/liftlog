from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class Kind(models.TextChoices):
    BUG = "bug", _("Bug")
    SUGGESTION = "suggestion", _("Suggestion")
    OPINION = "opinion", _("Opinion")


class Status(models.TextChoices):
    NEW = "new", pgettext_lazy("report status", "New")
    IN_PROGRESS = "in_progress", pgettext_lazy("report status", "In progress")
    DONE = "done", pgettext_lazy("report status", "Done")


class Device(models.TextChoices):
    PHONE = "phone", _("Phone")
    TABLET = "tablet", _("Tablet")
    COMPUTER = "computer", _("Computer")
    UNKNOWN = "unknown", _("Unknown")


MESSAGE_MAX_LENGTH = 2000


class Feedback(models.Model):
    """A bug report, a suggestion or an opinion sent from any screen of the app.

    The page, the user, the time and the device are filled in automatically.
    """

    # SET_NULL: deleting an account keeps the report (without who sent it).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="feedback",
    )
    kind = models.CharField(_("kind"), max_length=20, choices=Kind.choices)
    message = models.TextField(_("message"), max_length=MESSAGE_MAX_LENGTH)
    page = models.CharField(_("page"), max_length=500, blank=True)
    device = models.CharField(
        _("device"), max_length=10, choices=Device.choices, default=Device.UNKNOWN
    )
    user_agent = models.CharField(max_length=300, blank=True)
    status = models.CharField(
        _("status"), max_length=20, choices=Status.choices, default=Status.NEW
    )
    created_at = models.DateTimeField(_("sent"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("report")
        verbose_name_plural = _("reports")

    def __str__(self):
        return f"#{self.pk} {self.get_kind_display()}: {self.message[:50]}"
