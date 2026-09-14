from django.contrib import admin

from .models import Device, SensorReading


class SensorReadingInline(admin.TabularInline):
    model = SensorReading
    extra = 0
    readonly_fields = ("metric", "value", "unit", "timestamp")
    ordering = ("-timestamp",)
    can_delete = False
    max_num = 0


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "device_type",
        "owner_display",
        "status",
        "is_armed",
        "active_alert_count",
        "install_date",
    )
    list_filter = ("device_type", "status", "is_armed")
    search_fields = ("name", "location_label", "pairing_code", "user__email", "organization__name")
    autocomplete_fields = ("user", "organization")
    readonly_fields = ("pairing_code", "created_at")
    inlines = [SensorReadingInline]


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ("device", "metric", "value", "unit", "timestamp")
    list_filter = ("metric",)
    search_fields = ("device__name",)
    date_hierarchy = "timestamp"
