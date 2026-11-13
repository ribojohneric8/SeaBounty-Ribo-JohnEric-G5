from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import User

DASHBOARD_BY_ROLE = {
    User.Role.BUYER: "accounts:buyer_dashboard",
    User.Role.VENDOR: "accounts:vendor_dashboard",
    User.Role.ADMIN: "accounts:admin_dashboard",
}


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return redirect("accounts:login")


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! You can now log in.")
            return redirect("accounts:login")
        messages.error(request, "Please fix the errors below.")
    return render(request, "accounts/register.html", {"form": form})


class SeaBountyLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {form.get_user().full_name}!")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Login failed. Check your email and password.")
        return super().form_invalid(form)


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You've been logged out.")
    return redirect("accounts:login")


@login_required
def dashboard(request):
    """Send each user to the dashboard for their role."""
    return redirect(DASHBOARD_BY_ROLE[request.user.role])


@role_required(User.Role.BUYER)
def buyer_dashboard(request):
    return render(request, "accounts/dashboard_buyer.html")


@role_required(User.Role.VENDOR)
def vendor_dashboard(request):
    return render(request, "accounts/dashboard_vendor.html")


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    counts = {r["role"]: r["n"] for r in User.objects.values("role").annotate(n=Count("pk"))}
    context = {
        "total_users": sum(counts.values()),
        "buyers": counts.get(User.Role.BUYER, 0),
        "vendors": counts.get(User.Role.VENDOR, 0),
        "admins": counts.get(User.Role.ADMIN, 0),
        "recent_users": User.objects.order_by("-created_at")[:5],
    }
    return render(request, "accounts/dashboard_admin.html", context)


@login_required
def profile(request):
    # No user id in the URL: a user can only ever see their own profile.
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
        messages.error(request, "Your profile wasn't saved. Fix the errors below.")
    return render(request, "accounts/profile_edit.html", {"form": form})
