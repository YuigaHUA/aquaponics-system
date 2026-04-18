class SimulatorConfig:
    """中文注释：模拟器配置独立维护，避免和 Flask 进程相互耦合。"""

    MQTT_BROKER_HOST = "127.0.0.1"
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = ""
    MQTT_PASSWORD = ""
    MQTT_CLIENT_ID = "aquaponics-simulator"
    MQTT_KEEPALIVE = 60
    PUBLISH_INTERVAL = 3.0

    TOPIC_ENVIRONMENT = "aquaponics/telemetry/environment"
    TOPIC_DEVICE = "aquaponics/telemetry/device"
    TOPIC_CONTROL = "aquaponics/control/command"
    TOPIC_CONTROL_RESULT = "aquaponics/control/result"
