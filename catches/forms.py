from decimal import Decimal

from django import forms

from stalls.models import Stall

from .models import CatchUpdate

MAX_PRICE = Decimal("100000")


class CatchUpdateForm(forms.ModelForm):
    class Meta:
        model = CatchUpdate
        fields = ("stall", "category", "price_per_kg")
        labels = {"price_per_kg": "Price per kg (₱)"}
        widgets = {"price_per_kg": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"})}

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
