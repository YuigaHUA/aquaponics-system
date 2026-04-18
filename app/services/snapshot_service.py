from datetime import timedelta

from flask import current_app

from app.models import AlarmRecord, CommandLog, Device, DeviceReadingRecord, TelemetryRecord
from app.services.time_service import now_local


def _format_metric_value(metric_key, value):
    unit = current_app.config["METRIC_UNITS"].get(metric_key, "")
    if value is None:
        return "--"
    if metric_key == "ph":
        number = f"{value:.2f}"
    else:
        number = f"{value:.1f}"
    return f"{number} {unit}".strip()


def _format_device_value(device, reading):
    if reading is None:
        return "--"
    if not reading.online:
        return "离线"
    if device.data_type == "switch":
        return "开启" if reading.switch_value == "on" else "关闭"
    if reading.numeric_value is None:
        return "--"
    return f"{reading.numeric_value:.2f} {device.unit or ''}".strip()


def get_latest_telemetry_record():
    return TelemetryRecord.query.order_by(TelemetryRecord.reported_at.desc()).first()


def get_latest_telemetry_payload():
    record = get_latest_telemetry_record()
    return record.to_dict() if record else None


def get_metric_cards():
    latest = get_latest_telemetry_payload() or {}
    active_alarm_keys = {
        item.metric_key
        for item in AlarmRecord.query.filter_by(status="active").all()
    }
    cards = []
    for metric_key, label in current_app.config["METRIC_LABELS"].items():
        cards.append(
            {
                "key": metric_key,
                "label": label,
                "value": latest.get(metric_key),
                "display_value": _format_metric_value(metric_key, latest.get(metric_key)),
                "severity": "danger" if metric_key in active_alarm_keys else "success",
            }
        )
    return cards


def get_device_reading_cards():
    active_alarm_keys = {
        item.metric_key
        for item in AlarmRecord.query.filter_by(status="active").all()
    }
    cards = []
    for device in Device.query.order_by(Device.name.asc()).all():
        reading = (
            DeviceReadingRecord.query.filter_by(device_code=device.code)
            .order_by(DeviceReadingRecord.reported_at.desc())
            .first()
        )
        cards.append(
            {
                "key": f"device:{device.code}",
                "label": device.name,
                "value": reading.numeric_value if reading and device.data_type == "numeric" else None,
                "display_value": _format_device_value(device, reading),
                "severity": "danger" if f"device:{device.code}" in active_alarm_keys else "success",
                "data_type": device.data_type,
                "online": bool(reading.online) if reading else bool(device.online),
                "reported_at": reading.reported_at.isoformat() if reading else None,
            }
        )
    return cards


def get_device_list_payload():
    return [device.to_dict() for device in Device.query.order_by(Device.name.asc()).all()]


def get_active_alarms_payload():
    return [
        item.to_dict()
        for item in AlarmRecord.query.filter_by(status="active")
        .order_by(AlarmRecord.triggered_at.desc())
        .all()
    ]


def get_recent_commands_payload(limit=10):
    return [
        item.to_dict()
        for item in CommandLog.query.order_by(CommandLog.issued_at.desc()).limit(limit).all()
    ]


def get_history_payload(metric, hours=6, limit=60):
    metric_labels = current_app.config["METRIC_LABELS"]
    if metric.startswith("device:"):
        device_code = metric.split(":", 1)[1]
        device = Device.query.filter_by(code=device_code, data_type="numeric").first()
        if device is None:
            raise ValueError("不支持的指标。")
        cutoff = now_local() - timedelta(hours=hours)
        records = (
            DeviceReadingRecord.query.filter(
                DeviceReadingRecord.device_code == device_code,
                DeviceReadingRecord.reported_at >= cutoff,
                DeviceReadingRecord.numeric_value.isnot(None),
            )
            .order_by(DeviceReadingRecord.reported_at.desc())
            .limit(limit)
            .all()
        )
        records.reverse()
        return {
            "metric": metric,
            "label": device.name,
            "unit": device.unit or "",
            "items": [
                {
                    "reported_at": record.reported_at.isoformat(),
                    "value": record.numeric_value,
                }
                for record in records
            ],
        }

    if metric not in metric_labels:
        raise ValueError("不支持的指标。")

    cutoff = now_local() - timedelta(hours=hours)
    records = (
        TelemetryRecord.query.filter(TelemetryRecord.reported_at >= cutoff)
        .order_by(TelemetryRecord.reported_at.desc())
        .limit(limit)
        .all()
    )
    records.reverse()
    return {
        "metric": metric,
        "label": metric_labels[metric],
        "unit": current_app.config["METRIC_UNITS"].get(metric, ""),
        "items": [
            {
                "reported_at": record.reported_at.isoformat(),
                "value": getattr(record, metric),
            }
            for record in records
        ],
    }


def build_dashboard_summary():
    latest = get_latest_telemetry_payload()
    devices = get_device_list_payload()
    alarms = get_active_alarms_payload()
    commands = get_recent_commands_payload(limit=8)
    online_count = sum(1 for item in devices if item["online"])
    return {
        "generated_at": now_local().isoformat(),
        "latest_telemetry": latest,
        "metric_cards": get_metric_cards(),
        "device_reading_cards": get_device_reading_cards(),
        "dashboard_cards": get_device_reading_cards(),
        "devices": devices,
        "active_alarms": alarms,
        "recent_commands": commands,
        "device_totals": {
            "total": len(devices),
            "online": online_count,
            "alarms": len(alarms),
        },
    }
