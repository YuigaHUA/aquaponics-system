from flask import Flask, request
from flask_cors import CORS

from app.extensions import db, login_manager
from app.socketio_compat import SocketIO
from config.config import config


socketio = SocketIO()


def redirect_to_login():
    """中文注释：未登录页面请求统一跳转到登录页。"""
    from flask import redirect, url_for

    return redirect(url_for("auth.login"))


def create_app(config_name="default"):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config[config_name])
    app.config["INSTANCE_DIR"].mkdir(parents=True, exist_ok=True)

    CORS(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "请先登录系统。"
    login_manager.login_message_category = "warning"
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode=app.config["SOCKETIO_ASYNC_MODE"],
    )

    @login_manager.unauthorized_handler
    def unauthorized():
        """中文注释：API 返回 JSON，页面请求继续跳转登录页。"""
        if request.path.startswith("/api/"):
            from app.utils.api import error_api

            return error_api(
                "Unauthorized Exception",
                error="Unauthorized Exception",
                status_code=401,
            )
        return redirect_to_login()

    @app.context_processor
    def inject_global_values():
        """中文注释：向模板注入项目标题和当前技术栈说明。"""
        return {
            "project_name": "鱼菜共生监控系统",
        }

    from app.controllers.ai import bp as ai_bp
    from app.controllers.api import bp as api_bp
    from app.controllers.auth import bp as auth_bp
    from app.controllers.dashboard import bp as dashboard_bp
    from app.controllers.devices import bp as devices_bp
    from app.controllers.settings import bp as settings_bp
    from app.controllers.simulator import bp as simulator_bp
    from app.controllers.users import bp as users_bp
    from app.controllers.control import bp as control_bp
    from app.services.mqtt_service import init_mqtt_client
    from app.services.config_service import apply_runtime_config
    from app.services.schema_service import ensure_runtime_schema
    from app.services.seed_service import seed_defaults
    from app.services.simulator_service import start_simulator

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(control_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(simulator_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(api_bp)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        """中文注释：供 Flask-Login 从会话中恢复用户。"""
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        ensure_runtime_schema()
        seed_defaults()
        apply_runtime_config(app)
        init_mqtt_client(app)
        start_simulator(app)

    return app
