from app.extensions import db


class DeviceSimulatorConfig(db.Model):
    __tablename__ = "device_simulator_configs"

    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    online = db.Column(db.Boolean, nullable=False, default=True)
    numeric_min = db.Column(db.Float, nullable=True)
    numeric_max = db.Column(db.Float, nullable=True)
    fluctuation = db.Column(db.Float, nullable=True)
    switch_value = db.Column(db.String(16), nullable=False, default="off")
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def to_dict(self):
        return {
            "device_code": self.device_code,
            "online": bool(self.online),
            "numeric_min": self.numeric_min,
            "numeric_max": self.numeric_max,
            "fluctuation": self.fluctuation,
            "switch_value": self.switch_value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
