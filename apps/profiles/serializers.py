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
