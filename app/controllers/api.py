import json

from flask import Blueprint, Response, request, stream_with_context
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Device, User
from app.services.ai_history_service import clear_history, get_history, save_exchange
from app.services.ai_service import AIServiceError, chat_with_deepseek, stream_chat_with_deepseek
from app.services.command_service import create_command
from app.services.config_service import get_system_configs, update_system_configs
from app.services.simulator_config_service import get_simulator_configs, update_simulator_configs
from app.services.snapshot_service import (
    build_dashboard_summary,
    get_active_alarms_payload,
    get_device_list_payload,
    get_history_payload,
    get_recent_commands_payload,
)
from app.utils.api import error_api, success_api


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/dashboard/summary")
@login_required
def dashboard_summary():
    return success_api(data=build_dashboard_summary())


@bp.route("/history/environment")
@login_required
def environment_history():
    metric = request.args.get("metric", "water_temperature")
    hours = request.args.get("hours", default=6, type=int)
    limit = request.args.get("limit", default=60, type=int)
    if hours < 1 or hours > 168:
        return error_api("参数错误", error="hours 必须在 1 到 168 之间。", status_code=400)
    if limit < 1 or limit > 500:
        return error_api("参数错误", error="limit 必须在 1 到 500 之间。", status_code=400)

    try:
        data = get_history_payload(metric, hours=hours, limit=limit)
    except ValueError as exc:
        return error_api("参数错误", error=str(exc), status_code=400)
    return success_api(data=data)


@bp.route("/alarms/active")
@login_required
def active_alarms():
    return success_api(data=get_active_alarms_payload())


@bp.route("/devices", methods=["GET", "POST"])
@login_required
def devices():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        try:
            device = _create_device(data)
        except ValueError as exc:
            return error_api("参数错误", error=str(exc), status_code=400)
        return success_api(msg="设备已创建", data=device.to_dict(), status_code=201)
    return success_api(data=get_device_list_payload())


@bp.route("/devices/<string:device_code>")
@login_required
def device_detail(device_code):
    device = Device.query.filter_by(code=device_code).first()
    if device is None:
        return error_api("未找到设备", error="设备不存在。", status_code=404)
    return success_api(data=device.to_dict())


@bp.route("/devices/<string:device_code>", methods=["PUT", "DELETE"])
@login_required
def update_or_delete_device(device_code):
    device = Device.query.filter_by(code=device_code).first()
    if device is None:
        return error_api("未找到设备", error="设备不存在。", status_code=404)

    if request.method == "DELETE":
        _delete_device(device)
        return success_api(msg="设备已删除")

    data = request.get_json(silent=True) or {}
    try:
        _update_device(device, data)
    except ValueError as exc:
        return error_api("参数错误", error=str(exc), status_code=400)
    return success_api(msg="设备已更新", data=device.to_dict())


@bp.route("/control/devices/<string:device_code>", methods=["POST"])
@login_required
def control_device(device_code):
    data = request.get_json(silent=True) or {}
    try:
        result = create_command(device_code, data.get("action"))
    except ValueError as exc:
        return error_api("参数错误", error=str(exc), status_code=400)
    except KeyError as exc:
        return error_api("未找到设备", error=str(exc), status_code=404)
    return success_api(msg="命令已受理", data=result)


@bp.route("/commands/recent")
@login_required
def recent_commands():
    limit = request.args.get("limit", default=10, type=int)
    return success_api(data=get_recent_commands_payload(limit=limit))


@bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        try:
            user = _create_user(data)
        except ValueError as exc:
            return error_api("参数错误", error=str(exc), status_code=400)
        return success_api(msg="用户已创建", data=_user_to_dict(user), status_code=201)
    return success_api(data=[_user_to_dict(user) for user in User.query.order_by(User.id.asc()).all()])


