from app import socketio
from app.extensions import db
from app.models import Device, DeviceReadingRecord, DeviceStatusRecord
from app.services.alarm_service import resolve_device_alarm, sync_device_alarm
from app.services.snapshot_service import build_dashboard_summary
from app.services.time_service import parse_datetime


def process_device_payload(payload):
    """中文注释：处理设备快照 MQTT 上报并广播最新设备状态。"""
    items = payload.get("devices") or []
    if not isinstance(items, list):
        raise ValueError("设备快照格式错误。")

    reported_at = parse_datetime(payload.get("reported_at"))
    changed_devices = []
    existing_devices = {item.code: item for item in Device.query.all()}

    for item in items:
        code = str(item.get("code", "")).strip()
        if not code:
            continue

        device = existing_devices.get(code)
        if device is None:
            device = Device(
                code=code,
                name=item.get("name", code),
                device_type=item.get("type", "unknown"),
                description=item.get("description", ""),
            )
            db.session.add(device)
            existing_devices[code] = device

        device.name = item.get("name", device.name)
        device.device_type = item.get("type", device.device_type)
        device.data_type = item.get("data_type", device.data_type or "switch")
        device.unit = item.get("unit", device.unit)
        device.description = item.get("description", device.description)
        device.online = bool(item.get("online", False))
        switch_value = str(item.get("switch_value", item.get("power_state", "off"))).lower()
        numeric_value = item.get("numeric_value", item.get("value"))
        if device.data_type == "switch":
            device.power_state = "on" if device.online and switch_value == "on" else "off"
        else:
            device.power_state = "on" if device.online else "off"
        device.last_reported_at = reported_at

        reading = DeviceReadingRecord(
            device_code=device.code,
            device_name=device.name,
            data_type=device.data_type,
            numeric_value=float(numeric_value) if device.data_type == "numeric" and numeric_value is not None else None,
            switch_value=switch_value if device.data_type == "switch" else None,
            online=device.online,
            reported_at=reported_at,
        )
        db.session.add(reading)
        if not device.online:
            resolve_device_alarm(device.code, reported_at)
        elif device.data_type == "numeric" and reading.numeric_value is not None:
            sync_device_alarm(device, reading.numeric_value, reported_at)

        db.session.add(
            DeviceStatusRecord(
                device_code=device.code,
                device_name=device.name,
                device_type=device.device_type,
                online=device.online,
                power_state=device.power_state,
                reported_at=reported_at,
            )
        )
        changed_devices.append(device.to_dict())

    db.session.commit()

    socketio.emit(
        "device_status_changed",
        {
            "generated_at": reported_at.isoformat(),
            "items": changed_devices,
        },
    )
    socketio.emit("dashboard_snapshot", build_dashboard_summary())
    return changed_devices
