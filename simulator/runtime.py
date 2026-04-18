import json
import random
import time
from datetime import datetime

from simulator.config import SimulatorConfig

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    class _DummyPublishResult:
        """中文注释：当 paho 未安装时，模拟发布结果对象。"""

        rc = 0

    class _DummyClient:
        """中文注释：本地离线时允许模拟器以打印方式运行。"""

        def __init__(self, client_id=None):
            self.client_id = client_id
            self.on_connect = None
            self.on_message = None

        def username_pw_set(self, username, password=None):
            return None

        def connect(self, host, port=1883, keepalive=60):
            print(f"[simulator] MQTT 未安装，跳过真实连接: {host}:{port}")
            return 0

        def loop_start(self):
            return None

        def subscribe(self, topic):
            print(f"[simulator] 订阅主题: {topic}")
            return (0, 1)

        def publish(self, topic, payload):
            print(f"[simulator] 发布 {topic}: {payload}")
            return _DummyPublishResult()

    class _DummyModule:
        Client = _DummyClient

    mqtt = _DummyModule()


def _now_iso():
    return datetime.now().replace(microsecond=0).isoformat()


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class AquaponicsSimulator:
    """中文注释：维护内存态环境数据和设备状态，并持续通过 MQTT 上报。"""

    def __init__(self):
        self.client = mqtt.Client(client_id=SimulatorConfig.MQTT_CLIENT_ID)
        if SimulatorConfig.MQTT_USERNAME:
            self.client.username_pw_set(
                SimulatorConfig.MQTT_USERNAME,
                SimulatorConfig.MQTT_PASSWORD,
            )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.metrics = {
            "water_temperature": 25.2,
            "ph": 6.8,
            "dissolved_oxygen": 6.4,
            "air_temperature": 27.0,
            "air_humidity": 63.0,
        }
        self.devices = {
            "water_pump": {
                "code": "water_pump",
                "name": "循环水泵",
                "type": "pump",
                "online": True,
                "power_state": "on",
            },
            "oxygen_pump": {
                "code": "oxygen_pump",
                "name": "增氧机",
                "type": "oxygen",
                "online": True,
                "power_state": "on",
            },
            "grow_light": {
                "code": "grow_light",
                "name": "补光灯",
                "type": "light",
                "online": True,
                "power_state": "off",
            },
            "ventilation_fan": {
                "code": "ventilation_fan",
                "name": "风机",
                "type": "fan",
                "online": True,
                "power_state": "off",
            },
        }

    def on_connect(self, client, userdata, flags, rc, properties=None):  # pragma: no cover
        print(f"[simulator] MQTT 已连接，结果码: {rc}")
        client.subscribe(SimulatorConfig.TOPIC_CONTROL)

    def on_message(self, client, userdata, message):  # pragma: no cover
        payload = json.loads(message.payload.decode("utf-8"))
        self.handle_command(payload)

    def handle_command(self, payload):
        """中文注释：收到控制命令后更新设备状态并立刻回传执行结果。"""
        device_code = str(payload.get("device_code", "")).strip()
        action = str(payload.get("action", "")).strip().lower()
        command_id = str(payload.get("command_id", "")).strip()

        device = self.devices.get(device_code)
        if device is None and device_code and action in {"on", "off"}:
            device = {
                "code": device_code,
                "name": device_code,
                "type": "custom",
                "online": True,
                "power_state": "off",
            }
            self.devices[device_code] = device

        success = device is not None and action in {"on", "off"}
        if success:
            device["online"] = True
            device["power_state"] = action
            message = f"{device['name']}已切换为{'开启' if action == 'on' else '关闭'}"
        else:
            message = "命令无效或设备不存在"

        result_payload = {
            "command_id": command_id,
            "device_code": device_code,
            "success": success,
            "message": message,
            "reported_at": _now_iso(),
        }
        self.client.publish(
            SimulatorConfig.TOPIC_CONTROL_RESULT,
            json.dumps(result_payload, ensure_ascii=False),
        )
        self.publish_device_snapshot()

    def update_metrics(self):
        """中文注释：使用简单随机游走，让环境指标随设备状态自然波动。"""
        water_pump_on = self.devices["water_pump"]["power_state"] == "on"
        oxygen_on = self.devices["oxygen_pump"]["power_state"] == "on"
        light_on = self.devices["grow_light"]["power_state"] == "on"
        fan_on = self.devices["ventilation_fan"]["power_state"] == "on"

        self.metrics["water_temperature"] = _clamp(
            self.metrics["water_temperature"] + random.uniform(-0.55, 0.55) + (0.08 if not water_pump_on else -0.05),
            18.5,
            32.0,
        )
        self.metrics["ph"] = _clamp(
            self.metrics["ph"] + random.uniform(-0.12, 0.12) + (0.03 if not water_pump_on else 0),
            5.6,
            7.9,
        )
        self.metrics["dissolved_oxygen"] = _clamp(
            self.metrics["dissolved_oxygen"] + (0.34 if oxygen_on else -0.38) + random.uniform(-0.24, 0.24),
            3.8,
            8.5,
        )
        self.metrics["air_temperature"] = _clamp(
            self.metrics["air_temperature"] + (0.35 if light_on else -0.12) + (-0.28 if fan_on else 0.1) + random.uniform(-0.4, 0.4),
            16.0,
            34.5,
        )
        self.metrics["air_humidity"] = _clamp(
            self.metrics["air_humidity"] + (0.45 if not fan_on else -0.9) + random.uniform(-1.3, 1.3),
            35.0,
            90.0,
        )

    def publish_environment(self):
        payload = {
            "reported_at": _now_iso(),
            "metrics": {
                key: round(value, 2)
                for key, value in self.metrics.items()
            },
        }
        self.client.publish(
            SimulatorConfig.TOPIC_ENVIRONMENT,
            json.dumps(payload, ensure_ascii=False),
        )

    def publish_device_snapshot(self):
        payload = {
            "reported_at": _now_iso(),
            "devices": list(self.devices.values()),
        }
        self.client.publish(
            SimulatorConfig.TOPIC_DEVICE,
            json.dumps(payload, ensure_ascii=False),
        )

    def run(self):  # pragma: no cover
        print("[simulator] 启动鱼菜共生数据模拟器")
        self.client.connect(
            SimulatorConfig.MQTT_BROKER_HOST,
            SimulatorConfig.MQTT_BROKER_PORT,
            SimulatorConfig.MQTT_KEEPALIVE,
        )
        self.client.loop_start()
        self.publish_device_snapshot()
        while True:
            self.update_metrics()
            self.publish_environment()
            self.publish_device_snapshot()
            time.sleep(SimulatorConfig.PUBLISH_INTERVAL)
