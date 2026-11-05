from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model.

    Empty for now, but Django strongly recommends defining it at the start of a
    project: switching AUTH_USER_MODEL later, once tables exist, is very painful.
    """


class EffortScale(models.TextChoices):
    """How the user rates a set. Every scale is stored as RIR (see WorkoutSet.rir)."""

    SIMPLE = "simple", "Simple: Easy / Medium / Hard / Max effort"
    RIR = "rir", "RIR: reps left in the tank (0, 1, 2, 3, 4+)"
    RPE = "rpe", "RPE: effort from 6 to 10 (RPE = 10 − RIR)"


class UserSettings(models.Model):
    """Per-user preferences. Created on first use by accounts.services.get_user_settings."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_settings"
    )
    ios_shortcut_enabled = models.BooleanField(
        "iPhone Clock timer via Shortcuts",
        default=False,
        help_text="After each set, show a button that starts a timer in the iPhone Clock app.",
    )
    ios_shortcut_name = models.CharField(
        "shortcut name",
        max_length=100,
        default="LiftLog Rest",
        help_text="Exactly the name of the shortcut in the Shortcuts app.",
    )
    keep_screen_on = models.BooleanField(
        "keep the screen on during a workout",
        default=False,
        help_text="Uses more battery. Needs a browser that supports it (HTTPS only).",
    )
    rest_end_sound = models.BooleanField(
        "beep when the rest is over",
        default=True,
        help_text="Only while LiftLog is on screen; a locked phone can't play it.",
    )

    effort_scale = models.CharField(
        "how to rate sets",
        max_length=6,
        choices=EffortScale.choices,
        default=EffortScale.SIMPLE,
        help_text="Changing it only changes how ratings look; saved ratings stay the same.",
    )

    class Meta:
        verbose_name_plural = "user settings"

    def __str__(self):
        return f"Settings of {self.user}"
