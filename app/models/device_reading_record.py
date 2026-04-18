from app.extensions import db


class DeviceReadingRecord(db.Model):
    __tablename__ = "device_reading_records"

    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(64), nullable=False, index=True)
    device_name = db.Column(db.String(128), nullable=False)
    data_type = db.Column(db.String(16), nullable=False, index=True)
    numeric_value = db.Column(db.Float, nullable=True)
    switch_value = db.Column(db.String(16), nullable=True)
    online = db.Column(db.Boolean, nullable=False, default=True)
    reported_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def to_dict(self):
        return {
            "device_code": self.device_code,
            "device_name": self.device_name,
            "data_type": self.data_type,
            "numeric_value": self.numeric_value,
            "switch_value": self.switch_value or "",
            "online": bool(self.online),
            "reported_at": self.reported_at.isoformat(),
        }
