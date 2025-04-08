import datetime
import threading

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage
from django.db import connection

from apps.core.utils import convert_tuples_to_dicts


class JWTManager:
    def __init__(self, user=None, token=None):
        self.user = user
        self.token = token

    def generate_jwt_token(self):
        user = self.user
        if not user:
            return None
        # Access Token
        access_payload = {
            "user_id": str(user.get("uuid", None) or user.get("user_id", None)),
            "email": user.get("email", None),
            "role": user.get("role", None),
            "exp": datetime.datetime.utcnow() + settings.JWT_EXPIRATION_DELTA,
            "iat": datetime.datetime.utcnow(),
        }
        access_token = jwt.encode(
            access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        # Refresh Token
        refresh_payload = {
            "user_id": str(user.get("uuid", None) or user.get("user_id", None)),
            "email": user.get("email", None),
            "role": user.get("role", None),
            "exp": datetime.datetime.utcnow() + settings.JWT_EXPIRATION_REFRESH_DELTA,
            "iat": datetime.datetime.utcnow(),
        }
        refresh_token = jwt.encode(
            refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return access_token, refresh_token

    @staticmethod
    def verify_jwt_token(token):
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            with connection.cursor() as cursor:
                query = "SELECT uuid, role FROM core_user WHERE uuid = %s"
                cursor.execute(query, [payload["user_id"]])
                user = cursor.fetchone()
                if user is None:
                    return None
                user_dict = convert_tuples_to_dicts(user, ["uuid", "role"])[0]
                if user_dict["role"] != payload["role"]:
                    return None
                if user_dict["role"] == "ARTIST_MANAGER":
                    query = "SELECT uuid FROM artists_artist WHERE user_id = %s"
                    cursor.execute(query, [payload["user_id"]])
                    artist = cursor.fetchone()
                    if artist is None:
                        return None
                query = "SELECT uuid FROM profiles_userprofile WHERE user_id = %s"
                cursor.execute(query, [payload["user_id"]])
                manager = cursor.fetchone()
                if manager is None:
                    return None
                return True
        except (jwt.ExpiredSignatureError, jwt.DecodeError):
            return None

    @staticmethod
    def refresh_jwt_token(refresh_token):
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            jwt_manager = JWTManager(user=payload)
            return jwt_manager.generate_jwt_token()
        except (jwt.ExpiredSignatureError, jwt.DecodeError):
            return None

    @staticmethod
    def decode_jwt_token(token):
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except (jwt.ExpiredSignatureError, jwt.DecodeError):
            return None


def authenticate(email, raw_password):
    with connection.cursor() as c:
        c.execute(
            """
            SELECT uuid, email, password, is_active, role FROM core_user
            WHERE email = %s 
            """,
            [email],
        )
        user = c.fetchone()
        if user is None:
            return None
    user_dict = convert_tuples_to_dicts(
        user, ["uuid", "email", "password", "is_active", "role"]
    )[0]
    if not user_dict["is_active"]:
        return None
    if user is not None:
        stored_password = user_dict["password"]
        if check_password(raw_password, stored_password):
            return user_dict
    return None


def get_payload(headers):
    return JWTManager.decode_jwt_token(headers.get("Authorization", "").split(" ")[1])


def send_follow_email(subject, message, from_email, to_email):
    email = EmailMessage(subject, message, from_email, [to_email])

    def email_send():
        try:
            result = email.send()
            print("Email Sent.", result)
        except Exception as e:
            print(f"Failed to send email: {e}")

    email_thread = threading.Thread(target=email_send)
    email_thread.start()
