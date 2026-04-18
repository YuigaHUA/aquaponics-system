import json
import os

from flask import current_app

from app.mqtt_compat import mqtt


_mqtt_client = None
_flask_app = None


def _is_reloader_parent_process():
    """中文注释：识别 Flask CLI 调试重载器的父进程，避免重复连接 MQTT。"""
    return (
        os.environ.get("FLASK_RUN_FROM_CLI") == "true"
        and os.environ.get("WERKZEUG_RUN_MAIN") != "true"
    )


def init_mqtt_client(app):
    """中文注释：初始化 MQTT 客户端并绑定回调。"""
    global _mqtt_client, _flask_app
    _flask_app = app
    app.extensions.setdefault("published_messages", [])

    if "mqtt_client" in app.extensions and app.extensions["mqtt_client"] is not None:
        return app.extensions["mqtt_client"]

    if _mqtt_client is not None:
        app.extensions["mqtt_client"] = _mqtt_client
        return _mqtt_client

    if app.config.get("TESTING") or not app.config.get("ENABLE_MQTT", True):
        app.logger.info("MQTT 已在测试模式或配置中关闭。")
        app.extensions["mqtt_client"] = None
        return None

    if _is_reloader_parent_process():
        app.logger.info("MQTT 已跳过调试重载器父进程初始化。")
        app.extensions["mqtt_client"] = None
        return None

    client = mqtt.Client(client_id=app.config["MQTT_CLIENT_ID"])
    if app.config["MQTT_USERNAME"]:
        client.username_pw_set(
            app.config["MQTT_USERNAME"],
            app.config["MQTT_PASSWORD"],
        )

    client.on_connect = _on_connect
    client.on_message = _on_message

    try:
        client.connect(
            app.config["MQTT_BROKER_HOST"],
            app.config["MQTT_BROKER_PORT"],
            app.config["MQTT_KEEPALIVE"],
        )
        client.loop_start()
        _mqtt_client = client
        app.extensions["mqtt_client"] = client
        return client
    except Exception as exc:  # pragma: no cover
        app.logger.warning("MQTT 初始化失败: %s", exc)
        app.extensions["mqtt_client"] = None
        return None


def _on_connect(client, userdata, flags, rc, properties=None):  # pragma: no cover
    if _flask_app is None:
        return
    topics = (
        _flask_app.config["MQTT_TOPIC_ENVIRONMENT"],
        _flask_app.config["MQTT_TOPIC_DEVICE"],
        _flask_app.config["MQTT_TOPIC_CONTROL_RESULT"],
    )
    for topic in topics:
        client.subscribe(topic)
    _flask_app.logger.info("MQTT 已连接并订阅主题，结果码: %s", rc)


def _on_message(client, userdata, message):  # pragma: no cover
    if _flask_app is None:
        return

    payload_text = message.payload.decode("utf-8")
    with _flask_app.app_context():
        handle_message(message.topic, payload_text)


def handle_message(topic, payload_text):
    """中文注释：按主题分发 MQTT 消息。"""
    from app.services.command_service import process_command_result_payload
    from app.services.device_service import process_device_payload
    from app.services.telemetry_service import process_environment_payload

    payload = json.loads(payload_text)
    if topic == current_app.config["MQTT_TOPIC_ENVIRONMENT"]:
        return process_environment_payload(payload)
    if topic == current_app.config["MQTT_TOPIC_DEVICE"]:
        return process_device_payload(payload)
    if topic == current_app.config["MQTT_TOPIC_CONTROL_RESULT"]:
        return process_command_result_payload(payload)
    return None


def publish_json(topic, payload):
    """中文注释：统一发布 JSON 消息，并记录到扩展中方便测试。"""
    packet = json.dumps(payload, ensure_ascii=False)
    current_app.extensions.setdefault("published_messages", []).append(
        {"topic": topic, "payload": payload}
    )

    client = current_app.extensions.get("mqtt_client") or _mqtt_client
    if client is None:
        current_app.logger.warning("MQTT 客户端不可用，消息仅记录不实际发送。")
        return False

    client.publish(topic, packet)
    return True


def publish_control_command(payload):
    return publish_json(current_app.config["MQTT_TOPIC_CONTROL"], payload)
