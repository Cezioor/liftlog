from django.http import HttpResponse


class HealthCheckMiddleware:
    """Answer Render's health check before any other middleware runs.

    Render may call it with the container's internal IP as the Host header, which
    ALLOWED_HOSTS would reject (400), and over plain HTTP, which SECURE_SSL_REDIRECT
    would redirect. Answering first avoids both. It doesn't touch the database,
    so a suspended Neon database can't make the service look unhealthy.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/healthz/":
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
