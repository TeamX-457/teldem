from django.db import models
from django.utils import timezone

from apps.devices.models import Device


class Alert(models.Model):
    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="alerts")
    metric = models.CharField(max_length=50, blank=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    message = models.CharField(max_length=255)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["device", "metric", "is_resolved"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.device.name}: {self.message}"

    def resolve(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save(update_fields=["is_resolved", "resolved_at"])
