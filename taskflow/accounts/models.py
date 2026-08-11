from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class AuthProvider(models.TextChoices):
        EMAIL = "email", "Email"
        GOOGLE = "google", "Google"

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    auth_provider = models.CharField(
        max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]  # prompted for via createsuperuser; username handled separately

    def __str__(self):
        return self.name