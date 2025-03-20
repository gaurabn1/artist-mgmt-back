from django.contrib.auth.hashers import make_password
from django.db import connection, transaction

from apps.artists.serializers import ArtistSerializer
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
                VALUES (%s, %s, %s, %s, NOW(), NOW(), FALSE, FALSE)
                RETURNING uuid, email, password, role, is_active
                """,
                [
                    data.get("email", ""),
                    hashed_password,
                    data.get("role", ""),
                    data.get("is_active", False),
                ],
            )
            user = c.fetchone()
            user = convert_tuples_to_dicts(
                user,
                [
                    "uuid",
                    "email",
                    "password",
                    "role",
                    "is_active",
                ],
            )[0]
            return user

    @staticmethod
    def register_user(data):
        with transaction.atomic():
            serializer = UserRegistrationSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            user = UserService.create_user(data)

            role = data.get("role", "ARTIST")

            artist_serializer = None
            manager_serializer = None

            if role == "ARTIST":
                artist_serializer = ArtistSerializer(
                    data={
                        "user_id": user.get("uuid", None),
                        "name": data.get("name", ""),
                        "first_released_year": data.get("first_released_year", None),
                        "no_of_album_released": data.get("no_of_album_released", 0),
                        "gender": data.get("gender", ""),
                        "address": data.get("address", ""),
                        "dob": data.get("dob", None),
                        "manager": data.get("manager", None),
                    }
                )
                artist_serializer.is_valid(raise_exception=True)

            elif role == "ARTIST_MANAGER":
                manager_serializer = UserProfileSerializer(
                    data={
                        "user_id": user.get("uuid", None),
                        "first_name": data.get("first_name", ""),
                        "last_name": data.get("last_name", ""),
                        "phone": data.get("phone", ""),
                        "gender": data.get("gender", ""),
                        "address": data.get("address", ""),
                        "dob": data.get("dob", None),
                    }
                )
                manager_serializer.is_valid(raise_exception=True)

            if role == "ARTIST" and artist_serializer:
                artist_serializer.save()
                return {
                    "user": user.get("email", None),
                    "is_active": user.get("is_active", False),
                    "artist": artist_serializer.data,
                }

            elif role == "ARTIST_MANAGER" and manager_serializer:
                manager_serializer.save()
                return {
                    "user": user.get("email", None),
                    "is_active": user.get("is_active", False),
                    "manager": manager_serializer.data,
                }

            return {"user": user.email}

    @staticmethod
    def login_user(data):

        serializer = UserLoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        email = data.get("email", None)
        password = data.get("password", None)

        user = authenticate(email=email, raw_password=password)
        jwt_manager = JWTManager(user)
        if user is not None and user.get("is_active", False):
            access_token, refresh_token = jwt_manager.generate_jwt_token(user)
            return {
                "user": email,
                "tokens": {
                    "access": access_token,
                    "refresh": refresh_token,
                },
            }
        else:
            return None
