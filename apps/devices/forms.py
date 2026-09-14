from django import forms

from .models import Device


class DeviceRegistrationForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["device_type", "name", "location_label"]
        widgets = {
            "device_type": forms.RadioSelect,
        }

    def save(self, commit=True, owner=None):
        device = super().save(commit=False)
        if owner is not None:
            organization = owner.primary_organization
            if organization:
                device.organization = organization
            else:
                device.user = owner
        device.status = Device.Status.ONLINE
        if commit:
            device.save()
        return device


class DeviceUpdateForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["name", "location_label", "is_armed"]
