"""How django-allauth behaves in LiftLog (messages, where to go after sign-up)."""

from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    error_messages = {
        **DefaultAccountAdapter.error_messages,
        # The sign-up page adds links to "log in" and "reset your password" under it.
        "email_taken": "An account with this email already exists.",
    }

    def add_message(self, request, level, message_template=None, *args, **kwargs):
        # The "check your email" page already says where the link went.
        if message_template == "account/messages/email_confirmation_sent.txt":
            return
        super().add_message(request, level, message_template, *args, **kwargs)
