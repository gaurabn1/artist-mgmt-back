from datetime import datetime

from rest_framework import serializers

from apps.core.models import UserProfile
from apps.core.utils import convert_tuples_to_dicts
from apps.users.serializers import UserSerializer


class UserProfileSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    gender = serializers.ChoiceField(choices=UserProfile.Gender.choices)
    address = serializers.CharField()
    dob = serializers.DateField()
    user = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate(self, attrs):
        dob = attrs.get("dob", "")
        current_date = datetime.now().date()
        email = attrs.get("user", {}).get("email", "")

        if email and UserProfile.objects.filter(user__email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")

        if dob and dob > current_date:
            raise serializers.ValidationError("Date of birth cannot be in the future.")

        return attrs


# class UserProfileSerializer(serializers.Serializer):
#     uuid = serializers.UUIDField(read_only=True)
#     first_name = serializers.CharField()
#     last_name = serializers.CharField()
#     phone = serializers.CharField()
#     gender = serializers.ChoiceField(choices=UserProfile.Gender.choices)
#     address = serializers.CharField()
#     dob = serializers.DateField()
#     is_active = serializers.BooleanField(required=False)
#     user_id = serializers.UUIDField(required=False)
#
#     def validate(self, attrs):
#         dob = attrs.get("dob", "")
#         current_date = datetime.now().date()
#
#         if dob and dob > current_date:
#             raise serializers.ValidationError("Date of birth cannot be in the future.")
#
#         return attrs

# def create(self, validated_data):
#     with connection.cursor() as c:
#         c.execute(
#             """
#             INSERT INTO profiles_userprofile
#             (first_name, last_name, phone, gender, address, dob, created_at, updated_at, user_id)
#             VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
#             RETURNING uuid, first_name, last_name, phone, gender, address, dob, user_id
#             """,
#             [
#                 validated_data.get("first_name", ""),
#                 validated_data.get("last_name", ""),
#                 validated_data.get("phone", ""),
#                 validated_data.get("gender", ""),
#                 validated_data.get("address", ""),
#                 validated_data.get("dob", ""),
#                 validated_data.get("user_id", None),
#             ],
#         )
#         manager = c.fetchone()
#     manager = convert_tuples_to_dicts(
#         manager,
#         [
#             "uuid",
#             "first_name",
#             "last_name",
#             "phone",
#             "gender",
#             "address",
#             "dob",
#             "user_id",
#         ],
#     )[0]
#     return manager
