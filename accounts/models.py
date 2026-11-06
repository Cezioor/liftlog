from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model.

    Empty for now, but Django strongly recommends defining it at the start of a
    project: switching AUTH_USER_MODEL later, once tables exist, is very painful.
    """


class EffortScale(models.TextChoices):
    """How the user rates a set. Every scale is stored as RIR (see WorkoutSet.rir)."""

    SIMPLE = "simple", _("Simple: Easy / Medium / Hard / Max effort")
    RIR = "rir", _("RIR: reps left in the tank (0, 1, 2, 3, 4+)")
    RPE = "rpe", _("RPE: effort from 6 to 10 (RPE = 10 − RIR)")


class UserSettings(models.Model):
    """Per-user preferences. Created on first use by accounts.services.get_user_settings."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_settings"
    )
    ios_shortcut_enabled = models.BooleanField(
        _("iPhone Clock timer via Shortcuts"),
        default=False,
        help_text=_("After each set, show a button that starts a timer in the iPhone Clock app."),
    )
    ios_shortcut_name = models.CharField(
        _("shortcut name"),
        max_length=100,
        default="LiftLog Rest",
        help_text=_("Exactly the name of the shortcut in the Shortcuts app."),
    )
    keep_screen_on = models.BooleanField(
        _("keep the screen on during a workout"),
        default=False,
        help_text=_("Uses more battery. Needs a browser that supports it (HTTPS only)."),
    )
    rest_end_sound = models.BooleanField(
        _("beep when the rest is over"),
        default=True,
        help_text=_("Only while LiftLog is on screen; a locked phone can't play it."),
    )

    effort_scale = models.CharField(
        _("how to rate sets"),
        max_length=6,
        choices=EffortScale.choices,
        default=EffortScale.SIMPLE,
        help_text=_("Changing it only changes how ratings look; saved ratings stay the same."),
    )
    # "" = not chosen yet: the cookie or the browser decides (config.middleware).
    # Set at sign-up, by the PL · EN switcher and in Settings.
    language = models.CharField(
        _("language"), max_length=5, choices=settings.LANGUAGES, blank=True, default=""
    )

    class Meta:
        verbose_name = _("user settings")
        verbose_name_plural = _("user settings")

    def __str__(self):
        return f"Settings of {self.user}"
