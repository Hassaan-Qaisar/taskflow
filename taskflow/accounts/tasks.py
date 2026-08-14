from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User
from .tokens import email_verification_token


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    if user.is_active:
        return

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    base_url = settings.FRONTEND_BASE_URL.rstrip("/")
    verify_url = f"{base_url}/accounts/verify-email/{uidb64}/{token}/"

    subject = "Verify your email address"
    context = {"user": user, "verify_url": verify_url}
    html_content = render_to_string("accounts/verification_email.html", context)
    text_content = render_to_string("accounts/verification_email_plain.txt", context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
    return "email sent"
