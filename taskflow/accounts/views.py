from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic import FormView, TemplateView

from .forms import EmailAuthenticationForm, RegisterForm, ResendVerificationForm
from .models import EmailVerification, User
from .tasks import send_verification_email
from .tokens import email_verification_token


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("accounts:verify-email-sent")
    max_attempts = 5
    lockout_timeout_seconds = 15 * 60

    def get_client_ip(self):
        forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR", "unknown")

    def get_attempt_keys(self, email=None):
        normalized_email = (email or "").strip().lower()
        client_ip = self.get_client_ip()
        keys = [f"register:ip:{client_ip}"]
        if normalized_email:
            keys.append(f"register:user:{normalized_email}")
        return keys

    def is_rate_limited(self, email=None):
        for key in self.get_attempt_keys(email=email):
            if cache.get(key, 0) >= self.max_attempts:
                return True
        return False

    def record_failed_attempt(self, email=None):
        for key in self.get_attempt_keys(email=email):
            attempts = cache.get(key, 0) + 1
            cache.set(key, attempts, timeout=self.lockout_timeout_seconds)
            if attempts >= self.max_attempts:
                return True
        return False

    def clear_attempts(self, email=None):
        for key in self.get_attempt_keys(email=email):
            cache.delete(key)

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            email = (request.POST.get("email") or "").strip().lower()
            if self.is_rate_limited(email=email):
                return HttpResponse(
                    "Too many registration attempts. Please wait 15 minutes before trying again.",
                    status=429,
                )
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        email = (form.data.get("email") or "").strip().lower()
        self.record_failed_attempt(email=email)
        return super().form_invalid(form)

    def form_valid(self, form):
        email = form.cleaned_data["email"].strip().lower()
        self.clear_attempts(email=email)
        user = form.save()
        send_verification_email.delay(user.id)
        return super().form_valid(form)


class VerifyEmailSentView(TemplateView):
    template_name = "accounts/verify_email_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get("resend") == "1":
            context["resent"] = True
        return context


class VerifyEmailView(TemplateView):
    template_name = "accounts/email_verified.html"

    def get(self, request, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(kwargs["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "This verification link is invalid.")
            return redirect("accounts:login")

        token = kwargs["token"]
        if not email_verification_token.check_token(user, token):
            messages.error(request, "This verification link has expired or is invalid.")
            return redirect("accounts:login")

        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])

        verification = EmailVerification.objects.filter(user=user).first()
        if verification:
            verification.verified_at = timezone.now()
            verification.save(update_fields=["verified_at"])

        messages.success(request, "Your email has been verified. You can now log in.")
        return redirect("accounts:email-verified")


class EmailVerifiedView(TemplateView):
    template_name = "accounts/email_verified.html"


class CustomLoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    max_failed_attempts = 5
    lockout_timeout_seconds = 15 * 60

    def get_client_ip(self):
        forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR", "unknown")

    def get_attempt_keys(self, username):
        normalized_username = (username or "").strip().lower()
        client_ip = self.get_client_ip()
        keys = [
            f"login:ip:{client_ip}",
            f"login:user:{normalized_username or 'unknown'}",
        ]
        return keys

    def reset_attempts(self, username):
        for key in self.get_attempt_keys(username):
            cache.delete(key)

    def is_rate_limited(self, username):
        for key in self.get_attempt_keys(username):
            if cache.get(key, 0) >= self.max_failed_attempts:
                return True
        return False

    def record_failed_attempt(self, username):
        for key in self.get_attempt_keys(username):
            attempts = cache.get(key, 0) + 1
            cache.set(key, attempts, timeout=self.lockout_timeout_seconds)
            if attempts >= self.max_failed_attempts:
                return True
        return False

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            username = (request.POST.get("username") or "").strip().lower()
            if self.is_rate_limited(username):
                return HttpResponse(
                    "Too many failed login attempts. Please wait 15 minutes before trying again.",
                    status=429,
                )
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        username = (form.data.get("username") or "").strip().lower()
        if self.record_failed_attempt(username):
            return HttpResponse(
                "Too many failed login attempts. Please wait 15 minutes before trying again.",
                status=429,
            )
        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.get_user()
        self.reset_attempts(user.email)
        if not user.is_active:
            messages.error(self.request, "No user registered with this email.")
            return redirect("accounts:login")
        return super().form_valid(form)


class ResendVerificationView(FormView):
    form_class = ResendVerificationForm
    template_name = "accounts/verify_email_sent.html"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = User.objects.get(email=email)
        verification, _ = EmailVerification.objects.get_or_create(user=user)
        verification.last_sent_at = timezone.now()
        verification.save(update_fields=["last_sent_at"])
        send_verification_email.delay(user.id)
        messages.success(self.request, "A new verification email has been sent.")
        return redirect("accounts:verify-email-sent")

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, str(error))
        return redirect("accounts:login")