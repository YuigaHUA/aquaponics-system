from app.extensions import db
from app.models import Device, User
from app.services.config_service import seed_system_configs
from app.services.simulator_config_service import ensure_simulator_configs


def seed_defaults():
    """中文注释：初始化默认管理员和演示设备清单。"""
    from flask import current_app

    username = current_app.config["ADMIN_DEFAULT_USERNAME"]
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(
            username=username,
            display_name=current_app.config["ADMIN_DISPLAY_NAME"],
        )
        user.set_password(current_app.config["ADMIN_DEFAULT_PASSWORD"])
        db.session.add(user)

    existing_devices = {device.code: device for device in Device.query.all()}
    for item in current_app.config["DEVICE_DEFINITIONS"]:
        device = existing_devices.get(item["code"])
        if device is None:
            device = Device(
                code=item["code"],
                name=item["name"],
                device_type=item["device_type"],
                data_type=item.get("data_type", "switch"),
                unit=item.get("unit", ""),
                threshold_min=item.get("threshold_min"),
                threshold_max=item.get("threshold_max"),
                description=item["description"],
                online=False,
                power_state="off",
            )
            db.session.add(device)
            continue

        if not device.name:
            device.name = item["name"]
        if not device.device_type:
            device.device_type = item["device_type"]
        if not device.data_type:
            device.data_type = item.get("data_type", "switch")
        if not device.unit:
            device.unit = item.get("unit", "")
        if device.threshold_min is None:
            device.threshold_min = item.get("threshold_min")
        if device.threshold_max is None:
            device.threshold_max = item.get("threshold_max")
        if not device.description:
            device.description = item["description"]

    db.session.commit()
    seed_system_configs()
    ensure_simulator_configs()
