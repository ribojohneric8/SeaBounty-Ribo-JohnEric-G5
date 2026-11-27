from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class SeafoodCategory(models.Model):
    """Lookup table of seafood types (SDD: seafood_categories)."""

    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "seafood_categories"
        ordering = ["name"]
        verbose_name_plural = "seafood categories"

    def __str__(self):
        return self.name


class Stall(models.Model):
    """A seafood stall owned by one vendor (SDD: stalls)."""

    stall_id = models.AutoField(primary_key=True)
    # users 1 : M stalls. Deleting a user deletes their stalls (ON DELETE CASCADE).
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="stalls",
    )
    stall_name = models.CharField(max_length=100, unique=True, validators=[MinLengthValidator(3)])  # BR-03
    location = models.TextField(validators=[MinLengthValidator(5)])
    operating_hours = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "stalls"
        ordering = ["stall_name"]

    def __str__(self):
        return self.stall_name