@bp.route("/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def user_detail(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return error_api("未找到用户", error="用户不存在。", status_code=404)

    if request.method == "GET":
        return success_api(data=_user_to_dict(user))
    if request.method == "DELETE":
        if user.id == current_user.id:
            return error_api("参数错误", error="不能删除当前登录用户。", status_code=400)
        from app.models import AIChatMessage

        AIChatMessage.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        return success_api(msg="用户已删除")

    data = request.get_json(silent=True) or {}
    try:
        _update_user(user, data)
    except ValueError as exc:
        return error_api("参数错误", error=str(exc), status_code=400)
    return success_api(msg="用户已更新", data=_user_to_dict(user))


@bp.route("/system/configs", methods=["GET", "PUT"])
@login_required
def system_configs():
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        return success_api(
            msg="系统配置已保存，部分配置需重启后生效。",
            data=update_system_configs(data),
        )
    return success_api(data=get_system_configs(masked=True))


@bp.route("/simulator/configs", methods=["GET", "PUT"])
@login_required
def simulator_configs():
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        try:
            result = update_simulator_configs(data.get("items", []))
        except ValueError as exc:
            return error_api("参数错误", error=str(exc), status_code=400)
        _restart_simulator()
        return success_api(msg="模拟器配置已保存并重启。", data=result)
    return success_api(data=get_simulator_configs())


@bp.route("/ai/chat", methods=["POST"])
@login_required
def ai_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    try:
        result = chat_with_deepseek(message)
    except AIServiceError as exc:
        return error_api("AI 对话失败", error=str(exc), status_code=400)
    save_exchange(current_user.id, message, result["reply"], result.get("model", ""))
    return success_api(msg="AI 回复成功", data=result)


@bp.route("/ai/chat/stream", methods=["POST"])
@login_required
def ai_chat_stream():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    user_id = current_user.id

    def sse_event(event, payload):
        packet = json.dumps(payload, ensure_ascii=False)
        return f"event: {event}\ndata: {packet}\n\n"

    @stream_with_context
    def generate():
        reply_parts = []
        model = ""
        try:
            chunks, meta = stream_chat_with_deepseek(message)
            model = meta.get("model", "")
            for chunk in chunks:
                reply_parts.append(chunk)
                yield sse_event("delta", {"content": chunk})

            reply = "".join(reply_parts).strip()
            if reply:
                save_exchange(user_id, message, reply, model)
            yield sse_event(
                "done",
                {
                    "model": model,
                    "context_devices_count": meta.get("context_devices_count", 0),
                    "saved": bool(reply),
                },
            )
        except AIServiceError as exc:
            yield sse_event("error", {"message": str(exc)})

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@bp.route("/ai/history", methods=["GET", "DELETE"])
@login_required
def ai_history():
    if request.method == "DELETE":
        clear_history(current_user.id)
        return success_api(msg="AI 聊天记录已清空")
    return success_api(data=get_history(current_user.id))


def _user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _validate_username(username, exclude_user_id=None):
    username = str(username or "").strip()
    if not username:
        raise ValueError("用户名不能为空。")
    query = User.query.filter_by(username=username)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    if query.first() is not None:
        raise ValueError("用户名已存在。")
    return username


def _create_user(data):
    username = _validate_username(data.get("username"))
    display_name = str(data.get("display_name", "")).strip()
    password = str(data.get("password", "")).strip()
    if not display_name:
        raise ValueError("显示名称不能为空。")
    if not password:
        raise ValueError("密码不能为空。")

    user = User(username=username, display_name=display_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def _update_user(user, data):
    username = _validate_username(data.get("username", user.username), exclude_user_id=user.id)
    display_name = str(data.get("display_name", "")).strip()
    password = str(data.get("password", "")).strip()
    if not display_name:
        raise ValueError("显示名称不能为空。")
    user.username = username
    user.display_name = display_name
    if password:
        user.set_password(password)
    db.session.commit()


def _normalize_device_payload(data, require_code=False):
    code = str(data.get("code", "")).strip()
    name = str(data.get("name", "")).strip()
    device_type = str(data.get("device_type", "")).strip()
    data_type = str(data.get("data_type", "switch")).strip().lower()
    unit = str(data.get("unit", "")).strip()
    description = str(data.get("description", "")).strip()
    threshold_min = data.get("threshold_min")
    threshold_max = data.get("threshold_max")

    if require_code and not code:
        raise ValueError("设备编号不能为空。")
    if not name:
        raise ValueError("设备名称不能为空。")
    if not device_type:
        raise ValueError("设备类型不能为空。")
    if data_type not in {"numeric", "switch"}:
        raise ValueError("设备数据类型只支持 numeric 或 switch。")
    if data_type == "switch":
        threshold_min = None
        threshold_max = None
    else:
        threshold_min = float(threshold_min) if threshold_min not in (None, "") else None
        threshold_max = float(threshold_max) if threshold_max not in (None, "") else None
        if threshold_min is not None and threshold_max is not None and threshold_min >= threshold_max:
            raise ValueError("最小阈值必须小于最大阈值。")

    return {
        "code": code,
        "name": name,
        "device_type": device_type,
        "data_type": data_type,
        "unit": unit,
        "threshold_min": threshold_min,
        "threshold_max": threshold_max,
        "description": description,
    }


def _create_device(data):
    values = _normalize_device_payload(data, require_code=True)
    if Device.query.filter_by(code=values["code"]).first() is not None:
        raise ValueError("设备编号已存在。")
    device = Device(**values)
    db.session.add(device)
    db.session.commit()
    _restart_simulator()
    return device


def _update_device(device, data):
    values = _normalize_device_payload(data)
    device.name = values["name"]
    device.device_type = values["device_type"]
    device.data_type = values["data_type"]
    device.unit = values["unit"]
    device.threshold_min = values["threshold_min"]
    device.threshold_max = values["threshold_max"]
    device.description = values["description"]
    db.session.commit()
    _restart_simulator()


def _delete_device(device):
    from app.models import AlarmRecord, CommandLog, DeviceReadingRecord, DeviceSimulatorConfig, DeviceStatusRecord

    AlarmRecord.query.filter_by(metric_key=f"device:{device.code}").delete()
    DeviceReadingRecord.query.filter_by(device_code=device.code).delete()
    DeviceSimulatorConfig.query.filter_by(device_code=device.code).delete()
    DeviceStatusRecord.query.filter_by(device_code=device.code).delete()
    CommandLog.query.filter_by(device_code=device.code).delete()
    db.session.delete(device)
    db.session.commit()
    _restart_simulator()


def _restart_simulator():
    from app.services.simulator_service import restart_simulator

    restart_simulator()
