from rest_framework import serializers

from apps.core.models import User, UserProfile


class UserRegistrationSerializer(serializers.Serializer):
    # Fields required for user creation
    role = serializers.ChoiceField(choices=User.Role.choices)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    dob = serializers.DateField()
    gender = serializers.ChoiceField(choices=UserProfile.Gender.choices)
    address = serializers.CharField()
    is_active = serializers.BooleanField(required=False)

    # Artist-specific fields
    name = serializers.CharField(max_length=100, required=False)
    first_released_year = serializers.IntegerField(required=False, allow_null=True)
    no_of_album_released = serializers.IntegerField(
        required=False, allow_null=True, default=0
    )
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.ARTIST_MANAGER),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        email = attrs.get("email", "")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return attrs


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
