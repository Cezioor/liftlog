from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model.

    Empty for now, but Django strongly recommends defining it at the start of a
    project: switching AUTH_USER_MODEL later, once tables exist, is very painful.
    """
