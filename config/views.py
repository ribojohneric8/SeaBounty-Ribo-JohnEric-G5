"""Friendly error pages used instead of Django's debug pages."""
from django.shortcuts import render


def bad_request(request, exception=None):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    # Rendered without a request context so it can't fail on a broken session/database.
    return render(None, "errors/500.html", status=500)


def csrf_failure(request, reason=""):
    return render(request, "errors/403_csrf.html", status=403)
