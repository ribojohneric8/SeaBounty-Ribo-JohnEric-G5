from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from stalls.models import SeafoodCategory, Stall


class CatchUpdate(models.Model):
    """A vendor's post about seafood available at a stall (SDD: catch_updates)."""

    update_id = models.AutoField(primary_key=True)
    # stalls 1 : M catch_updates (BR-06, ON DELETE CASCADE)
    stall = models.ForeignKey(Stall, on_delete=models.CASCADE, related_name="updates")
    # seafood_categories 1 : M catch_updates
    category = models.ForeignKey(SeafoodCategory, on_delete=models.CASCADE, related_name="updates")
    # users 1 : M catch_updates (who posted it)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="catch_updates",
    )
    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100000"))],
    )
    # ISS-01: optional short note (e.g. "about 5 kg left", "caught this morning")
    notes = models.CharField(max_length=200, blank=True, default="")
    date_posted = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "catch_updates"
        ordering = ["-date_posted", "-update_id"]
        constraints = [
            # BR-04: price per kg must be greater than zero
            models.CheckConstraint(condition=Q(price_per_kg__gt=0), name="catch_price_positive"),
        ]

    def __str__(self):
        return f"{self.category} at {self.stall} (₱{self.price_per_kg}/kg)"
