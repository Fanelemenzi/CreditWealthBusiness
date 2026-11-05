from rest_framework import serializers

from accounts.models import BusinessOwner


class BusinessOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessOwner
        fields = [
            "id",
            "phone",
            "username",
            "first_name",
            "last_name",
            "national_id",
            "date_of_birth",
            "country",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = BusinessOwner
        fields = [
            "phone",
            "username",
            "password",
            "first_name",
            "last_name",
            "national_id",
            "date_of_birth",
            "country",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        return BusinessOwner.objects.create_user(password=password, **validated_data)
