from importlib.util import find_spec
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


def _default_database_uri():
    """中文注释：优先使用写死的 MySQL，驱动缺失或连接失败时回退 SQLite。"""
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
    """中文注释：集中管理 Flask、数据库、MQTT 和演示系统基础配置。"""

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
    ADMIN_DISPLAY_NAME = "系统管理员"

    MQTT_TOPIC_ENVIRONMENT = "aquaponics/telemetry/environment"
    MQTT_TOPIC_DEVICE = "aquaponics/telemetry/device"
    MQTT_TOPIC_CONTROL = "aquaponics/control/command"
    MQTT_TOPIC_CONTROL_RESULT = "aquaponics/control/result"

    DEVICE_DEFINITIONS = [
        {
            "code": "water_temperature_sensor",
            "name": "水温传感器",
            "device_type": "water_temperature",
            "data_type": "numeric",
            "unit": "°C",
            "threshold_min": 20.0,
            "threshold_max": 30.0,
            "simulator_min": 22.0,
            "simulator_max": 28.0,
            "simulator_fluctuation": 0.8,
            "description": "监测鱼池水温，辅助判断鱼类活性和硝化系统状态。",
        },
        {
            "code": "ph_sensor",
            "name": "pH 传感器",
            "device_type": "ph",
            "data_type": "numeric",
            "unit": "",
            "threshold_min": 6.0,
            "threshold_max": 7.5,
            "simulator_min": 6.4,
            "simulator_max": 7.2,
            "simulator_fluctuation": 0.12,
            "description": "监测水体酸碱度，保障鱼类和植物根系处于适宜环境。",
        },
        {
            "code": "dissolved_oxygen_sensor",
            "name": "溶解氧传感器",
            "device_type": "dissolved_oxygen",
            "data_type": "numeric",
            "unit": "mg/L",
            "threshold_min": 5.0,
            "threshold_max": 9.5,
            "simulator_min": 5.8,
            "simulator_max": 8.5,
            "simulator_fluctuation": 0.35,
            "description": "监测鱼池溶解氧浓度，用于联动增氧设备和告警。",
        },
        {
            "code": "air_temperature_sensor",
            "name": "空气温度传感器",
            "device_type": "air_temperature",
            "data_type": "numeric",
            "unit": "°C",
            "threshold_min": 18.0,
            "threshold_max": 32.0,
            "simulator_min": 22.0,
            "simulator_max": 30.0,
            "simulator_fluctuation": 0.9,
            "description": "监测温室空气温度，辅助控制通风和补光策略。",
        },
        {
            "code": "air_humidity_sensor",
            "name": "空气湿度传感器",
            "device_type": "air_humidity",
            "data_type": "numeric",
            "unit": "%",
            "threshold_min": 40.0,
            "threshold_max": 85.0,
            "simulator_min": 55.0,
            "simulator_max": 78.0,
            "simulator_fluctuation": 2.5,
            "description": "监测温室空气湿度，辅助判断蒸腾和通风状态。",
        },
        {
            "code": "water_level_sensor",
            "name": "水位传感器",
            "device_type": "water_level",
            "data_type": "numeric",
            "unit": "cm",
            "threshold_min": 25.0,
            "threshold_max": 80.0,
            "simulator_min": 35.0,
            "simulator_max": 70.0,
            "simulator_fluctuation": 2.0,
            "description": "监测鱼池或回水仓水位，辅助补水和防干抽。",
        },
        {
            "code": "ec_sensor",
            "name": "EC 传感器",
            "device_type": "ec",
            "data_type": "numeric",
            "unit": "mS/cm",
            "threshold_min": 0.8,
            "threshold_max": 2.2,
            "simulator_min": 1.1,
            "simulator_max": 1.8,
            "simulator_fluctuation": 0.08,
            "description": "监测水体电导率，反映营养盐浓度变化。",
        },
        {
            "code": "water_flow_sensor",
            "name": "水流量传感器",
            "device_type": "water_flow",
            "data_type": "numeric",
            "unit": "L/min",
            "threshold_min": 8.0,
            "threshold_max": 30.0,
            "simulator_min": 12.0,
            "simulator_max": 24.0,
            "simulator_fluctuation": 1.5,
            "description": "监测循环管路流量，辅助发现堵塞、缺水或水泵异常。",
        },
        {
            "code": "nitrate_sensor",
            "name": "硝酸盐传感器",
            "device_type": "nitrate",
            "data_type": "numeric",
            "unit": "mg/L",
            "threshold_min": 20.0,
            "threshold_max": 120.0,
            "simulator_min": 30.0,
            "simulator_max": 90.0,
            "simulator_fluctuation": 5.0,
            "description": "监测硝酸盐水平，反映系统硝化效率和植物吸收情况。",
        },
        {
            "code": "water_pump",
            "name": "循环水泵",
            "device_type": "pump",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "负责循环水体，维持鱼池与种植槽之间的水流。",
        },
        {
            "code": "oxygen_pump",
            "name": "增氧机",
            "device_type": "oxygen",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "负责提升溶解氧，保证鱼池含氧量处于安全范围。",
        },
        {
            "code": "grow_light",
            "name": "补光灯",
            "device_type": "light",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "在自然光不足时补充光照，支持植物生长。",
        },
        {
            "code": "ventilation_fan",
            "name": "风机",
            "device_type": "fan",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "on",
            "description": "用于温湿度平衡和空气流通。",
        },
        {
            "code": "auto_feeder",
            "name": "自动投喂机",
            "device_type": "feeder",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "off",
            "description": "按养殖计划进行定时投喂，减少人工值守压力。",
        },
        {
            "code": "water_heater",
            "name": "加热棒",
            "device_type": "heater",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "off",
            "description": "在低温时辅助提升水温，保障鱼类和硝化菌活性。",
        },
        {
            "code": "refill_valve",
            "name": "自动补水阀",
            "device_type": "valve",
            "data_type": "switch",
            "unit": "",
            "simulator_switch_value": "off",
            "description": "水位偏低时开启补水，维持鱼池和回水仓安全水位。",
        },
    ]

    METRIC_LABELS = {
        "water_temperature": "水温",
        "ph": "pH",
        "dissolved_oxygen": "溶解氧",
        "air_temperature": "空气温度",
        "air_humidity": "空气湿度",
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
