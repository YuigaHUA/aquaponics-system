from sqlalchemy import inspect, text

from app.extensions import db


def ensure_runtime_schema():
    """中文注释：为已有演示库补充本次新增字段，不引入迁移框架。"""
    inspector = inspect(db.engine)
    if "devices" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("devices")}
    column_sql = {
        "data_type": "VARCHAR(16) NOT NULL DEFAULT 'switch'",
        "unit": "VARCHAR(32) NULL",
        "threshold_min": "DOUBLE NULL",
        "threshold_max": "DOUBLE NULL",
    }
    with db.engine.begin() as connection:
        for column_name, definition in column_sql.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE devices ADD COLUMN {column_name} {definition}"))
