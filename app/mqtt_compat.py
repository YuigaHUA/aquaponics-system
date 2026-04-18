try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    class _DummyPublishResult:
        """中文注释：模拟 paho 发布结果对象，兼容离线开发。"""

        rc = 0

    class _DummyClient:
        """中文注释：当 paho 未安装时提供空实现。"""

        def __init__(self, client_id=None):
            self.client_id = client_id
            self.on_connect = None
            self.on_message = None

        def username_pw_set(self, username, password=None):
            return None

        def connect(self, host, port=1883, keepalive=60):
            return 0

        def loop_start(self):
            return None

        def subscribe(self, topic):
            return (0, 1)

        def publish(self, topic, payload):
            return _DummyPublishResult()

    class _DummyModule:
        Client = _DummyClient

    mqtt = _DummyModule()
