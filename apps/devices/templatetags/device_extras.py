from django import template

register = template.Library()

_ICON_MAP = {
    "fridge": "fridge",
    "gas": "gas",
    "vehicle": "vehicle",
    "home_office": "home",
}


@register.filter
def device_icon(device_type):
    return _ICON_MAP.get(device_type, "shield")
