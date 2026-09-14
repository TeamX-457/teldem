from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.devices.models import Device

from .models import Alert


@login_required
def alert_inbox(request):
    devices = Device.objects.filter_for_owner(request.user)
    alerts = Alert.objects.filter(device__in=devices).select_related("device")

    status = request.GET.get("status", "open")
    if status == "open":
        alerts = alerts.filter(is_resolved=False)
    elif status == "resolved":
        alerts = alerts.filter(is_resolved=True)

    severity = request.GET.get("severity")
    if severity:
        alerts = alerts.filter(severity=severity)

    return render(
        request,
        "alerts/alert_inbox.html",
        {
            "alerts": alerts,
            "status": status,
            "severity": severity,
            "open_count": Alert.objects.filter(device__in=devices, is_resolved=False).count(),
        },
    )


@login_required
def alert_resolve(request, pk):
    devices = Device.objects.filter_for_owner(request.user)
    alert = get_object_or_404(Alert, pk=pk, device__in=devices)
    if request.method == "POST":
        alert.resolve()
        messages.success(request, "Alert marked as resolved.")
    return redirect(request.META.get("HTTP_REFERER") or "alerts:inbox")
