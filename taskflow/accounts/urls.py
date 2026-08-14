from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    CustomLoginView,
    EmailVerifiedView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailSentView,
    VerifyEmailView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("verify-email-sent/", VerifyEmailSentView.as_view(), name="verify-email-sent"),
    path("verify-email/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify-email"),
    path("email-verified/", EmailVerifiedView.as_view(), name="email-verified"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
]