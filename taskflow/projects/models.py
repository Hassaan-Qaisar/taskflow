from django.conf import settings
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectMembership",
        related_name="projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"      # optional, can skip for v1
        MEMBER = "member", "Member"

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")  # a user can't join twice

    def __str__(self):
        return f"{self.user} - {self.project} ({self.role})"