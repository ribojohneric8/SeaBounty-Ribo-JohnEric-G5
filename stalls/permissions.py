from accounts.models import User


def can_manage_stall(user, stall):
    """Owner of the stall, or an administrator."""
    return user.is_authenticated and (user.role == User.Role.ADMIN or stall.owner_id == user.pk)
