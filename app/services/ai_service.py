import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models import Device
from app.services.config_service import get_config_value


class AIServiceError(Exception):
    """中文注释：统一封装 AI 服务调用过程中的可展示错误。"""


def _device_value_text(device):
    reading = device.to_dict().get("latest_reading")
    if not reading:
        return "暂无数据"
    if not reading["online"]:
        return "离线"
    if device.data_type == "switch":
        return "开启" if reading.get("switch_value") == "on" else "关闭"
    value = reading.get("numeric_value")
    if value is None:
        return "暂无数据"
    return f"{value:.2f} {device.unit or ''}".strip()


def build_device_context():
    """中文注释：把当前设备和最新读数整理为 AI 可理解的短上下文。"""
    devices = Device.query.order_by(Device.name.asc()).all()
    lines = [f"当前系统共有 {len(devices)} 个设备。"]
    for device in devices:
        threshold = "无"
        if device.data_type == "numeric":
            if device.threshold_min is not None and device.threshold_max is not None:
                threshold = f"{device.threshold_min}-{device.threshold_max} {device.unit or ''}".strip()
            elif device.threshold_min is not None:
                threshold = f">= {device.threshold_min} {device.unit or ''}".strip()
            elif device.threshold_max is not None:
                threshold = f"<= {device.threshold_max} {device.unit or ''}".strip()

        latest = device.to_dict().get("latest_reading") or {}
        lines.append(
            "；".join(
                [
                    f"设备名称：{device.name}",
                    f"设备编号：{device.code}",
                    f"数据类型：{'数值型' if device.data_type == 'numeric' else '开关型'}",
                    f"在线状态：{'在线' if latest.get('online', device.online) else '离线'}",
                    f"当前值：{_device_value_text(device)}",
                    f"阈值：{threshold}",
                    f"最后上报：{latest.get('reported_at') or '暂无'}",
                ]
            )
        )
    return "\n".join(lines), len(devices)


def _build_api_url(base_url):
    base = (base_url or "https://api.deepseek.com").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _build_chat_request(message, stream=False):
    """中文注释：统一构造 DeepSeek 对话请求，供普通和流式接口复用。"""
    api_key = get_config_value("deepseek_api_key", "")
    if not api_key:
        raise AIServiceError("请先在系统配置中填写 DeepSeek API Key。")

    base_url = get_config_value("deepseek_base_url", "https://api.deepseek.com")
    model = get_config_value("deepseek_model", "deepseek-chat")
    device_context, device_count = build_device_context()
    user_message = str(message or "").strip()
    if not user_message:
        raise AIServiceError("请输入要咨询的问题。")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是鱼菜共生监控系统助手。请基于系统实时数据直接回答用户问题，"
                    "当用户询问适合养殖的鱼类、种植建议、运维建议或风险判断时，"
                    "可以结合鱼菜共生和水产养殖通用知识给出建议，并说明建议依据。"
                    "例如可根据水温、pH、溶解氧、空气温湿度等数据推荐罗非鱼、鲫鱼、锦鲤、鲤鱼、鲈鱼等候选品种，"
                    "同时给出需要继续确认的关键条件。"
                    "不要在回复中出现“根据当前设备上下文”“根据上下文”“基于上下文”等措辞，"
                    "不要编造设备、数值或状态。若缺少某些判断条件，请说明缺少哪些数据，"
                    "但不要因为缺少全部养殖资料就拒绝给出合理建议。"
                ),
            },
            {
                "role": "user",
                "content": f"系统实时数据：\n{device_context}\n\n用户问题：{user_message}",
            },
        ],
        "stream": bool(stream),
    }
    request = Request(
        _build_api_url(base_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    return request, model, device_count, user_message


def chat_with_deepseek(message):
    """中文注释：调用 DeepSeek 对话接口并返回回复和上下文信息。"""
    request, model, device_count, _user_message = _build_chat_request(message, stream=False)
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise AIServiceError(f"AI 服务请求失败，状态码 {exc.code}。{detail[:120]}") from exc
    except URLError as exc:
        raise AIServiceError(f"AI 服务连接失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise AIServiceError("AI 服务请求超时。") from exc
    except json.JSONDecodeError as exc:
        raise AIServiceError("AI 服务响应格式异常。") from exc

    try:
        reply = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIServiceError("AI 服务响应格式异常。") from exc

    return {
        "status": "ok",
        "reply": str(reply).strip(),
        "model": model,
        "context_devices_count": device_count,
    }


def stream_chat_with_deepseek(message):
    """中文注释：打开 DeepSeek 流式响应，逐段产出模型返回文本。"""
    request, model, device_count, _user_message = _build_chat_request(message, stream=True)
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise AIServiceError(f"AI 服务请求失败，状态码 {exc.code}。{detail[:120]}") from exc
    except URLError as exc:
        raise AIServiceError(f"AI 服务连接失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise AIServiceError("AI 服务请求超时。") from exc

    def generate_chunks():
        try:
            while True:
                line = response.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="ignore").strip()
                if not text or not text.startswith("data:"):
                    continue

                data = text[5:].strip()
                if data == "[DONE]":
                    break

                try:
                    payload = json.loads(data)
                    delta = payload["choices"][0].get("delta", {}).get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                    raise AIServiceError("AI 服务流式响应格式异常。") from exc
                if delta:
                    yield str(delta)
        finally:
            response.close()

    return generate_chunks(), {
        "model": model,
        "context_devices_count": device_count,
    }
