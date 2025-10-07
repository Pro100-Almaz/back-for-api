from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import authentication

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        # Custom validation logic, e.g., check if role matches expected
        # For now, just return the user; extend as needed
        return user
