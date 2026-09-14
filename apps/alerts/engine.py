"""Threshold-based alert engine.

Every simulated (or, eventually, real) sensor reading is passed through
`evaluate_reading`. If it crosses a threshold defined in
`apps.devices.constants.METRIC_CONFIG`, an Alert is raised - unless an
equivalent alert is already open, to avoid spamming the inbox.
"""

from django.core.mail import mail_admins
from django.utils import timezone

from apps.devices.constants import metrics_for

from .models import Alert

COOLDOWN_MINUTES = 30


def _has_recent_unresolved_alert(device, metric):
    return Alert.objects.filter(
        device=device, metric=metric, is_resolved=False
    ).exists()


def _gauge_breach(cfg, value):
    low, high = cfg["safe_range"]
    if value < low:
        return f"below the safe minimum ({value:.1f}{cfg['unit']} < {low:.1f}{cfg['unit']})"
    if value > high:
        return f"above the safe maximum ({value:.1f}{cfg['unit']} > {high:.1f}{cfg['unit']})"
    return None


def evaluate_reading(reading):
    """Inspect one SensorReading and raise an Alert if it breaches policy."""
    device = reading.device
    cfg = metrics_for(device.device_type).get(reading.metric)
    if not cfg:
        return None

    triggered = False
    detail = ""

    if cfg["kind"] == "gauge":
        breach = _gauge_breach(cfg, reading.value)
        if breach:
            triggered = True
            detail = f"{cfg['label']} is {breach}."
    elif cfg["kind"] == "binary":
        if cfg.get("armed_only") and not device.is_armed:
            triggered = False
        elif reading.value == cfg.get("alert_on"):
            triggered = True
            detail = f"{cfg['label']} triggered."

    if not triggered:
        return None

    if _has_recent_unresolved_alert(device, reading.metric):
        return None

    alert = Alert.objects.create(
        device=device,
        metric=reading.metric,
        severity=cfg.get("severity", Alert.Severity.WARNING),
        message=f"{device.name}: {detail}",
    )

    if alert.severity == Alert.Severity.CRITICAL:
        _notify_critical(alert)

    return alert


def _notify_critical(alert):
    """Stub notification hook - logs to console/admins via email backend."""
    try:
        mail_admins(
            subject=f"[TELDEM ALERT] {alert.device.name} - {alert.get_severity_display()}",
            message=(
                f"{alert.message}\n\nDevice: {alert.device.name}\n"
                f"Owner: {alert.device.owner_display}\n"
                f"Time: {timezone.localtime(alert.created_at):%Y-%m-%d %H:%M}\n"
            ),
            fail_silently=True,
        )
    except Exception:
        # Notification delivery must never break the simulation/ingest path.
        pass
