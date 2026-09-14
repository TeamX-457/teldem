import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .constants import chartable_metrics, metrics_for
from .forms import DeviceRegistrationForm, DeviceUpdateForm
from .models import Device


def _get_owned_device_or_404(user, pk):
    device = get_object_or_404(Device.objects.filter_for_owner(user), pk=pk)
    return device


@login_required
def device_list(request):
    devices = Device.objects.filter_for_owner(request.user)
    return render(request, "devices/device_list.html", {"devices": devices})


@login_required
def device_register(request):
    if request.method == "POST":
        form = DeviceRegistrationForm(request.POST)
        if form.is_valid():
            device = form.save(owner=request.user)
            messages.success(
                request,
                f"{device.name} paired successfully with code {device.pairing_code}.",
            )
            return redirect("devices:detail", pk=device.pk)
    else:
        form = DeviceRegistrationForm()

    return render(request, "devices/device_register.html", {"form": form})


@login_required
def device_detail(request, pk):
    device = _get_owned_device_or_404(request.user, pk)
    metrics = metrics_for(device.device_type)

    latest_readings = {
        metric: device.latest_reading_for(metric) for metric in metrics
    }

    chart_data = {}
    for metric, cfg in chartable_metrics(device.device_type).items():
        readings = list(
            device.readings.filter(metric=metric).order_by("timestamp")[:200]
        )
        chart_data[metric] = {
            "label": cfg["label"],
            "unit": cfg["unit"],
            "kind": cfg["kind"],
            "points": [
                {"t": r.timestamp.isoformat(), "v": r.value} for r in readings
            ],
        }

    alerts = device.alerts.order_by("-created_at")[:10]

    return render(
        request,
        "devices/device_detail.html",
        {
            "device": device,
            "metrics": metrics,
            "latest_readings": latest_readings,
            "chart_data_json": json.dumps(chart_data),
            "alerts": alerts,
        },
    )


@login_required
def device_update(request, pk):
    device = _get_owned_device_or_404(request.user, pk)
    if request.method == "POST":
        form = DeviceUpdateForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, f"{device.name} updated.")
            return redirect("devices:detail", pk=device.pk)
    else:
        form = DeviceUpdateForm(instance=device)
    return render(
        request, "devices/device_update.html", {"form": form, "device": device}
    )


@login_required
def device_toggle_armed(request, pk):
    device = _get_owned_device_or_404(request.user, pk)
    if not device.is_security_capable:
        raise Http404("This device type cannot be armed.")
    if request.method == "POST":
        device.is_armed = not device.is_armed
        device.save(update_fields=["is_armed"])
        state = "armed" if device.is_armed else "disarmed"
        messages.success(request, f"{device.name} is now {state}.")
    return redirect("devices:detail", pk=device.pk)


@login_required
def device_delete(request, pk):
    device = _get_owned_device_or_404(request.user, pk)
    if request.method == "POST":
        name = device.name
        device.delete()
        messages.success(request, f"{name} was removed from your account.")
        return redirect("devices:list")
    return render(request, "devices/device_confirm_delete.html", {"device": device})
