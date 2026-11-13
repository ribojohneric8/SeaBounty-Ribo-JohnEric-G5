from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def role_required(*roles):
    """Allow only logged-in users whose role is in `roles`.
    Logged-out users go to login; wrong-role users go back to their own dashboard."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role not in roles:
                messages.error(request, "You don't have access to that page.")
                return redirect("accounts:dashboard")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
