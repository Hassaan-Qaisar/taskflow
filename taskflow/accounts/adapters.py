from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import User


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        full_name = (
            data.get("name")
            or " ".join(
                part.strip()
                for part in [data.get("first_name"), data.get("last_name")]
                if part and part.strip()
            )
            or data.get("email", "").split("@")[0]
            or "Google User"
        ).strip()

        user.name = full_name
        user.auth_provider = User.AuthProvider.GOOGLE
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.set_unusable_password()
        user.save()
        return user