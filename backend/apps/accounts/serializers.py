from django.contrib.auth import get_user_model
# pyrefly: ignore [missing-import]
from rest_framework import serializers


User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "phone",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate_old_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )

        return value

    def validate_new_password(self, value):
        user = self.context["request"].user

        if user.check_password(value):
            raise serializers.ValidationError(
                "New password must be different from the current password."
            )

        return value