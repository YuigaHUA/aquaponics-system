from importlib.util import find_spec
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


def _default_database_uri():
    """Prefer MySQL, fall back to SQLite if driver missing or connection fails."""
    if find_spec("pymysql") is not None:
        try:
            import pymysql
            conn = pymysql.connect(
                host='127.0.0.1',
                port=3306,
                user='root',
                password='271539',
                db='aquaponics_demo'
            )
            conn.close()
            return "mysql+pymysql://root:271539@127.0.0.1:3306/aquaponics_demo?charset=utf8mb4"
        except:
            pass
    sqlite_path = (INSTANCE_DIR / "aquaponics_demo.db").as_posix()
    return f"sqlite:///{sqlite_path}"


class Config:
    """Centralized management of Flask, database, MQTT and demo system base config."""

    SECRET_KEY = "aquaponics-dev-secret-key"
    DEBUG = True
    APP_HOST = "0.0.0.0"
    APP_PORT = 5000

    SQLALCHEMY_DATABASE_URI = _default_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MQTT_BROKER_HOST = "127.0.0.1"
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = ""
    MQTT_PASSWORD = ""
    MQTT_CLIENT_ID = "aquaponics-flask"
    MQTT_KEEPALIVE = 60

    SOCKETIO_ASYNC_MODE = "threading"
    ENABLE_MQTT = True
    ENABLE_SIMULATOR = True

    DEEPSEEK_API_KEY = ""
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"

    ADMIN_DEFAULT_USERNAME = "admin"
    ADMIN_DEFAULT_PASSWORD = "123456"
    ADMIN_DISPLAY_NAME = "Administrator"

    MQTT_TOPIC_ENVIRONMENT = "aquaponics/telemetry/environment"
    MQTT_TOPIC_DEVICE = "aquaponics/telemetry/device"
    MQTT_TOPIC_CONTROL = "aquaponics/control/command"
    MQTT_TOPIC_CONTROL_RESULT = "aquaponics/control/result"

    DEVICE_DEFINITIONS = [
        {
            "code": "water_temperature_sensor",
            "name": "Water Temperature Sensor",
            "device_type": "water_temperature",
            "data_type": "numeric",
            "unit": "°C",
            "threshold_min": 20.0,
            "threshold_max": 30.0,
            "simulator_min": 22.0,
            "simulator_max": 28.0,
            "simulator_fluctuation": 0.8,
            "description": "Monitors fish tank water temperature to assess fish activity and nitrification system status.",
        },
        {
            "code": "ph_sensor",
            "name": "pH Sensor",
            "device_type": "ph",
            "data_type": "numeric",
            "unit": "",
            "threshold_min": 6.0,
            "threshold_max": 7.5,
            "simulator_min": 6.4,
            "simulator_max": 7.2,
            "simulator_fluctuation": 0.12,
            "description": "Monitors water pH level to ensure fish and plant roots are in optimal conditions.",
        },
        {
            "code": "dissolved_oxygen_sensor",
            "name": "Dissolved Oxygen Sensor",
            "device_type": "dissolved_oxygen",
            "data_type": "numeric",
            "unit": "mg/L",
            "threshold_min": 5.0,
            "threshold_max": 9.5,
            "simulator_min": 5.8,
            "simulator_max": 8.5,
            "simulator_fluctuation": 0.35,
            "description": "Monitors dissolved oxygen in fish tank for aerator control and alerts.",
        },
        {
            "code": "air_temperature_sensor",
            "name": "Air Temperature Sensor",
            "device_type": "air_temperature",
            "data_type": "numeric",
            "unit": "°C",
            "threshold_min": 18.0,
            "threshold_max": 32.0,
            "simulator_min": 22.0,
            "simulator_max": 30.0,
            "simulator_fluctuation": 0.9,
            "description": "Monitors greenhouse air temperature for ventilation and supplemental lighting control.",
        },
        {
            "code": "air_humidity_sensor",
            "name": "Air Humidity Sensor",
            "device_type": "air_humidity",
            "data_type": "numeric",
            "unit": "%",
            "threshold_min": 40.0,
            "threshold_max": 85.0,
            "simulator_min": 55.0,
            "simulator_max": 78.0,
            "simulator_fluctuation": 2.5,
            "description": "Monitors greenhouse humidity to assess transpiration and ventilation status.",
        },
        {
            "code": "water_level_sensor",
            "name": "Water Level Sensor",
            "device_type": "water_level",
            "data_type": "numeric",
            "unit": "cm",
            "threshold_min": 25.0,
            "threshold_max": 80.0,
            "simulator_min": 35.0,
            "simulator_max": 70.0,
            "simulator_fluctuation": 2.0,
            "description": "Monitors fish tank or return water reservoir level for refill and dry-run protection.",
        },
        {
            "code": "ec_sensor",
            "name": "EC Sensor",
            "device_type": "ec",
            "data_type": "numeric",
            "unit": "mS/cm",
            "threshold_min": 0.8,
            "threshold_max": 2.2,
            "simulator_min": 1.1,
            "simulator_max": 1.8,
            "simulator_fluctuation": 0.08,
            "description": "Monitors water electrical conductivity to reflect nutrient concentration changes.",
        },
        {
            "code": "water_flow_sensor",
            "name": "Water Flow Sensor",
            "device_type": "water_flow",
            "data_type": "numeric",
            "unit": "L/min",
            "threshold_min": 8.0,
            "threshold_max": 30.0,
            "simulator_min": 12.0,
            "simulator_max": 24.0,
            "simulator_fluctuation": 1.5,
            "description": "Monitors circulation pipe flow to detect blockages, water shortage or pump anomalies.",
        },
        {
            "code": "nitrate_sensor",
            "name": "Nitrate Sensor",
            "device_type": "nitrate",
            "data_type": "numeric",
            "unit": "mg/L",
            "threshold_min": 20.0,
            "threshold_max": 120.0,
            "simulator_min": 30.0,
            "simulator_max": 90.0,
            "simulator_fluctuation": 5.0,
            "description": "Monitors nitrate levels to reflect system nitrification efficiency and plant absorption.",
        },
        {
            "code": "water_pump",
            "name": "Circulation Pump",
            "device_type": "pump",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "Circulates water between fish tank and grow bed.",
        },
        {
            "code": "oxygen_pump",
            "name": "Aerator",
            "device_type": "oxygen",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "Increases dissolved oxygen to maintain safe oxygen levels in fish tank.",
        },
        {
            "code": "grow_light",
            "name": "Grow Light",
            "device_type": "light",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "Supplements natural light when insufficient to support plant growth.",
        },
        {
            "code": "ventilation_fan",
            "name": "Ventilation Fan",
            "device_type": "fan",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "Balances temperature and humidity, ensures air circulation.",
        },
        {
            "code": "auto_feeder",
            "name": "Auto Feeder",
            "device_type": "feeder",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "off",
            "description": "Timed feeding according to breeding schedule, reduces manual monitoring.",
        },
        {
            "code": "water_heater",
            "name": "Water Heater",
            "device_type": "heater",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "off",
            "description": "Auxiliary water heating in low temperatures to protect fish and nitrifying bacteria.",
        },
        {
            "code": "refill_valve",
            "name": "Auto Refill Valve",
            "device_type": "valve",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "off",
            "description": "Opens when water level is low to maintain safe water level in fish tank and reservoir.",
        },
    ]

    METRIC_LABELS = {
        "water_temperature": "Water Temp",
        "ph": "pH",
        "dissolved_oxygen": "DO",
        "air_temperature": "Air Temp",
        "air_humidity": "Humidity",
    }

    METRIC_UNITS = {
        "water_temperature": "°C",
        "ph": "",
        "dissolved_oxygen": "mg/L",
        "air_temperature": "°C",
        "air_humidity": "%",
    }

    ALERT_RULES = {
        "water_temperature": {"min": 20.0, "max": 30.0},
        "ph": {"min": 6.0, "max": 7.5},
        "dissolved_oxygen": {"min": 5.0},
        "air_temperature": {"min": 18.0, "max": 32.0},
        "air_humidity": {"min": 40.0, "max": 85.0},
    }

    INSTANCE_DIR = INSTANCE_DIR


class DevelopmentConfig(Config):
    pass


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    ENABLE_MQTT = False


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
