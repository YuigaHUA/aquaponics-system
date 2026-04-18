from app.extensions import db


class AlarmRecord(db.Model):
    __tablename__ = "alarm_records"

    id = db.Column(db.Integer, primary_key=True)
    metric_key = db.Column(db.String(64), nullable=False, index=True)
    metric_label = db.Column(db.String(64), nullable=False)
    severity = db.Column(db.String(16), nullable=False, default="warning")
    message = db.Column(db.String(255), nullable=False)
    current_value = db.Column(db.Float, nullable=False)
    threshold_text = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="active", index=True)
    triggered_at = db.Column(db.DateTime, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "metric_key": self.metric_key,
            "metric_label": self.metric_label,
            "severity": self.severity,
            "message": self.message,
            "current_value": self.current_value,
            "threshold_text": self.threshold_text,
            "status": self.status,
            "triggered_at": self.triggered_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
