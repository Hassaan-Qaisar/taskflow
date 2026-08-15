from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import EmailVerification, User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError("No user registered with this email.")
        return super().confirm_login_allowed(user)


class RegisterForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.is_active:
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1, p2 = cleaned_data.get("password1"), cleaned_data.get("password2")
        if p1 and p2:
            if p1 != p2:
                raise ValidationError("Passwords do not match.")
            validate_password(p1)
        return cleaned_data

    def save(self):
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        existing_user = User.objects.filter(email=email).first()

        if existing_user and not existing_user.is_active:
            existing_user.name = self.cleaned_data["name"]
            existing_user.set_password(password)
            existing_user.is_active = False
            existing_user.email_verified = False
            existing_user.auth_provider = User.AuthProvider.EMAIL
            existing_user.save(update_fields=["name", "password", "is_active", "email_verified", "auth_provider"])
            verification, _ = EmailVerification.objects.get_or_create(user=existing_user)
            verification.last_sent_at = None
            verification.save(update_fields=["last_sent_at"])
            return existing_user

        user = User.objects.create_user(
            email=email,
            name=self.cleaned_data["name"],
            password=password,
            is_active=False,
            email_verified=False,
            auth_provider=User.AuthProvider.EMAIL,
        )
        EmailVerification.objects.create(user=user)
        return user


class ResendVerificationForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data["email"]

        email = email.lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("No account found with that email.")

        if user.is_active:
            raise ValidationError("This account is already verified.")

        verification = EmailVerification.objects.filter(user=user).first()
        if verification and verification.last_sent_at:
            throttle_window = timezone.now() - timedelta(minutes=1)
            if verification.last_sent_at > throttle_window:
                raise ValidationError("Please wait 1 minute before requesting another verification email.")

        return email