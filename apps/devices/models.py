import random
import string

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .constants import DEVICE_TYPE_LABELS


def generate_pairing_code():
    alphabet = string.ascii_uppercase + string.digits
    return "-".join("".join(random.choices(alphabet, k=4)) for _ in range(2))


class DeviceQuerySet(models.QuerySet):
    def filter_for_owner(self, user):
        if not user.is_authenticated:
            return self.none()
        org_ids = user.memberships.values_list("organization_id", flat=True)
        return self.filter(Q(user=user) | Q(organization_id__in=org_ids))

    def online(self):
        return self.filter(status=Device.Status.ONLINE)


class Device(models.Model):
    class DeviceType(models.TextChoices):
        FRIDGE = "fridge", "Smart Fridge"
        GAS = "gas", "Smart Gas"
        VEHICLE = "vehicle", "Smart Vehicle"
        HOME_OFFICE = "home_office", "Smart Home / Office"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending activation"
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="devices",
        help_text="Set for individual (B2C) devices.",
    )
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="devices",
        help_text="Set for organization (B2B) devices.",
    )
    device_type = models.CharField(max_length=20, choices=DeviceType.choices)
    name = models.CharField(max_length=100)
    location_label = models.CharField(max_length=150, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    is_armed = models.BooleanField(
        default=False,
        help_text="Security-relevant devices (vehicle, home/office) can be armed.",
    )
    pairing_code = models.CharField(
        max_length=20, unique=True, default=generate_pairing_code
    )
    install_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = DeviceQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"

    @property
    def type_label(self):
        return DEVICE_TYPE_LABELS.get(self.device_type, self.device_type)

    @property
    def owner_display(self):
        if self.organization_id:
            return self.organization.name
        if self.user_id:
            return self.user.get_full_name() or self.user.username
        return "Unassigned"

    @property
    def is_security_capable(self):
        return self.device_type in (self.DeviceType.VEHICLE, self.DeviceType.HOME_OFFICE)

    def latest_reading_for(self, metric):
        return self.readings.filter(metric=metric).order_by("-timestamp").first()

    @property
    def active_alert_count(self):
        return self.alerts.filter(is_resolved=False).count()


class SensorReading(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="readings")
    metric = models.CharField(max_length=50)
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["device", "metric", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.device.name} · {self.metric}={self.value}{self.unit} @ {self.timestamp:%Y-%m-%d %H:%M}"
