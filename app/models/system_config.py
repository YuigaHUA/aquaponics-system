from app.extensions import db


class SystemConfig(db.Model):
    __tablename__ = "system_configs"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    label = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_secret = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def to_dict(self, masked=True):
        value = self.value or ""
        if masked and self.is_secret and value:
            value = "******"
        return {
            "key": self.key,
            "value": value,
            "label": self.label,
            "description": self.description or "",
            "is_secret": bool(self.is_secret),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
