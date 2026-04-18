from app.extensions import db
from app.models import Device, DeviceSimulatorConfig


def _device_definition(device_code):
    """中文注释：从当前应用配置中查找设备默认模拟参数。"""
    from flask import current_app, has_app_context

    if not has_app_context():
        return {}
    for item in current_app.config.get("DEVICE_DEFINITIONS", []):
        if item.get("code") == device_code:
            return item
    return {}


def _default_numeric_config(device):
    definition = _device_definition(device.code)
    if {
        "simulator_min",
        "simulator_max",
        "simulator_fluctuation",
    }.issubset(definition):
        return (
            float(definition["simulator_min"]),
            float(definition["simulator_max"]),
            float(definition["simulator_fluctuation"]),
        )

    minimum = device.threshold_min if device.threshold_min is not None else 0.0
    maximum = device.threshold_max if device.threshold_max is not None else 100.0
    if minimum >= maximum:
        minimum, maximum = 0.0, 100.0
    return minimum, maximum, max((maximum - minimum) * 0.08, 0.1)


def _default_switch_value(device):
    definition = _device_definition(device.code)
    value = str(definition.get("simulator_switch_value", "on")).strip().lower()
    return value if value in {"on", "off"} else "on"


def ensure_simulator_configs():
    """中文注释：确保每个设备都有一条模拟器配置。"""
    existing = {item.device_code: item for item in DeviceSimulatorConfig.query.all()}
    device_codes = set()
    for device in Device.query.order_by(Device.name.asc()).all():
        device_codes.add(device.code)
        config = existing.get(device.code)
        if config is not None:
            continue
        numeric_min, numeric_max, fluctuation = _default_numeric_config(device)
        db.session.add(
            DeviceSimulatorConfig(
                device_code=device.code,
                online=True,
                numeric_min=numeric_min if device.data_type == "numeric" else None,
                numeric_max=numeric_max if device.data_type == "numeric" else None,
                fluctuation=fluctuation if device.data_type == "numeric" else None,
                switch_value=_default_switch_value(device) if device.data_type == "switch" else "off",
            )
        )

    for config in DeviceSimulatorConfig.query.all():
        if config.device_code not in device_codes:
            db.session.delete(config)
    db.session.commit()


def get_simulator_configs():
    ensure_simulator_configs()
    configs = {item.device_code: item for item in DeviceSimulatorConfig.query.all()}
    return [
        {
            "device": device.to_dict(),
            "config": configs[device.code].to_dict(),
        }
        for device in Device.query.order_by(Device.name.asc()).all()
    ]


def update_simulator_configs(items):
    ensure_simulator_configs()
    configs = {item.device_code: item for item in DeviceSimulatorConfig.query.all()}
    devices = {item.code: item for item in Device.query.all()}
    for item in items or []:
        code = str(item.get("device_code", "")).strip()
        config = configs.get(code)
        device = devices.get(code)
        if config is None or device is None:
            continue

        config.online = bool(item.get("online", False))
        switch_value = str(item.get("switch_value", config.switch_value)).strip().lower()
        if switch_value in {"on", "off"}:
            config.switch_value = switch_value

        if device.data_type == "numeric":
            numeric_min = float(item.get("numeric_min", 0))
            numeric_max = float(item.get("numeric_max", 100))
            fluctuation = float(item.get("fluctuation", 1))
            if numeric_min >= numeric_max:
                raise ValueError(f"{device.name} 的模拟最小值必须小于最大值。")
            if fluctuation < 0:
                raise ValueError(f"{device.name} 的波动大小不能小于 0。")
            config.numeric_min = numeric_min
            config.numeric_max = numeric_max
            config.fluctuation = fluctuation
    db.session.commit()
    return get_simulator_configs()
