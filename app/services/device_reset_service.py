from app.extensions import db
from app.models import (
    AlarmRecord,
    CommandLog,
    Device,
    DeviceReadingRecord,
    DeviceSimulatorConfig,
    DeviceStatusRecord,
)


def _switch_value(item):
    value = str(item.get("simulator_switch_value", "on")).strip().lower()
    return value if value in {"on", "off"} else "on"


def _numeric_config(item):
    return (
        item.get("simulator_min", item.get("threshold_min", 0.0)),
        item.get("simulator_max", item.get("threshold_max", 100.0)),
        item.get("simulator_fluctuation", 1.0),
    )


def reset_devices_from_definitions(definitions):
    """中文注释：清空设备及设备关联数据，然后按默认清单重建。"""
    AlarmRecord.query.filter(AlarmRecord.metric_key.like("device:%")).delete(synchronize_session=False)
    DeviceReadingRecord.query.delete(synchronize_session=False)
    DeviceSimulatorConfig.query.delete(synchronize_session=False)
    DeviceStatusRecord.query.delete(synchronize_session=False)
    CommandLog.query.delete(synchronize_session=False)
    Device.query.delete(synchronize_session=False)

    created_devices = []
    for item in definitions:
        device = Device(
            code=item["code"],
            name=item["name"],
            device_type=item["device_type"],
            data_type=item.get("data_type", "switch"),
            unit=item.get("unit", ""),
            threshold_min=item.get("threshold_min"),
            threshold_max=item.get("threshold_max"),
            description=item["description"],
            online=True,
            power_state=_switch_value(item) if item.get("data_type") == "switch" else "off",
        )
        db.session.add(device)
        created_devices.append(device)

        if item.get("data_type") == "numeric":
            numeric_min, numeric_max, fluctuation = _numeric_config(item)
            config = DeviceSimulatorConfig(
                device_code=item["code"],
                online=True,
                numeric_min=numeric_min,
                numeric_max=numeric_max,
                fluctuation=fluctuation,
                switch_value="off",
            )
        else:
            config = DeviceSimulatorConfig(
                device_code=item["code"],
                online=True,
                switch_value=_switch_value(item),
            )
        db.session.add(config)

    db.session.commit()
    return created_devices


def reset_devices_from_app_config():
    """中文注释：使用当前 Flask 配置中的默认设备清单重建设备。"""
    from flask import current_app

    devices = reset_devices_from_definitions(current_app.config["DEVICE_DEFINITIONS"])
    from app.services.simulator_service import restart_simulator

    restart_simulator()
    return devices
