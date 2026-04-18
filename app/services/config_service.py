from app.extensions import db
from app.models import SystemConfig


CONFIG_DEFINITIONS = {
    "deepseek_api_key": {
        "label": "DeepSeek API Key",
        "description": "用于后续接入 DeepSeek 对话能力。",
        "default": "",
        "is_secret": True,
    },
    "deepseek_base_url": {
        "label": "DeepSeek Base URL",
        "description": "DeepSeek 接口基础地址。",
        "default": "https://api.deepseek.com",
        "is_secret": False,
    },
    "deepseek_model": {
        "label": "DeepSeek 模型",
        "description": "默认调用的 DeepSeek 模型名称。",
        "default": "deepseek-chat",
        "is_secret": False,
    },
    "ai_chat_history_limit": {
        "label": "AI 聊天记录上限",
        "description": "每个用户最多保存的 AI 聊天消息数，最大 1000。",
        "default": "1000",
        "is_secret": False,
    },
    "mqtt_broker_host": {
        "label": "MQTT Broker 地址",
        "description": "主站和模拟器连接的 MQTT 服务地址。",
        "default": "127.0.0.1",
        "is_secret": False,
    },
    "mqtt_broker_port": {
        "label": "MQTT Broker 端口",
        "description": "主站和模拟器连接的 MQTT 服务端口。",
        "default": "1883",
        "is_secret": False,
    },
    "mqtt_keepalive": {
        "label": "MQTT Keepalive",
        "description": "MQTT 心跳保活秒数。",
        "default": "60",
        "is_secret": False,
    },
    "simulator_publish_interval": {
        "label": "模拟器发布间隔",
        "description": "模拟器数据上报间隔，单位秒。",
        "default": "3.0",
        "is_secret": False,
    },
}


def seed_system_configs():
    """中文注释：初始化系统配置项，避免页面首次打开为空。"""
    existing = {item.key: item for item in SystemConfig.query.all()}
    for key, definition in CONFIG_DEFINITIONS.items():
        item = existing.get(key)
        if item is None:
            db.session.add(
                SystemConfig(
                    key=key,
                    value=definition["default"],
                    label=definition["label"],
                    description=definition["description"],
                    is_secret=definition["is_secret"],
                )
            )
            continue

        item.label = definition["label"]
        item.description = definition["description"]
        item.is_secret = definition["is_secret"]
    db.session.commit()


def get_system_configs(masked=True):
    """中文注释：按定义顺序返回配置，便于前端稳定渲染。"""
    items = {item.key: item for item in SystemConfig.query.all()}
    return [
        items[key].to_dict(masked=masked)
        for key in CONFIG_DEFINITIONS
        if key in items
    ]


def get_config_value(key, default=""):
    item = SystemConfig.query.filter_by(key=key).first()
    if item is None or item.value in (None, ""):
        return default
    return item.value


def update_system_configs(values):
    """中文注释：保存配置；密钥字段为空时保留原值。"""
    items = {item.key: item for item in SystemConfig.query.all()}
    for key, definition in CONFIG_DEFINITIONS.items():
        if key not in values:
            continue
        item = items.get(key)
        if item is None:
            item = SystemConfig(
                key=key,
                label=definition["label"],
                description=definition["description"],
                is_secret=definition["is_secret"],
            )
            db.session.add(item)

        value = str(values.get(key, "")).strip()
        if definition["is_secret"] and value == "":
            continue
        item.value = value

    db.session.commit()
    return get_system_configs(masked=True)


def apply_runtime_config(app):
    """中文注释：主站启动时把数据库配置应用到 Flask 运行配置。"""
    items = {item.key: item.value or "" for item in SystemConfig.query.all()}
    mapping = {
        "deepseek_api_key": ("DEEPSEEK_API_KEY", str),
        "deepseek_base_url": ("DEEPSEEK_BASE_URL", str),
        "deepseek_model": ("DEEPSEEK_MODEL", str),
        "mqtt_broker_host": ("MQTT_BROKER_HOST", str),
        "mqtt_broker_port": ("MQTT_BROKER_PORT", int),
        "mqtt_keepalive": ("MQTT_KEEPALIVE", int),
    }
    for key, (config_key, converter) in mapping.items():
        value = items.get(key)
        if value in (None, ""):
            continue
        try:
            app.config[config_key] = converter(value)
        except ValueError:
            app.logger.warning("系统配置 %s 格式无效，已忽略。", key)
