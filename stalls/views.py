from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import StallForm
from .models import Stall
from .permissions import can_manage_stall


def stall_updates_queryset():
    from catches.models import CatchUpdate

    return CatchUpdate.objects.select_related("category")


def visible_stalls(user):
    """Admins see every stall; everyone else only sees active ones."""
    qs = Stall.objects.select_related("owner")
    return qs if user.role == User.Role.ADMIN else qs.filter(is_active=True)


@login_required
def stall_list(request):
    q = request.GET.get("q", "").strip()
    stalls = visible_stalls(request.user)
    if q:
        stalls = stalls.filter(Q(stall_name__icontains=q) | Q(location__icontains=q))
    return render(request, "stalls/stall_list.html", {"stalls": stalls, "q": q})


@role_required(User.Role.VENDOR)
def my_stalls(request):
    return render(request, "stalls/my_stalls.html", {"stalls": request.user.stalls.all()})


@login_required
def stall_detail(request, pk):
    stall = get_object_or_404(
        visible_stalls(request.user).prefetch_related(
            Prefetch("updates", queryset=stall_updates_queryset())
        ),
        pk=pk,
    )
    return render(request, "stalls/stall_detail.html", {
        "stall": stall,
        "can_manage": can_manage_stall(request.user, stall),
    })


@role_required(User.Role.VENDOR)
def stall_create(request):
    form = StallForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                stall = form.save(commit=False)
                stall.owner = request.user  # record is linked to the logged-in vendor
                stall.save()
            messages.success(request, f"“{stall.stall_name}” was added.")
            return redirect("stalls:detail", pk=stall.pk)
        messages.error(request, "The stall wasn't saved. Fix the errors below.")
    return render(request, "stalls/stall_form.html", {"form": form, "title": "Add a stall"})


@login_required
def stall_edit(request, pk):
    stall = get_object_or_404(Stall, pk=pk)
    if not can_manage_stall(request.user, stall):
        messages.error(request, "You can only edit your own stalls.")
        return redirect("accounts:dashboard")
    form = StallForm(request.POST or None, instance=stall)
    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, "Stall updated.")
            return redirect("stalls:detail", pk=stall.pk)
        messages.error(request, "Your changes weren't saved. Fix the errors below.")
    return render(request, "stalls/stall_form.html", {"form": form, "title": "Edit stall", "stall": stall})


@login_required
def stall_delete(request, pk):
    stall = get_object_or_404(Stall, pk=pk)
    if not can_manage_stall(request.user, stall):
        messages.error(request, "You can only delete your own stalls.")
        return redirect("accounts:dashboard")
    if request.method == "POST":
        name = stall.stall_name
        with transaction.atomic():  # removes the stall and its catch updates together
            stall.delete()
        messages.success(request, f"“{name}” was deleted.")
        return redirect("accounts:dashboard")
    return render(request, "stalls/stall_confirm_delete.html", {"stall": stall})
