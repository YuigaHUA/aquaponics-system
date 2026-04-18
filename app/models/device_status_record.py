from app.extensions import db


class DeviceStatusRecord(db.Model):
    __tablename__ = "device_status_records"

    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(64), nullable=False, index=True)
    device_name = db.Column(db.String(128), nullable=False)
    device_type = db.Column(db.String(64), nullable=False)
    online = db.Column(db.Boolean, nullable=False)
    power_state = db.Column(db.String(16), nullable=False)
    reported_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def to_dict(self):
        return {
            "device_code": self.device_code,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "online": bool(self.online),
            "power_state": self.power_state,
            "reported_at": self.reported_at.isoformat(),
        }
