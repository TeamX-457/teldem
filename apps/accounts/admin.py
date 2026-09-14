from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Membership, Organization, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "account_type",
        "is_email_verified",
        "is_staff",
        "created_at",
    )
    list_filter = ("account_type", "is_staff", "is_active", "is_email_verified")
    search_fields = ("username", "email", "first_name", "last_name", "phone_number")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "TELDEM profile",
            {
                "fields": (
                    "account_type",
                    "phone_number",
                    "is_email_verified",
                    "has_completed_onboarding",
                )
            },
        ),
    )


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "member_count", "device_count", "created_at")
    list_filter = ("industry",)
    search_fields = ("name", "contact_email", "contact_phone")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("user__email", "user__username", "organization__name")
    autocomplete_fields = ("user", "organization")
