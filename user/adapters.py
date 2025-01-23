from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If user exists, link the social account
        if sociallogin.is_existing:
            return

        # Create a new user if it doesn't exist
        user = sociallogin.user
        User = get_user_model()
        if not user.username:
            user.username = user.email.split('@')[0]

        # Ensure unique username
        counter = 1
        while User.objects.filter(username=user.username).exists():
            user.username = f"{user.username}_{counter}"
            counter += 1

        user.save()
