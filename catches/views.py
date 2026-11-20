from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from stalls.models import SeafoodCategory, Stall

from .forms import CatchUpdateForm
from .models import CatchUpdate


def can_manage_update(user, update):
    """The vendor who posted it, or an administrator."""
    return user.is_authenticated and (user.role == User.Role.ADMIN or update.posted_by_id == user.pk)


@login_required
def catch_list(request):
    """Browse and search seafood posted by active stalls."""
    q = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    updates = CatchUpdate.objects.filter(stall__is_active=True).select_related("stall", "category")
    if q:
        updates = updates.filter(
            Q(category__name__icontains=q) | Q(stall__stall_name__icontains=q) | Q(stall__location__icontains=q)
        )
    if category_id.isdigit():
        updates = updates.filter(category_id=int(category_id))
    return render(request, "catches/catch_list.html", {
        "updates": updates[:100],
        "categories": SeafoodCategory.objects.all(),
        "q": q,
        "selected_category": category_id,
    })


@role_required(User.Role.VENDOR)
def my_updates(request):
    updates = CatchUpdate.objects.filter(posted_by=request.user).select_related("stall", "category")
    return render(request, "catches/my_updates.html", {"updates": updates})


@role_required(User.Role.VENDOR)
def catch_create(request):
    if not Stall.objects.filter(owner=request.user, is_active=True).exists():
        messages.error(request, "Add an open stall first, then you can post your catch.")
        return redirect("stalls:create")
    initial = {}
    if request.GET.get("stall", "").isdigit():
        initial["stall"] = int(request.GET["stall"])
    form = CatchUpdateForm(request.POST or None, user=request.user, initial=initial)
    if request.method == "POST":
        if form.is_valid():
            update = form.save(commit=False)
            update.posted_by = request.user  # record is linked to the logged-in vendor
            update.save()
            messages.success(request, f"{update.category} posted for {update.stall}.")
            return redirect("catches:mine")
        messages.error(request, "The update wasn't posted. Fix the errors below.")
    return render(request, "catches/catch_form.html", {"form": form, "title": "Post a catch update"})


@login_required
def catch_edit(request, pk):
    update = get_object_or_404(CatchUpdate, pk=pk)
    if not can_manage_update(request.user, update):
        messages.error(request, "You can only edit your own updates.")
        return redirect("accounts:dashboard")
    form = CatchUpdateForm(request.POST or None, instance=update, user=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Update saved.")
            return redirect("catches:mine" if request.user.role == User.Role.VENDOR else "catches:list")
        messages.error(request, "Your changes weren't saved. Fix the errors below.")
    return render(request, "catches/catch_form.html", {"form": form, "title": "Edit catch update", "update": update})


@login_required
def catch_delete(request, pk):
    update = get_object_or_404(CatchUpdate, pk=pk)
    if not can_manage_update(request.user, update):
        messages.error(request, "You can only delete your own updates.")
        return redirect("accounts:dashboard")
    if request.method == "POST":
        update.delete()
        messages.success(request, "Update deleted.")
        return redirect("catches:mine" if request.user.role == User.Role.VENDOR else "catches:list")
    return render(request, "catches/catch_confirm_delete.html", {"update": update})
