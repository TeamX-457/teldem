from django.contrib import admin

from .models import Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name", "tier", "price_monthly", "price_device_from",
        "max_devices", "is_featured", "is_active", "order",
    )
    list_filter = ("tier", "is_active", "is_featured")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("owner_display", "plan", "status", "started_at", "current_period_end")
    list_filter = ("status", "plan")
    search_fields = ("user__email", "organization__name")
    autocomplete_fields = ("user", "organization", "plan")
