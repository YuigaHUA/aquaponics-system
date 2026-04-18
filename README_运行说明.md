# 鱼菜共生项目运行说明

## 1. 安装依赖

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. 初始化 MySQL

```powershell
mysql -uroot -p < .\sql\mysql_init.sql
```

当前项目配置已经直接写在代码里：

- Flask 主站配置文件：`config\config.py`
- 模拟器配置文件：`simulator\config.py`

如果你需要改主机、端口、数据库账号、MQTT 地址或默认管理员账号，直接编辑这两个配置文件即可。

如果当前机器还没有安装 `PyMySQL`，项目仍会自动回退到 `instance\aquaponics_demo.db` 作为本地开发库；正式联调 MySQL 时，请先安装 `PyMySQL`。

## 3. 启动 Flask 主站

```powershell
python .\run.py
```

默认地址：`http://127.0.0.1:5000`

默认账号：

- 用户名：`admin`
- 密码：`123456`

## 4. 数据模拟器

数据模拟器已经随 Flask 主站一起启动，不需要再单独运行。模拟器仍通过 MQTT 向后端上报设备数据，并接收控制命令。

注意：

- 默认 MQTT 地址为 `127.0.0.1:1883`，请先确认本机 MQTT Broker 已启动。
- 设备新增、删除或模拟器配置保存后，主站会自动重启内置数据模拟器。
- `python .\simulator\run_simulator.py` 仅作为调试入口保留，日常运行不需要执行。

## 5. 当前功能状态

- 监控大屏：已实现
- 设备控制：已实现
- 设备管理：已实现
- 模拟器配置：已实现
- MQTT 收发：已实现
- WebSocket 实时刷新：已实现
- AI 对话 / DeepSeek / RAG：已实现

## 6. 测试

```powershell
python -m unittest tests.test_app -v
```
