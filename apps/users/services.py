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
            validated_data = serializer.validated_data

            role = validated_data.get("role", "ARTIST")

            artist_serializer = None
            manager_serializer = None

            if role == "ARTIST":
                artist_serializer = ArtistSerializer(
                    data={
                        "name": validated_data.get("name", ""),
                        "first_released_year": validated_data.get(
                            "first_released_year", None
                        ),
                        "no_of_album_released": validated_data.get(
                            "no_of_album_released", None
                        ),
                        "gender": validated_data.get("gender", ""),
                        "address": validated_data.get("address", ""),
                        "dob": validated_data.get("dob", None),
                        "manager": validated_data.get("manager", None),
                    }
                )
                artist_serializer.is_valid(raise_exception=True)

            elif role == "ARTIST_MANAGER":
                manager_serializer = UserProfileSerializer(
                    data={
                        "first_name": validated_data.get("first_name", ""),
                        "last_name": validated_data.get("last_name", ""),
                        "phone": validated_data.get("phone", ""),
                        "gender": validated_data.get("gender", ""),
                        "address": validated_data.get("address", ""),
                        "dob": validated_data.get("dob", None),
                    }
                )
                manager_serializer.is_valid(raise_exception=True)

            user = serializer.save()

            if role == "ARTIST" and artist_serializer:
                artist_serializer.save(user=user)
                return {
                    "user": user.email,
                    "is_active": user.is_active,
                    "artist": artist_serializer.data,
                }

            elif role == "ARTIST_MANAGER" and manager_serializer:
                manager_serializer.save(user=user)
                return {
                    "user": user.email,
                    "is_active": user.is_active,
                    "manager": manager_serializer.data,
                }

            return {"user": user.email}

    @staticmethod
    def login_user(data):
        serializer = UserLoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data.get("email", None)
        password = validated_data.get("password", None)

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
