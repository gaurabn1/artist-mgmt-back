import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt.exceptions import DecodeError, ExpiredSignatureError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """Authenticate user based on JWT token"""
        token = self.get_token_from_request(request)
        if not token:
            return None

        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
        except ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except DecodeError:
            raise AuthenticationFailed("Invalid token")

        user = self.get_user_from_payload(payload)
        if user is None:
            raise AuthenticationFailed("Invalid token")

        return user, token

    def get_token_from_request(self, request):
        """Extract token from Authorization header"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        return auth_header.split(" ")[1]

    def get_user_from_payload(self, payload):
        """Fetch user from decoded JWT payload"""
        try:
            user = User.objects.get(uuid=payload["user_id"])
        except User.DoesNotExist:
            return None
        return user
