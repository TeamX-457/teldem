from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("device", "severity", "metric", "message", "is_resolved", "created_at")
    list_filter = ("severity", "is_resolved", "metric")
    search_fields = ("device__name", "message")
    date_hierarchy = "created_at"
    actions = ["mark_resolved"]

    @admin.action(description="Mark selected alerts as resolved")
    def mark_resolved(self, request, queryset):
        for alert in queryset:
            alert.resolve()
