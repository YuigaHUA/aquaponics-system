from uuid import uuid4

from app import socketio
from app.extensions import db
from app.models import CommandLog, Device
from app.services.mqtt_service import publish_control_command
from app.services.snapshot_service import build_dashboard_summary
from app.services.time_service import now_local, parse_datetime


def create_command(device_code, action):
    """中文注释：受理设备控制命令，并通过 MQTT 发布到模拟器。"""
    normalized_action = str(action).strip().lower()
    if normalized_action not in {"on", "off"}:
        raise ValueError("动作只支持 on 或 off。")

    device = Device.query.filter_by(code=device_code).first()
    if device is None:
        raise KeyError("设备不存在。")
    if device.data_type != "switch":
        raise ValueError("数值型设备不支持开关控制。")

    issued_at = now_local()
    command_id = uuid4().hex
    log = CommandLog(
        command_id=command_id,
        device_code=device_code,
        action=normalized_action,
        status="pending",
        source="web",
        message="命令已受理，等待设备回执。",
        issued_at=issued_at,
    )
    db.session.add(log)
    db.session.commit()

    published = publish_control_command(
        {
            "command_id": command_id,
            "device_code": device_code,
            "action": normalized_action,
            "issued_at": issued_at.isoformat(),
            "source": "web",
        }
    )
    if not published:
        log.status = "failed"
        log.message = "MQTT 客户端不可用，命令未发送。"
        log.acknowledged_at = issued_at
        db.session.commit()

    socketio.emit(
        "command_feedback",
        {
            "generated_at": issued_at.isoformat(),
            "command": log.to_dict(),
        },
    )
    socketio.emit("dashboard_snapshot", build_dashboard_summary())
    return {
        "command_id": command_id,
        "device_code": device_code,
        "action": normalized_action,
        "status": log.status,
        "message": log.message,
    }


def process_command_result_payload(payload):
    """中文注释：处理设备执行结果回执，并更新命令状态。"""
    command_id = str(payload.get("command_id", "")).strip()
    if not command_id:
        raise ValueError("缺少 command_id。")

    log = CommandLog.query.filter_by(command_id=command_id).first()
    if log is None:
        raise KeyError("命令不存在。")

    success = bool(payload.get("success", False))
    log.status = "success" if success else "failed"
    log.message = payload.get("message", "设备已返回执行结果。")
    log.acknowledged_at = parse_datetime(payload.get("reported_at"))
    if success:
        device = Device.query.filter_by(code=log.device_code).first()
        if device is not None:
            device.power_state = log.action
            device.online = True
            device.last_reported_at = log.acknowledged_at
    db.session.commit()

    socketio.emit(
        "command_feedback",
        {
            "generated_at": log.acknowledged_at.isoformat() if log.acknowledged_at else None,
            "command": log.to_dict(),
        },
    )
    socketio.emit("dashboard_snapshot", build_dashboard_summary())
    return log.to_dict()
