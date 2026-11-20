from django import forms

from .models import Stall


class StallForm(forms.ModelForm):
    class Meta:
        model = Stall
        fields = ("stall_name", "location", "operating_hours", "is_active")
        labels = {"stall_name": "Stall name", "is_active": "Stall is open for business"}
        widgets = {
            "location": forms.Textarea(attrs={"rows": 3}),
            "operating_hours": forms.TextInput(attrs={"placeholder": "e.g. 5:00 AM - 11:00 AM"}),
        }

    def clean_stall_name(self):
        name = " ".join(self.cleaned_data["stall_name"].split())
        if len(name) < 3:
            raise forms.ValidationError("Stall name must be at least 3 characters.")
        duplicates = Stall.objects.filter(stall_name__iexact=name).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A stall with this name already exists.")
        return name

    def clean_location(self):
        location = self.cleaned_data["location"].strip()
        if len(location) < 5:
            raise forms.ValidationError("Please give a more specific location or landmark.")
        return location
