from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.alerts.models import Alert
from apps.billing.models import Subscription
from apps.devices.constants import DEVICE_TYPE_LABELS
from apps.devices.models import Device


@login_required
def home(request):
    user = request.user
    devices = Device.objects.filter_for_owner(user)
    alerts = Alert.objects.filter(device__in=devices).select_related("device")
    open_alerts = alerts.filter(is_resolved=False)

    organization = user.primary_organization
    subscription = None
    if organization:
        subscription = (
            Subscription.objects.filter(organization=organization)
            .select_related("plan")
            .first()
        )
    else:
        subscription = (
            Subscription.objects.filter(user=user).select_related("plan").first()
        )

    device_status_grid = [
        {
            "type": key,
            "label": label,
            "devices": devices.filter(device_type=key),
        }
        for key, label in DEVICE_TYPE_LABELS.items()
        if devices.filter(device_type=key).exists()
    ]

    team_activity = None
    if organization:
        team_activity = organization.memberships.select_related("user").order_by(
            "-joined_at"
        )[:8]

    context = {
        "devices": devices,
        "device_count": devices.count(),
        "online_count": devices.online().count(),
        "open_alerts": open_alerts[:8],
        "open_alert_count": open_alerts.count(),
        "recent_alerts": alerts[:8],
        "organization": organization,
        "subscription": subscription,
        "device_status_grid": device_status_grid,
        "team_activity": team_activity,
    }
    return render(request, "dashboard/home.html", context)
