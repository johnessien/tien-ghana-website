from django.db import connection
from django.http import HttpResponse


class HealthCheckMiddleware:
    """Answers /healthz before host validation and the HTTPS redirect, so Render's health checker
    (plain HTTP, internal Host header) gets a real answer. Returns 503 if the database is unreachable."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/healthz":
            try:
                with connection.cursor() as cur:
                    cur.execute("SELECT 1")
            except Exception:
                return HttpResponse("database unavailable", status=503, content_type="text/plain")
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
