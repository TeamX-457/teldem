"""Generate one realistic sensor reading per metric for every active device.

This stands in for real hardware telemetry: it is what a physical TELDEM
device would be POSTing to an ingest endpoint. Run it on a schedule (cron,
Windows Task Scheduler, or `manage.py run_scheduler`) to keep the demo data
and alert feed alive.
"""

import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.alerts.engine import evaluate_reading
from apps.devices.constants import metrics_for
from apps.devices.models import Device, SensorReading


def _next_gauge_value(cfg, previous):
    low, high = cfg["normal_range"]
    if previous is None:
        value = random.uniform(low, high)
    else:
        # Random walk around the previous value, occasionally drifting
        # outside the safe range to give the alert engine something to do.
        drift = random.uniform(-0.06, 0.06) * (high - low)
        value = previous + drift
        if random.random() < 0.05:
            safe_low, safe_high = cfg["safe_range"]
            span = safe_high - safe_low
            value += random.choice([-1, 1]) * random.uniform(0.15, 0.35) * span

    if cfg["unit"] == "%":
        value = max(0.0, min(100.0, value))
    return round(value, 2)


def _next_binary_value(cfg):
    anomaly_chance = 0.08 if cfg.get("armed_only") else 0.05
    if cfg["label"] == "Smoke":
        anomaly_chance = 0.02
    return 1 if random.random() < anomaly_chance else 0


def _next_location():
    # Rough bounding box around Lagos, Nigeria for believable demo pings.
    lat = 6.4281 + random.uniform(-0.08, 0.08)
    lng = 3.4219 + random.uniform(-0.08, 0.08)
    return f"{lat:.5f},{lng:.5f}"


def generate_reading_value(device, metric, cfg):
    if cfg["kind"] == "gauge":
        previous = device.latest_reading_for(metric)
        return _next_gauge_value(cfg, previous.value if previous else None)
    if cfg["kind"] == "binary":
        return _next_binary_value(cfg)
    if cfg["kind"] == "location":
        return 0.0  # location is stored as text metadata below
    return 0.0


class Command(BaseCommand):
    help = "Simulate one round of sensor readings for every online device."

    def add_arguments(self, parser):
        parser.add_argument(
            "--device-id",
            type=int,
            default=None,
            help="Only simulate readings for a single device id.",
        )

    def handle(self, *args, **options):
        devices = Device.objects.filter(status=Device.Status.ONLINE)
        if options["device_id"]:
            devices = devices.filter(pk=options["device_id"])

        readings_created = 0
        alerts_created = 0
        now = timezone.now()

        for device in devices:
            for metric, cfg in metrics_for(device.device_type).items():
                if cfg["kind"] == "location":
                    coords = _next_location()
                    reading = SensorReading.objects.create(
                        device=device,
                        metric=metric,
                        value=0.0,
                        unit=coords,
                        timestamp=now,
                    )
                else:
                    value = generate_reading_value(device, metric, cfg)
                    reading = SensorReading.objects.create(
                        device=device,
                        metric=metric,
                        value=value,
                        unit=cfg["unit"],
                        timestamp=now,
                    )
                    if evaluate_reading(reading):
                        alerts_created += 1
                readings_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Simulated {readings_created} readings across {devices.count()} "
                f"devices, raising {alerts_created} new alert(s)."
            )
        )
