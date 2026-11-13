from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    """Registration with required fields, email validation, unique email, password confirmation."""

    ROLE_CHOICES = [
        (User.Role.BUYER, "Buyer – I want to find fresh seafood"),
        (User.Role.VENDOR, "Vendor – I run a seafood stall"),
    ]  # ADMIN can never be chosen at sign-up
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="I am a")

    class Meta:
        model = User
        fields = ("full_name", "email", "contact_number", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].required = True
        self.fields["email"].required = True
        self.fields["contact_number"].required = False
        self.fields["password2"].label = "Confirm password"
        self.fields["password2"].error_messages["required"] = "Please confirm your password."

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))
    error_messages = {
        "invalid_login": "Incorrect email or password. Check both and try again.",
        "inactive": "This account is disabled.",
    }

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "email", "contact_number", "profile_photo")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another account already uses this email.")
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if photo and hasattr(photo, "size") and photo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Photo must be 2 MB or smaller.")
        return photo
