from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import BusinessOwner


@admin.register(BusinessOwner)
class BusinessOwnerAdmin(UserAdmin):
    list_display = [
        "email",
        "username",
        "firebase_uid",
        "phone",
        "country",
        "is_active",
        "is_staff",
        "created_at",
    ]
    search_fields = ["email", "username", "firebase_uid", "phone", "national_id"]
    ordering = ["-created_at"]
    fieldsets = UserAdmin.fieldsets + (
        (
            "Firebase",
            {"fields": ("firebase_uid",)},
        ),
        (
            "Business Profile",
            {"fields": ("phone", "national_id", "date_of_birth", "country")},
        ),
    )
