import datetime

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import connection

from apps.core.models import User
from apps.core.utils import convert_tuples_to_dicts


class JWTManager:
    def __init__(self, user=None, token=None):
        self.user = user
        self.token = token

    def generate_jwt_token(self, user):
        # Access Token
        access_payload = {
            "user_id": str(user.get("uuid", None)),
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
            "user_id": str(user.get("uuid", None)),
            "email": user.get("email", None),
            "role": user.get("role", None),
            "exp": datetime.datetime.utcnow() + settings.JWT_EXPIRATION_REFRESH_DELTA,
            "iat": datetime.datetime.utcnow(),
        }
        refresh_token = jwt.encode(
            refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return access_token, refresh_token

    def verify_jwt_token(self, token):
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            with connection.cursor() as cursor:
                query = "SELECT * FROM core_user WHERE uuid = %s"
                cursor.execute(query, [payload["user_id"]])
                user = cursor.fetchone()
                return user
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            return None


def authenticate(email, raw_password):
    with connection.cursor() as c:
        c.execute(
            """
            SELECT uuid, email, password, is_active FROM core_user
            WHERE email = %s 
            """,
            [email],
        )
        user = c.fetchone()
    user_dict = convert_tuples_to_dicts(
        user, ["uuid", "email", "password", "is_active"]
    )[0]
    if user is not None:
        stored_password = user_dict["password"]
        if check_password(raw_password, stored_password):
            return user_dict
    return None
