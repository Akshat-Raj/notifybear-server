from rest_framework import serializers
from .models import User, UserProfile
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError as DjangoValidationError


class UserProfileSerializer(serializers.ModelSerializer):
    dp_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["dp", "dp_url"]

    def get_dp_url(self, obj):
        if obj.dp and hasattr(obj.dp, 'url'):
            return obj.dp.url
        return None


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    initials = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "initials",
            "profile",
        ]

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password"]

    def validate_email(self, value):
        value = value.strip().lower()
        try:
            django_validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError([
                {"code": "email_invalid", "message": "Enter a valid email address."}
            ])

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError([
                {"code": "email_taken", "message": "Email is already in use."}
            ])
        return value

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError([
                {"code": "username_taken", "message": "Username is already taken."}
            ])
        return value

    def validate_password(self, value):
        errors = []

        if len(value) < 8:
            errors.append({"code": "password_too_short", "message": "Password must be at least 8 characters."})

        if not any(c.isdigit() for c in value):
            errors.append({"code": "password_no_digit", "message": "Password must contain at least one digit."})

        if not any(c.islower() for c in value):
            errors.append({"code": "password_no_lower", "message": "Password must contain at least one lowercase letter."})

        if not any(c.isupper() for c in value):
            errors.append({"code": "password_no_upper", "message": "Password must contain at least one uppercase letter."})

        if not any(not c.isalnum() for c in value):
            errors.append({"code":"password_no_special","message":"Password should contain a special character."})

        if errors:
            raise serializers.ValidationError(errors)

        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # create UserProfile automatically
        UserProfile.objects.get_or_create(user=user)

        return user
