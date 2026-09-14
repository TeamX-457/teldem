"""Shared metric configuration for every TELDEM device type.

This single source of truth is used by:
- the `simulate_readings` management command (what to generate),
- the alert engine (what thresholds trip an alert),
- and the device detail templates (what to chart).
"""

GAUGE = "gauge"
BINARY = "binary"
LOCATION = "location"

METRIC_CONFIG = {
    "fridge": {
        "temperature": {
            "label": "Temperature",
            "unit": "°C",
            "kind": GAUGE,
            "safe_range": (1.0, 5.0),
            "normal_range": (2.0, 4.0),
            "severity": "critical",
        },
        "door_open": {
            "label": "Door",
            "unit": "state",
            "kind": BINARY,
            "alert_on": 1,
            "severity": "warning",
        },
        "stock_level": {
            "label": "Stock level",
            "unit": "%",
            "kind": GAUGE,
            "safe_range": (15.0, 100.0),
            "normal_range": (40.0, 95.0),
            "severity": "warning",
        },
    },
    "gas": {
        "level_percent": {
            "label": "Gas level",
            "unit": "%",
            "kind": GAUGE,
            "safe_range": (15.0, 100.0),
            "normal_range": (30.0, 95.0),
            "severity": "critical",
        },
    },
    "vehicle": {
        "motion_detected": {
            "label": "Motion",
            "unit": "state",
            "kind": BINARY,
            "alert_on": 1,
            "armed_only": True,
            "severity": "critical",
        },
        "impact_detected": {
            "label": "Impact",
            "unit": "state",
            "kind": BINARY,
            "alert_on": 1,
            "severity": "critical",
        },
        "location_ping": {
            "label": "Location",
            "unit": "coords",
            "kind": LOCATION,
        },
    },
    "home_office": {
        "motion": {
            "label": "Motion",
            "unit": "state",
            "kind": BINARY,
            "alert_on": 1,
            "armed_only": True,
            "severity": "warning",
        },
        "smoke": {
            "label": "Smoke",
            "unit": "state",
            "kind": BINARY,
            "alert_on": 1,
            "severity": "critical",
        },
        "door_open": {
            "label": "Door",
            "unit": "state",
            "kind": BINARY,
            "alert_on": 1,
            "armed_only": True,
            "severity": "warning",
        },
    },
}

DEVICE_TYPE_LABELS = {
    "fridge": "Smart Fridge",
    "gas": "Smart Gas",
    "vehicle": "Smart Vehicle",
    "home_office": "Smart Home / Office",
}


def metrics_for(device_type):
    return METRIC_CONFIG.get(device_type, {})


def chartable_metrics(device_type):
    return {
        key: cfg
        for key, cfg in metrics_for(device_type).items()
        if cfg["kind"] in (GAUGE, BINARY)
    }
