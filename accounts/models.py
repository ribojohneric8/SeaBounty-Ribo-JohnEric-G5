from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)  # hashes the password
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.ADMIN)
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Maps to the `users` table in the SDD (BR-01, BR-02)."""

    class Role(models.TextChoices):
        BUYER = "BUYER", "Buyer"
        VENDOR = "VENDOR", "Vendor"
        ADMIN = "ADMIN", "Administrator"

    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=150, unique=True)  # BR-01
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.BUYER)
    contact_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        constraints = [
            # BR-02: role must be BUYER, VENDOR, or ADMIN
            models.CheckConstraint(
                condition=models.Q(role__in=["BUYER", "VENDOR", "ADMIN"]),
                name="users_role_valid",
            )
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def is_buyer(self):
        return self.role == self.Role.BUYER

    @property
    def is_vendor(self):
        return self.role == self.Role.VENDOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
