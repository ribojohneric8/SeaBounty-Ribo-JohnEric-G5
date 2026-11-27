from decimal import Decimal

from django import forms
from django.utils import timezone

from stalls.models import Stall

from .models import CatchUpdate

MAX_PRICE = Decimal("100000")


class CatchUpdateForm(forms.ModelForm):
    class Meta:
        model = CatchUpdate
        fields = ("stall", "category", "price_per_kg", "notes")
        labels = {"price_per_kg": "Price per kg (₱)", "notes": "Notes (optional)"}
        widgets = {
            "price_per_kg": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "notes": forms.TextInput(attrs={"placeholder": "e.g. about 5 kg left, caught this morning"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        # A vendor can only post to their own ACTIVE stalls (BR-06).
        self.fields["stall"].queryset = Stall.objects.filter(owner=user, is_active=True)
        self.fields["stall"].empty_label = "Choose one of your stalls"
        self.fields["category"].empty_label = "Choose seafood"
        if self.instance.pk:
            # The stall of an existing post can't be changed (edit price / seafood only).
            self.fields["stall"].queryset = Stall.objects.filter(pk=self.instance.stall_id)
            self.fields["stall"].disabled = True

    def clean_price_per_kg(self):
        price = self.cleaned_data["price_per_kg"]
        if price <= 0:
            raise forms.ValidationError("Price per kg must be greater than zero.")
        if price > MAX_PRICE:
            raise forms.ValidationError("That price looks too high. Please check it.")
        return price

    def clean(self):
        cleaned = super().clean()
        stall, category = cleaned.get("stall"), cleaned.get("category")
        if stall and category:
            # Business rule: one post per seafood type per stall per day (edit it instead of re-posting).
            start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
            duplicate = CatchUpdate.objects.filter(stall=stall, category=category, date_posted__gte=start)
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise forms.ValidationError(
                    f"{category} was already posted for {stall} today. Edit that post instead of adding another."
                )
        return cleaned

    def clean_notes(self):
        return " ".join(self.cleaned_data.get("notes", "").split())
