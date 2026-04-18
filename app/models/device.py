from app.extensions import db


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    device_type = db.Column(db.String(64), nullable=False)
    data_type = db.Column(db.String(16), nullable=False, default="switch")
    unit = db.Column(db.String(32), nullable=True)
    threshold_min = db.Column(db.Float, nullable=True)
    threshold_max = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    online = db.Column(db.Boolean, nullable=False, default=False)
    power_state = db.Column(db.String(16), nullable=False, default="off")
    last_reported_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def to_dict(self):
        from app.models.device_reading_record import DeviceReadingRecord

        latest = (
            DeviceReadingRecord.query.filter_by(device_code=self.code)
            .order_by(DeviceReadingRecord.reported_at.desc())
            .first()
        )
        return {
            "code": self.code,
            "name": self.name,
            "device_type": self.device_type,
            "data_type": self.data_type,
            "unit": self.unit or "",
            "threshold_min": self.threshold_min,
            "threshold_max": self.threshold_max,
            "description": self.description or "",
            "online": bool(self.online),
            "power_state": self.power_state,
            "latest_reading": latest.to_dict() if latest else None,
            "last_reported_at": self.last_reported_at.isoformat()
            if self.last_reported_at
            else None,
        }
