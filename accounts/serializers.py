from rest_framework import serializers

from accounts.models import BusinessOwner


class BusinessOwnerSerializer(serializers.ModelSerializer):
    """
    Read serializer — returned by GET /api/auth/me/.
    Email is controlled by Firebase and is kept in sync automatically,
    so it is exposed as read-only here.
    """

    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = BusinessOwner
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "national_id",
            "date_of_birth",
            "country",
            "age",
            "created_at",
        ]
        read_only_fields = ["id", "email", "age", "created_at"]


class BusinessOwnerUpdateSerializer(serializers.ModelSerializer):
    """
    Write serializer — used for PATCH /api/auth/me/.
    Allows the owner to fill in business-profile fields after their first login.
    """

    class Meta:
        model = BusinessOwner
        fields = [
            "first_name",
            "last_name",
            "phone",
            "national_id",
            "date_of_birth",
            "country",
        ]
