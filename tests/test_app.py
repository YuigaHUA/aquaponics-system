import json
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.models import (
    AIChatMessage,
    AlarmRecord,
    CommandLog,
    Device,
    DeviceReadingRecord,
    DeviceSimulatorConfig,
    DeviceStatusRecord,
    SystemConfig,
    TelemetryRecord,
)
from app.services.mqtt_service import handle_message


class AquaponicsAppTestCase(unittest.TestCase):
    """中文注释：测试覆盖登录、接口、MQTT 处理和 AI 占位能力。"""

    def setUp(self):
        self.app = create_app("testing")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        from app.extensions import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login(self):
        return self.client.post(
            "/login",
            data={"username": "admin", "password": "123456"},
            follow_redirects=False,
        )

    def test_login_success(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])

    def test_api_requires_login(self):
        response = self.client.get("/api/dashboard/summary")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["message"], "Unauthorized Exception")

    def test_dashboard_summary_after_login(self):
        with self.client:
            self.login()
            response = self.client.get("/api/dashboard/summary")
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload["code"], 0)
            self.assertEqual(payload["data"]["device_totals"]["total"], len(self.app.config["DEVICE_DEFINITIONS"]))
            self.assertEqual(
                len(payload["data"]["dashboard_cards"]),
                payload["data"]["device_totals"]["total"],
            )
            self.assertTrue(
                all(item["key"].startswith("device:") for item in payload["data"]["dashboard_cards"])
            )

    def test_switch_device_history_is_not_supported(self):
        with self.client:
            self.login()
            response = self.client.get("/api/history/environment?metric=device:water_pump")
            self.assertEqual(response.status_code, 400)

    def test_management_pages_render_after_login(self):
        with self.client:
            self.login()
            for path in ("/devices", "/users", "/settings", "/simulator", "/control"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_environment_message_creates_telemetry_and_alarm(self):
        payload = {
            "reported_at": "2026-04-15T09:00:00",
            "metrics": {
                "water_temperature": 31.2,
                "ph": 6.7,
                "dissolved_oxygen": 4.2,
                "air_temperature": 28.1,
                "air_humidity": 62.0,
            },
        }
        handle_message(
            self.app.config["MQTT_TOPIC_ENVIRONMENT"],
            json.dumps(payload, ensure_ascii=False),
        )
        self.assertEqual(TelemetryRecord.query.count(), 1)
        self.assertGreaterEqual(AlarmRecord.query.filter_by(status="active").count(), 1)

    def test_device_message_updates_snapshot_table(self):
        payload = {
            "reported_at": "2026-04-15T09:05:00",
            "devices": [
                {
                    "code": "water_pump",
                    "name": "循环水泵",
                    "type": "pump",
                    "online": True,
                    "power_state": "on",
                }
            ],
        }
        handle_message(
            self.app.config["MQTT_TOPIC_DEVICE"],
            json.dumps(payload, ensure_ascii=False),
        )
        self.assertEqual(DeviceStatusRecord.query.count(), 1)
        self.assertEqual(DeviceReadingRecord.query.count(), 1)

    def test_control_command_publishes_message(self):
        with self.client:
            self.login()
            response = self.client.post(
                "/api/control/devices/water_pump",
                json={"action": "off"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(CommandLog.query.count(), 1)
            self.assertEqual(len(self.app.extensions["published_messages"]), 1)
            self.assertEqual(CommandLog.query.first().status, "failed")

    def test_user_crud_and_login(self):
        with self.client:
            self.login()
            response = self.client.post(
                "/api/users",
                json={
                    "username": "operator",
                    "display_name": "操作员",
                    "password": "abc123",
                },
            )
            self.assertEqual(response.status_code, 201)

            user_id = response.get_json()["data"]["id"]
            response = self.client.put(
                f"/api/users/{user_id}",
                json={
                    "username": "operator",
                    "display_name": "值班操作员",
                    "password": "",
                },
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/login",
            data={"username": "operator", "password": "abc123"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)

    def test_device_crud(self):
        with self.client:
            self.login()
            response = self.client.post(
                "/api/devices",
                json={
                    "code": "heater",
                    "name": "加热棒",
                    "device_type": "heater",
                    "data_type": "numeric",
                    "unit": "°C",
                    "threshold_min": 20,
                    "threshold_max": 30,
                    "description": "用于升温",
                },
            )
            self.assertEqual(response.status_code, 201)

            response = self.client.put(
                "/api/devices/heater",
                json={
                    "name": "恒温加热棒",
                    "device_type": "heater",
                    "data_type": "numeric",
                    "unit": "°C",
                    "threshold_min": 18,
                    "threshold_max": 32,
                    "description": "用于鱼池升温",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Device.query.filter_by(code="heater").first().name, "恒温加热棒")

            response = self.client.delete("/api/devices/heater")
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(Device.query.filter_by(code="heater").first())

    def test_reset_devices_from_app_config_rebuilds_device_set(self):
        from app.extensions import db
        from app.services.device_reset_service import reset_devices_from_app_config
        from app.services.time_service import now_local

        old_device = Device(
            code="old_device",
            name="旧设备",
            device_type="old",
            data_type="numeric",
            unit="",
            threshold_min=1,
            threshold_max=2,
            description="待清理设备",
        )
        db.session.add(old_device)
        db.session.add(
            DeviceReadingRecord(
                device_code="old_device",
                device_name="旧设备",
                data_type="numeric",
                numeric_value=1.5,
                online=True,
                reported_at=now_local(),
            )
        )
        db.session.add(
            DeviceStatusRecord(
                device_code="old_device",
                device_name="旧设备",
                device_type="old",
                online=True,
                power_state="on",
                reported_at=now_local(),
            )
        )
        db.session.add(DeviceSimulatorConfig(device_code="old_device", online=True, numeric_min=1, numeric_max=2))
        db.session.add(
            CommandLog(
                command_id="cmd-old",
                device_code="old_device",
                action="on",
                status="pending",
                source="web",
                issued_at=now_local(),
            )
        )
        db.session.add(
            AlarmRecord(
                metric_key="device:old_device",
                metric_label="旧设备",
                severity="warning",
                message="旧设备告警",
                current_value=3,
                threshold_text="1-2",
                status="active",
                triggered_at=now_local(),
            )
        )
        db.session.commit()

        reset_devices_from_app_config()

        expected_codes = {item["code"] for item in self.app.config["DEVICE_DEFINITIONS"]}
        self.assertEqual(Device.query.count(), len(expected_codes))
        self.assertEqual(DeviceSimulatorConfig.query.count(), len(expected_codes))
        self.assertSetEqual({device.code for device in Device.query.all()}, expected_codes)
        self.assertIsNone(Device.query.filter_by(code="old_device").first())
        self.assertEqual(DeviceReadingRecord.query.count(), 0)
        self.assertEqual(DeviceStatusRecord.query.count(), 0)
        self.assertEqual(CommandLog.query.count(), 0)
        self.assertEqual(AlarmRecord.query.filter(AlarmRecord.metric_key.like("device:%")).count(), 0)

        water_temperature = Device.query.filter_by(code="water_temperature_sensor").first()
        water_temperature_config = DeviceSimulatorConfig.query.filter_by(device_code="water_temperature_sensor").first()
        water_pump_config = DeviceSimulatorConfig.query.filter_by(device_code="water_pump").first()
        self.assertEqual(water_temperature.data_type, "numeric")
        self.assertEqual(water_temperature.unit, "°C")
        self.assertEqual(water_temperature.threshold_min, 20.0)
        self.assertEqual(water_temperature_config.numeric_min, 22.0)
        self.assertEqual(water_temperature_config.numeric_max, 28.0)
        self.assertEqual(water_pump_config.switch_value, "on")

    def test_numeric_device_reading_creates_alarm(self):
        from app.extensions import db

        device = Device(
            code="water_level",
            name="水位传感器",
            device_type="sensor",
            data_type="numeric",
            unit="cm",
            threshold_min=10,
            threshold_max=20,
            description="监测水位",
        )
        db.session.add(device)
        db.session.commit()

        payload = {
            "reported_at": "2026-04-15T09:05:00",
            "devices": [
                {
                    "code": "water_level",
                    "name": "水位传感器",
                    "type": "sensor",
                    "data_type": "numeric",
                    "unit": "cm",
                    "online": True,
                    "numeric_value": 25,
                }
            ],
        }
        handle_message(self.app.config["MQTT_TOPIC_DEVICE"], json.dumps(payload, ensure_ascii=False))
        alarm = AlarmRecord.query.filter_by(metric_key="device:water_level", status="active").first()
        self.assertIsNotNone(alarm)
        self.assertEqual(alarm.metric_label, "水位传感器")

    def test_numeric_device_rejects_control(self):
        with self.client:
            self.login()
            self.client.post(
                "/api/devices",
                json={
                    "code": "water_level",
                    "name": "水位传感器",
                    "device_type": "sensor",
                    "data_type": "numeric",
                    "unit": "cm",
                    "threshold_min": 10,
                    "threshold_max": 20,
                    "description": "监测水位",
                },
            )
            response = self.client.post("/api/control/devices/water_level", json={"action": "on"})
            self.assertEqual(response.status_code, 400)

    def test_simulator_config_api_updates_device_config(self):
        with self.client:
            self.login()
            self.client.post(
                "/api/devices",
                json={
                    "code": "water_level",
                    "name": "水位传感器",
                    "device_type": "sensor",
                    "data_type": "numeric",
                    "unit": "cm",
                    "threshold_min": 10,
                    "threshold_max": 20,
                    "description": "监测水位",
                },
            )
            response = self.client.put(
                "/api/simulator/configs",
                json={
                    "items": [
                        {
                            "device_code": "water_level",
                            "online": True,
                            "numeric_min": 11,
                            "numeric_max": 19,
                            "fluctuation": 1.5,
                            "switch_value": "off",
                        }
                    ]
                },
            )
            self.assertEqual(response.status_code, 200)

    def test_system_config_masks_api_key_and_keeps_blank_secret(self):
        with self.client:
            self.login()
            response = self.client.put(
                "/api/system/configs",
                json={
                    "deepseek_api_key": "sk-test",
                    "deepseek_model": "deepseek-chat",
                },
            )
            self.assertEqual(response.status_code, 200)
            api_key = SystemConfig.query.filter_by(key="deepseek_api_key").first()
            self.assertEqual(api_key.value, "sk-test")
            self.assertEqual(
                next(item for item in response.get_json()["data"] if item["key"] == "deepseek_api_key")["value"],
                "******",
            )

            response = self.client.put("/api/system/configs", json={"deepseek_api_key": ""})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(api_key.value, "sk-test")

    def test_command_result_updates_device_state(self):
        from app.extensions import db
        from app.services.command_service import process_command_result_payload
        from app.services.time_service import now_local

        log = CommandLog(
            command_id="cmd-test",
            device_code="water_pump",
            action="off",
            status="pending",
            source="web",
            message="等待回执",
            issued_at=now_local(),
        )
        db.session.add(log)
        db.session.commit()

        result = process_command_result_payload(
            {
                "command_id": "cmd-test",
                "device_code": "water_pump",
                "success": True,
                "message": "执行完成",
                "reported_at": "2026-04-15T09:10:00",
            }
        )
        device = Device.query.filter_by(code="water_pump").first()
        self.assertEqual(result["status"], "success")
        self.assertEqual(device.power_state, "off")
        self.assertTrue(device.online)

    def test_mqtt_disabled_init_keeps_published_messages(self):
        from app.services.mqtt_service import init_mqtt_client

        self.app.extensions["published_messages"].append({"topic": "test", "payload": {}})
        init_mqtt_client(self.app)
        self.assertEqual(len(self.app.extensions["published_messages"]), 1)

    def test_mqtt_init_reuses_existing_client(self):
        from app.services import mqtt_service

        class FakeMqttClient:
            """中文注释：替代真实 MQTT 客户端，避免单元测试连接外部服务。"""

            connect_count = 0

            def __init__(self, client_id):
                self.client_id = client_id
                self.on_connect = None
                self.on_message = None

            def username_pw_set(self, username, password):
                self.username = username
                self.password = password

            def connect(self, host, port, keepalive):
                FakeMqttClient.connect_count += 1

            def loop_start(self):
                self.loop_started = True

            def publish(self, topic, packet):
                self.last_publish = (topic, packet)

        original_client = mqtt_service.mqtt.Client
        original_mqtt_client = mqtt_service._mqtt_client
        self.app.config["TESTING"] = False
        self.app.config["ENABLE_MQTT"] = True
        self.app.extensions.pop("mqtt_client", None)
        mqtt_service._mqtt_client = None
        mqtt_service.mqtt.Client = FakeMqttClient
        try:
            first_client = mqtt_service.init_mqtt_client(self.app)
            second_client = mqtt_service.init_mqtt_client(self.app)
        finally:
            mqtt_service.mqtt.Client = original_client
            mqtt_service._mqtt_client = original_mqtt_client

        self.assertIs(first_client, second_client)
        self.assertEqual(FakeMqttClient.connect_count, 1)

    def test_ai_chat_requires_deepseek_api_key(self):
        with self.client:
            self.login()
            response = self.client.post(
                "/api/ai/chat",
                json={"message": "现在水温怎么样"},
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("DeepSeek API Key", response.get_json()["error"])
            self.assertEqual(AIChatMessage.query.count(), 0)

    def test_ai_chat_calls_deepseek_with_device_context(self):
        from app.extensions import db
        from app.models import SystemConfig

        api_key = SystemConfig.query.filter_by(key="deepseek_api_key").first()
        api_key.value = "sk-test"
        db.session.commit()

        fake_response = MagicMock()
        fake_response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "当前共有 4 个设备。"}}]},
            ensure_ascii=False,
        ).encode("utf-8")

        captured_request = {}

        def fake_request(url, data, headers, method):
            captured_request["url"] = url
            captured_request["data"] = data
            captured_request["headers"] = headers
            captured_request["method"] = method
            return "fake-request"

        with patch("app.services.ai_service.Request", side_effect=fake_request), patch(
            "app.services.ai_service.urlopen",
            return_value=fake_response,
        ):
            with self.client:
                self.login()
                response = self.client.post(
                    "/api/ai/chat",
                    json={"message": "我有几个设备？"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["data"]
        expected_device_count = len(self.app.config["DEVICE_DEFINITIONS"])
        self.assertEqual(payload["reply"], "当前共有 4 个设备。")
        self.assertEqual(payload["context_devices_count"], expected_device_count)
        self.assertEqual(AIChatMessage.query.count(), 2)

        history_response = self.client.get("/api/ai/history")
        self.assertEqual(history_response.status_code, 200)
        history = history_response.get_json()["data"]
        self.assertEqual([item["role"] for item in history], ["user", "assistant"])
        self.assertEqual(history[0]["content"], "我有几个设备？")
        self.assertEqual(history[1]["content"], "当前共有 4 个设备。")

        request_body = captured_request["data"]
        body = json.loads(request_body.decode("utf-8") if hasattr(request_body, "decode") else request_body)
        self.assertIn(f"当前系统共有 {expected_device_count} 个设备", body["messages"][1]["content"])
        self.assertIn("我有几个设备？", body["messages"][1]["content"])
        self.assertIn("适合养殖的鱼类", body["messages"][0]["content"])
        self.assertIn("不要因为缺少全部养殖资料就拒绝给出合理建议", body["messages"][0]["content"])
        self.assertEqual(captured_request["method"], "POST")
        self.assertIn("Bearer sk-test", captured_request["headers"]["Authorization"])

    def test_ai_stream_chat_saves_complete_reply(self):
        from app.extensions import db
        from app.models import SystemConfig

        api_key = SystemConfig.query.filter_by(key="deepseek_api_key").first()
        api_key.value = "sk-test"
        db.session.commit()

        expected_device_count = len(self.app.config["DEVICE_DEFINITIONS"])
        stream_lines = [
            'data: {"choices":[{"delta":{"content":"当前"}}]}\n\n'.encode("utf-8"),
            f'data: {{"choices":[{{"delta":{{"content":"共有 {expected_device_count} 个设备。"}}}}]}}\n\n'.encode("utf-8"),
            b"data: [DONE]\n\n",
            b"",
        ]
        fake_response = MagicMock()
        fake_response.readline.side_effect = stream_lines

        captured_request = {}

        def fake_request(url, data, headers, method):
            captured_request["data"] = data
            captured_request["headers"] = headers
            captured_request["method"] = method
            return "fake-stream-request"

        with patch("app.services.ai_service.Request", side_effect=fake_request), patch(
            "app.services.ai_service.urlopen",
            return_value=fake_response,
        ):
            with self.client:
                self.login()
                response = self.client.post(
                    "/api/ai/chat/stream",
                    json={"message": "我有几个设备？"},
                    buffered=True,
                )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("event: delta", body)
        self.assertIn("当前", body)
        self.assertIn(f"共有 {expected_device_count} 个设备。", body)
        self.assertIn("event: done", body)
        self.assertEqual(AIChatMessage.query.count(), 2)

        history = AIChatMessage.query.order_by(AIChatMessage.id.asc()).all()
        self.assertEqual(history[0].content, "我有几个设备？")
        self.assertEqual(history[1].content, f"当前共有 {expected_device_count} 个设备。")

        request_body = captured_request["data"]
        payload = json.loads(request_body.decode("utf-8") if hasattr(request_body, "decode") else request_body)
        self.assertTrue(payload["stream"])
        self.assertIn("系统实时数据", payload["messages"][1]["content"])
        self.assertNotIn("当前设备上下文：", payload["messages"][1]["content"])
        self.assertEqual(captured_request["method"], "POST")
        self.assertIn("Bearer sk-test", captured_request["headers"]["Authorization"])

    def test_ai_stream_chat_error_does_not_save_history(self):
        with self.client:
            self.login()
            response = self.client.post(
                "/api/ai/chat/stream",
                json={"message": "现在水温怎么样"},
                buffered=True,
            )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("event: error", body)
        self.assertIn("DeepSeek API Key", body)
        self.assertEqual(AIChatMessage.query.count(), 0)

    def test_ai_history_can_be_cleared(self):
        from app.extensions import db
        from app.models import User
        from app.services.ai_history_service import save_exchange

        user = User.query.filter_by(username="admin").first()
        save_exchange(user.id, "问题", "回答", "deepseek-chat")

        with self.client:
            self.login()
            response = self.client.delete("/api/ai/history")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(AIChatMessage.query.filter_by(user_id=user.id).count(), 0)

            history_response = self.client.get("/api/ai/history")
            self.assertEqual(history_response.status_code, 200)
            self.assertEqual(history_response.get_json()["data"], [])

    def test_ai_history_limit_prunes_old_messages_per_user(self):
        from app.extensions import db
        from app.models import User
        from app.services.ai_history_service import save_exchange

        limit_config = SystemConfig.query.filter_by(key="ai_chat_history_limit").first()
        limit_config.value = "3"
        user = User.query.filter_by(username="admin").first()
        db.session.commit()

        save_exchange(user.id, "问题一", "回答一", "deepseek-chat")
        save_exchange(user.id, "问题二", "回答二", "deepseek-chat")

        history = AIChatMessage.query.filter_by(user_id=user.id).order_by(AIChatMessage.id.asc()).all()
        self.assertEqual(len(history), 3)
        self.assertEqual([item.content for item in history], ["回答一", "问题二", "回答二"])


if __name__ == "__main__":
    unittest.main()
