try:
    from flask_socketio import SocketIO
except ImportError:  # pragma: no cover
    class SocketIO:  # type: ignore[override]
        """中文注释：依赖未安装时提供最小兼容实现，便于离线开发。"""

        def __init__(self, *args, **kwargs):
            self.app = None

        def init_app(self, app, **kwargs):
            self.app = app

        def emit(self, event, data=None, **kwargs):
            return None

        def run(self, app, host="127.0.0.1", port=5000, debug=False, **kwargs):
            app.run(host=host, port=port, debug=debug)
