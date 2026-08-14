from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "name", "is_staff", "is_active")
    search_fields = ("email", "name")
    ordering = ("email",)

    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("name", "auth_provider")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("name", "auth_provider")}),
    )
