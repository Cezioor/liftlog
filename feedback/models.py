from django.conf import settings
from django.db import models


class Kind(models.TextChoices):
    BUG = "bug", "Błąd"
    SUGGESTION = "suggestion", "Sugestia zmiany"
    OPINION = "opinion", "Opinia"


class Status(models.TextChoices):
    NEW = "new", "Nowe"
    IN_PROGRESS = "in_progress", "W trakcie"
    DONE = "done", "Załatwione"


class Device(models.TextChoices):
    PHONE = "phone", "Telefon"
    TABLET = "tablet", "Tablet"
    COMPUTER = "computer", "Komputer"
    UNKNOWN = "unknown", "Nieznane"


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
    kind = models.CharField("rodzaj", max_length=20, choices=Kind.choices)
    message = models.TextField("treść", max_length=MESSAGE_MAX_LENGTH)
    page = models.CharField("strona", max_length=500, blank=True)
    device = models.CharField(
        "urządzenie", max_length=10, choices=Device.choices, default=Device.UNKNOWN
    )
    user_agent = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("wysłano", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "zgłoszenie"
        verbose_name_plural = "zgłoszenia"

    def __str__(self):
        return f"#{self.pk} {self.get_kind_display()}: {self.message[:50]}"
