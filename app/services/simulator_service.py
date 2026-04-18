import json
import random
import threading
import time

from app.mqtt_compat import mqtt
from app.models import Device, DeviceSimulatorConfig
from app.services.config_service import get_config_value
from app.services.simulator_config_service import ensure_simulator_configs
from app.services.time_service import now_local


_simulator_runtime = None
_runtime_lock = threading.Lock()


class EmbeddedSimulatorRuntime:
    """中文注释：在 Flask 进程内运行的 MQTT 数据模拟器。"""

    def __init__(self, app):
        self.app = app
        self.stop_event = threading.Event()
        self.thread = None
        self.client = None
        self.values = {}

    def start(self):
        self.thread = threading.Thread(target=self.run, name="aquaponics-simulator", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.client is not None:
            if hasattr(self.client, "loop_stop"):
                self.client.loop_stop()
            if hasattr(self.client, "disconnect"):
                self.client.disconnect()

    def run(self):  # pragma: no cover
        with self.app.app_context():
            try:
                self.client = mqtt.Client(client_id=f"{self.app.config['MQTT_CLIENT_ID']}-simulator")
                if self.app.config["MQTT_USERNAME"]:
                    self.client.username_pw_set(
                        self.app.config["MQTT_USERNAME"],
                        self.app.config["MQTT_PASSWORD"],
                    )
                self.client.on_connect = self.on_connect
                self.client.on_message = self.on_message
                self.client.connect(
                    self.app.config["MQTT_BROKER_HOST"],
                    self.app.config["MQTT_BROKER_PORT"],
                    self.app.config["MQTT_KEEPALIVE"],
                )
                self.client.loop_start()
            except Exception as exc:
                self.app.logger.warning("内置数据模拟器启动失败: %s", exc)
                return

            self.publish_snapshot()
            while not self.stop_event.wait(self._publish_interval()):
                self.publish_snapshot()

    def on_connect(self, client, userdata, flags, rc, properties=None):  # pragma: no cover
        client.subscribe(self.app.config["MQTT_TOPIC_CONTROL"])
        self.app.logger.info("内置数据模拟器已连接 MQTT，结果码: %s", rc)

    def on_message(self, client, userdata, message):  # pragma: no cover
        with self.app.app_context():
            payload = json.loads(message.payload.decode("utf-8"))
            self.handle_command(payload)

    def _publish_interval(self):
        value = get_config_value("simulator_publish_interval", "3.0")
        try:
            return max(float(value), 0.5)
        except ValueError:
            return 3.0

    def _next_numeric_value(self, device, config):
        minimum = config.numeric_min if config.numeric_min is not None else 0.0
        maximum = config.numeric_max if config.numeric_max is not None else 100.0
        fluctuation = config.fluctuation if config.fluctuation is not None else max((maximum - minimum) * 0.08, 0.1)
        current = self.values.get(device.code)
        if current is None:
            current = random.uniform(minimum, maximum)
        current += random.uniform(-fluctuation, fluctuation)
        current = max(minimum, min(maximum, current))
        self.values[device.code] = current
        return round(current, 2)

    def build_devices_payload(self):
        ensure_simulator_configs()
        configs = {item.device_code: item for item in DeviceSimulatorConfig.query.all()}
        items = []
        for device in Device.query.order_by(Device.name.asc()).all():
            config = configs.get(device.code)
            if config is None:
                continue
            item = {
                "code": device.code,
                "name": device.name,
                "type": device.device_type,
                "data_type": device.data_type,
                "unit": device.unit or "",
                "description": device.description or "",
                "online": bool(config.online),
            }
            if device.data_type == "numeric":
                item["numeric_value"] = self._next_numeric_value(device, config) if config.online else None
            else:
                item["switch_value"] = config.switch_value if config.online else "off"
            items.append(item)
        return {
            "reported_at": now_local().replace(microsecond=0).isoformat(),
            "devices": items,
        }

    def publish_snapshot(self):
        payload = self.build_devices_payload()
        self.client.publish(
            self.app.config["MQTT_TOPIC_DEVICE"],
            json.dumps(payload, ensure_ascii=False),
        )

    def handle_command(self, payload):
        command_id = str(payload.get("command_id", "")).strip()
        device_code = str(payload.get("device_code", "")).strip()
        action = str(payload.get("action", "")).strip().lower()
        device = Device.query.filter_by(code=device_code).first()
        config = DeviceSimulatorConfig.query.filter_by(device_code=device_code).first()
        success = (
            device is not None
            and config is not None
            and device.data_type == "switch"
            and action in {"on", "off"}
            and config.online
        )
        if success:
            config.switch_value = action
            message = f"{device.name}已切换为{'开启' if action == 'on' else '关闭'}"
        else:
            message = "命令无效、设备离线或设备不支持开关控制"
        reported_at = now_local().replace(microsecond=0).isoformat()
        self.client.publish(
            self.app.config["MQTT_TOPIC_CONTROL_RESULT"],
            json.dumps(
                {
                    "command_id": command_id,
                    "device_code": device_code,
                    "success": success,
                    "message": message,
                    "reported_at": reported_at,
                },
                ensure_ascii=False,
            ),
        )
        if success:
            from app.extensions import db

            db.session.commit()
        self.publish_snapshot()


def start_simulator(app):
    """中文注释：随 Flask 主站启动内置数据模拟器。"""
    global _simulator_runtime
    if app.config.get("TESTING") or not app.config.get("ENABLE_SIMULATOR", True):
        return None
    with _runtime_lock:
        if _simulator_runtime is not None:
            return _simulator_runtime
        _simulator_runtime = EmbeddedSimulatorRuntime(app)
        _simulator_runtime.start()
        return _simulator_runtime


def restart_simulator():
    """中文注释：设备或模拟配置变更后重启后台模拟器。"""
    global _simulator_runtime
    with _runtime_lock:
        if _simulator_runtime is None:
            return
        app = _simulator_runtime.app
        _simulator_runtime.stop()
        _simulator_runtime = EmbeddedSimulatorRuntime(app)
        _simulator_runtime.start()
