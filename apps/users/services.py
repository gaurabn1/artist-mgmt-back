from django.contrib.auth.hashers import make_password
from django.db import connection, transaction
from rest_framework import status
from rest_framework.response import Response

from apps.artists.serializers import ArtistSerializer
from apps.artists.services import ArtistService
from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.serializers import UserProfileSerializer
from apps.users.serializers import UserLoginSerializer, UserRegistrationSerializer
from apps.users.utils import JWTManager, authenticate


class UserService:

    @staticmethod
    def create_user(data):
        serializer = UserRegistrationSerializer(data=data)
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

    @staticmethod
    def login_user(data):

        serializer = UserLoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        email = data.get("email", None)
        password = data.get("password", None)

        user = authenticate(email=email, raw_password=password)
        if not user:
            return user  # return message if not user
        else:
            jwt_manager = JWTManager(user)
            tokens = jwt_manager.generate_jwt_token()
            if tokens:
                access_token, refresh_token = tokens
                return Response(
                    {
                        "user": email,
                        "tokens": {
                            "access": access_token,
                            "refresh": refresh_token,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return None
