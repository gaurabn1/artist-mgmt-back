import datetime

import jwt
from django.conf import settings
from django.db import connection

from apps.core.models import User


def generate_jwt_token(user):
    # Access Token
    access_payload = {
        "user_id": str(user.uuid),
        "email": user.email,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + settings.JWT_EXPIRATION_DELTA,
        "iat": datetime.datetime.utcnow(),
    }
    access_token = jwt.encode(
        access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    # Refresh Token
    refresh_payload = {
        "user_id": str(user.uuid),
        "email": user.email,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + settings.JWT_EXPIRATION_REFRESH_DELTA,
        "iat": datetime.datetime.utcnow(),
    }
    refresh_token = jwt.encode(
        refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return access_token, refresh_token


def verify_jwt_token(token):
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
