from flask import current_app

from app.extensions import db
from app.models import AlarmRecord, Device


def _build_threshold_text(metric_key):
    rule = current_app.config["ALERT_RULES"][metric_key]
    unit = current_app.config["METRIC_UNITS"].get(metric_key, "")
    if "min" in rule and "max" in rule:
        return f"{rule['min']}-{rule['max']} {unit}".strip()
    if "min" in rule:
        return f">= {rule['min']} {unit}".strip()
    return f"<= {rule['max']} {unit}".strip()


def _is_violation(metric_key, value):
    rule = current_app.config["ALERT_RULES"][metric_key]
    if "min" in rule and value < rule["min"]:
        return True
    if "max" in rule and value > rule["max"]:
        return True
    return False


def sync_alarms(metrics, reported_at):
    """中文注释：根据最新环境数据生成或恢复活动告警。"""
    active_alarms = {
        item.metric_key: item
        for item in AlarmRecord.query.filter_by(status="active").all()
    }

    for metric_key, label in current_app.config["METRIC_LABELS"].items():
        value = float(metrics[metric_key])
        threshold_text = _build_threshold_text(metric_key)
        unit = current_app.config["METRIC_UNITS"].get(metric_key, "")
        active_alarm = active_alarms.get(metric_key)

        if _is_violation(metric_key, value):
            message = (
                f"{label}超出阈值，当前值 {value:.2f}{unit}，"
                f"要求 {threshold_text}"
            )
            if active_alarm is None:
                db.session.add(
                    AlarmRecord(
                        metric_key=metric_key,
                        metric_label=label,
                        severity="danger",
                        message=message,
                        current_value=value,
                        threshold_text=threshold_text,
                        status="active",
                        triggered_at=reported_at,
                    )
                )
            else:
                active_alarm.message = message
                active_alarm.current_value = value
                active_alarm.threshold_text = threshold_text
        elif active_alarm is not None:
            active_alarm.status = "resolved"
            active_alarm.resolved_at = reported_at


def _device_threshold_text(device):
    unit = device.unit or ""
    if device.threshold_min is not None and device.threshold_max is not None:
        return f"{device.threshold_min}-{device.threshold_max} {unit}".strip()
    if device.threshold_min is not None:
        return f">= {device.threshold_min} {unit}".strip()
    if device.threshold_max is not None:
        return f"<= {device.threshold_max} {unit}".strip()
    return "未配置阈值"


def _is_device_violation(device, value):
    if device.threshold_min is not None and value < device.threshold_min:
        return True
    if device.threshold_max is not None and value > device.threshold_max:
        return True
    return False


def sync_device_alarm(device, value, reported_at):
    """中文注释：仅数值型设备根据自身阈值生成或恢复告警。"""
    if device.data_type != "numeric":
        return
    if device.threshold_min is None and device.threshold_max is None:
        return

    metric_key = f"device:{device.code}"
    active_alarm = AlarmRecord.query.filter_by(metric_key=metric_key, status="active").first()
    threshold_text = _device_threshold_text(device)
    unit = device.unit or ""
    if _is_device_violation(device, value):
        message = (
            f"{device.name}超出阈值，当前值 {value:.2f}{unit}，"
            f"要求 {threshold_text}"
        )
        if active_alarm is None:
            db.session.add(
                AlarmRecord(
                    metric_key=metric_key,
                    metric_label=device.name,
                    severity="danger",
                    message=message,
                    current_value=value,
                    threshold_text=threshold_text,
                    status="active",
                    triggered_at=reported_at,
                )
            )
        else:
            active_alarm.message = message
            active_alarm.current_value = value
            active_alarm.threshold_text = threshold_text
    elif active_alarm is not None:
        active_alarm.status = "resolved"
        active_alarm.resolved_at = reported_at


def resolve_device_alarm(device_code, reported_at):
    """中文注释：设备离线或删除时恢复该设备活动告警。"""
    metric_key = f"device:{device_code}"
    active_alarm = AlarmRecord.query.filter_by(metric_key=metric_key, status="active").first()
    if active_alarm is not None:
        active_alarm.status = "resolved"
        active_alarm.resolved_at = reported_at
