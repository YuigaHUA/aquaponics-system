from app import socketio
from app.extensions import db
from app.models import TelemetryRecord
from app.services.alarm_service import sync_alarms
from app.services.snapshot_service import build_dashboard_summary, get_active_alarms_payload
from app.services.time_service import parse_datetime


def process_environment_payload(payload):
    """中文注释：处理环境监测 MQTT 上报并广播最新摘要。"""
    metrics = payload.get("metrics") or {}
    required_keys = (
        "water_temperature",
        "ph",
        "dissolved_oxygen",
        "air_temperature",
        "air_humidity",
    )
    missing = [item for item in required_keys if item not in metrics]
    if missing:
        raise ValueError(f"缺少指标字段: {', '.join(missing)}")

    reported_at = parse_datetime(payload.get("reported_at"))
    record = TelemetryRecord(
        reported_at=reported_at,
        water_temperature=float(metrics["water_temperature"]),
        ph=float(metrics["ph"]),
        dissolved_oxygen=float(metrics["dissolved_oxygen"]),
        air_temperature=float(metrics["air_temperature"]),
        air_humidity=float(metrics["air_humidity"]),
    )
    db.session.add(record)
    sync_alarms(metrics, reported_at)
    db.session.commit()

    socketio.emit("dashboard_snapshot", build_dashboard_summary())
    socketio.emit(
        "alarm_changed",
        {
            "generated_at": reported_at.isoformat(),
            "items": get_active_alarms_payload(),
        },
    )
    return record.to_dict()
