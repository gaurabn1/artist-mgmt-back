from django.contrib.auth import authenticate
from django.db import transaction

from apps.artists.serializers import ArtistSerializer
from apps.profiles.serializers import UserProfileSerializer
from apps.users.serializers import UserLoginSerializer, UserRegistrationSerializer
from apps.users.utils import generate_jwt_token


class UserService:
    @staticmethod
    def register_user(data):
        with transaction.atomic():
            serializer = UserRegistrationSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

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
                artist_serializer.save(user=user)
                return {
                    "user": user.get("email", None),
                    "is_active": user.get("is_active", False),
                    "artist": artist_serializer.data,
                }

            elif role == "ARTIST_MANAGER" and manager_serializer:
                manager_serializer.save(user=user)
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

        user = authenticate(email=email, password=password)
        if user is not None and user.is_active:
            access_token, refresh_token = generate_jwt_token(user)
            return {
                "user": email,
                "tokens": {
                    "access": access_token,
                    "refresh": refresh_token,
                },
            }
        else:
            return None
