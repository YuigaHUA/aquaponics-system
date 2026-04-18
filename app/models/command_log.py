from app.extensions import db


class CommandLog(db.Model):
    __tablename__ = "command_logs"

    id = db.Column(db.Integer, primary_key=True)
    command_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    device_code = db.Column(db.String(64), nullable=False, index=True)
    action = db.Column(db.String(16), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="pending", index=True)
    source = db.Column(db.String(32), nullable=False, default="web")
    message = db.Column(db.String(255), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=False, index=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def to_dict(self):
        return {
            "command_id": self.command_id,
            "device_code": self.device_code,
            "action": self.action,
            "status": self.status,
            "source": self.source,
            "message": self.message or "",
            "issued_at": self.issued_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat()
            if self.acknowledged_at
            else None,
        }
