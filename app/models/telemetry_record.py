from app.extensions import db


class TelemetryRecord(db.Model):
    __tablename__ = "telemetry_records"

    id = db.Column(db.Integer, primary_key=True)
    reported_at = db.Column(db.DateTime, nullable=False, index=True)
    water_temperature = db.Column(db.Float, nullable=False)
    ph = db.Column(db.Float, nullable=False)
    dissolved_oxygen = db.Column(db.Float, nullable=False)
    air_temperature = db.Column(db.Float, nullable=False)
    air_humidity = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def to_dict(self):
        return {
            "reported_at": self.reported_at.isoformat(),
            "water_temperature": self.water_temperature,
            "ph": self.ph,
            "dissolved_oxygen": self.dissolved_oxygen,
            "air_temperature": self.air_temperature,
            "air_humidity": self.air_humidity,
        }
