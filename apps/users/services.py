from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core import signing
from django.core.cache import cache
from django.db import connection, transaction
from django.utils.http import unquote
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from apps.core.models import User
from apps.core.utils import convert_tuples_to_dicts
from apps.users.serializers import UserLoginSerializer, UserRegistrationSerializer
from apps.users.utils import JWTManager, authenticate, send_follow_email


class UserService:

    def __init__(self, request, data):
        self.headers = request.headers
        self.data = data

    @staticmethod
    def create_user(data):
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            print(serializer.errors)
        serializer.is_valid(raise_exception=True)
        password = data.get("password", "")
        hashed_password = make_password(password)
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO core_user
                (email, password, role, is_active, created_at, updated_at, is_staff, is_superuser)
                VALUES (%s, %s, %s, True, NOW(), NOW(), FALSE, FALSE)
                RETURNING uuid, email, role
                """,
                [
                    data.get("email", ""),
                    hashed_password,
                    data.get("role", ""),
                ],
            )
            user = c.fetchone()
            user = convert_tuples_to_dicts(
                user,
                [
                    "uuid",
                    "email",
                    "role",
                    "is_active",
                ],
            )[0]

            if user.get("role", "") == "ARTIST":
                with connection.cursor() as c:
                    c.execute(
                        """
                        INSERT INTO artists_artist
                        (user_id, created_at, updated_at)
                        VALUES (%s, NOW(), NOW())
                        """,
                        [user["uuid"]],
                    )

            if user.get("role", "") == "ARTIST_MANAGER":
                with connection.cursor() as c:
                    c.execute(
                        """
                        INSERT INTO profiles_userprofile
                        (user_id, created_at, updated_at)
                        VALUES (%s, NOW(), NOW())
                        """,
                        [user["uuid"]],
                    )
            return user

    @staticmethod
    def register_user(data):
        with transaction.atomic():
            user = UserService.create_user(data)
            return {"user": user["email"]}

    def login_user(self):
        data = self.data
        serializer = UserLoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        email = data.get("email", None)
        password = data.get("password", None)

        user = authenticate(email=email, raw_password=password)
        if not user:
            raise APIException("Invalid credentials", status.HTTP_401_UNAUTHORIZED)
        else:
            jwt_manager = JWTManager(user)
            tokens = jwt_manager.generate_jwt_token()
            if tokens:
                access_token, refresh_token = tokens
                return Response(
                    {
                        "user": user.get("email"),
                        "role": user.get("role"),
                        "tokens": {
                            "access": access_token,
                            "refresh": refresh_token,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                raise APIException("Invalid credentials", status.HTTP_401_UNAUTHORIZED)

    def request_forget_password(self):
        email = self.data.get("email", None)
        user = User.objects.filter(email=email).first()
        token = signing.dumps(email)
        cache.set(f"reset_token_{token}", True, timeout=900)
        if user is None:
            raise APIException("User not found", status.HTTP_404_NOT_FOUND)
        try:
            send_follow_email(
                "Reset Password",
                f"Visit this link: http://127.0.0.1:3000/reset-password/{token} to reset your password",
                settings.EMAIL_HOST_USER,
                user.email,
            )
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            raise APIException(
                f"Failed to send email, Please check your email. {e}",
                status.HTTP_400_BAD_REQUEST,
            )

    def reset_password(self):
        password = self.data.get("password", None)
        token = self.data.get("token")
        if not token:
            raise APIException("Token is required", status.HTTP_400_BAD_REQUEST)
        decoded_token = unquote(token)
        try:
            email = signing.loads(decoded_token, max_age=36000)
        except signing.BadSignature:
            raise APIException(
                "Invalid token or token has expired", status.HTTP_400_BAD_REQUEST
            )
        if cache.get(f"reset_token_{token}") is None:
            raise APIException(
                "Token has already been used or expired", status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as c:
            c.execute(
                """
                UPDATE core_user
                SET password = %s, updated_at = NOW()
                WHERE email = %s
                RETURNING uuid
                """,
                [make_password(password), email],
            )
            user = c.fetchone()
            if user is None:
                raise APIException(
                    "Failed to update password", status.HTTP_400_BAD_REQUEST
                )

        cache.delete(f"reset_token_{token}")
        return Response(status=status.HTTP_200_OK)
