# Aquaponics Intelligent Management System

## Development Tools

- VSCode (Python/Flask development, frontend page coding and debugging)
- MySQL (database storage)
- Browser (frontend page testing)
- Postman (API debugging, optional)
- MQTTX / MQTT Explorer (MQTT message debugging, optional)

## Development Languages

- Python
- HTML
- CSS
- JavaScript

## Technology Stack

| Layer | Technology |
|:---|:---|
| Backend Framework | Flask |
| Frontend Pages | HTML + CSS + JavaScript |
| Frontend UI Framework | Bootstrap 5 + AdminLTE |
| Chart Visualization | ECharts |
| Template Engine | Jinja2 |
| Real-Time Communication | WebSocket |
| Message Transport | MQTT |
| Data Storage | MySQL |
| AI Dialogue Integration | DeepSeek Chat API |
| Lightweight Knowledge Base | RAG (Retrieval-Augmented Generation) |
| Data Simulation Module | Dynamic data simulator implemented in Python |

## Hardware Components

- No physical hardware required

## Overall Functionality and Requirements

### I. Frontend Page Functionality

#### 1. Monitoring Dashboard

Used to display core monitoring information of the aquaponics system. The page should be visually appealing, intuitive, and provide effective data visualization. Key features include:

- Display real-time environmental data such as water temperature, pH, dissolved oxygen, air temperature, and air humidity
- Display current status of major equipment, including pump, aerator, grow light, and fan
- Display alert information such as threshold violations and device anomalies
- Support real-time data refresh via WebSocket
- Support ECharts visualizations including line charts, gauge charts, and bar charts

#### 2. AI Dialogue Interface

Used to implement the built-in AI assistant functionality, providing basic intelligent Q&A capabilities. Key features include:

- Provide a chat-style interactive interface
- Support user input of questions and display AI-generated responses
- Support retention of basic conversation history
- Integrate with DeepSeek Chat API
- Lightweight integration with RAG knowledge base to generate responses augmented by predefined knowledge content

#### 3. Device Control Panel

Used for manual control of actuators within the system. Key features include:

- Display device list and current operating status
- Support ON/OFF control for pump, aerator, grow light, and fan
- Support visual feedback for control execution results
- Maintain visual consistency with the overall system design

#### 4. Device Management Page

Used to display basic management information of system devices. Key features include:

- Display device name, device ID, device type, and device status
- Support viewing device online/offline status
- Support viewing basic device description information
- Provide basic information display and management for system devices

---

### II. Backend API Functionality

#### 1. Data Reception Interface

Used to receive and process system operational data. Key features include:

- Receive environmental monitoring data via MQTT
- Receive device status data via MQTT
- Parse, process, and store received data
- Push latest data to frontend pages

#### 2. Real-Time Push Functionality

Used to implement real-time data updates from backend to frontend. Key features include: 

- Push latest environmental data to monitoring dashboard via WebSocket
- Push device status change information to frontend via WebSocket
- Push alert information to frontend via WebSocket

#### 3. Device Control Interface

Used to process device control requests initiated from the frontend. Key features include:

- Receive device ON/OFF control commands from frontend
- Update current device status
- Return control execution results
- Support publishing control messages via MQTT

#### 4. Device Management Interface

Used to implement device information queries. Key features include:

- Retrieve device list
- Retrieve detailed device information
- Retrieve current device status information

#### 5. Historical Data Interface

Used to implement historical data query and display. Key features include:

- Query historical environmental monitoring data
- Query historical device status data
- Support basic filtering by time range
- Provide data support for chart visualizations

#### 6. AI Dialogue Interface

Used to implement system AI Q&A capabilities. Key features include:

- Receive user questions from frontend
- Call DeepSeek Chat API to obtain responses
- Enhance retrieval using lightweight RAG knowledge base
- Return AI Q&A results to frontend pages

#### 7. Alert Processing Functionality

Used to implement basic anomaly detection and notification. Key features include:

- Perform threshold evaluation on monitoring data
- Generate alert information for anomalous data
- Push alert results to frontend pages
- Support storage of basic alert records

---

### III. Data Simulator Functionality

As this project does not involve physical hardware, an independent data simulator module shall be developed in Python to dynamically generate and report system operational data. Key features include:

#### 1. Environmental Data Simulation

- Dynamically generate monitoring data such as water temperature, pH, dissolved oxygen, air temperature, and air humidity
- Support data refresh over time
- Support configuration of basic fluctuation ranges to make data behavior more realistic

#### 2. Device Status Simulation

- Simulate operating status of pump, aerator, grow light, and fan
- Support device status updates in response to control commands
- Support generation of device online/offline or operating status change information

#### 3. MQTT Data Reporting

- The data simulator shall publish data to a designated server via MQTT
- Support publishing to environmental data topics
- Support publishing to device status topics
- Support continuous reporting at configurable time intervals

#### 4. Backend Integration

- Data reported by the simulator shall be correctly subscribed to and processed by the Flask backend
- The backend shall complete monitoring display, historical recording, alert evaluation, and page push based on simulator data

---

### IV. Overall System Requirements

1. The system backend shall be developed using Flask
2. Frontend pages shall be developed using HTML, CSS, and JavaScript, combined with Bootstrap 5, AdminLTE, and ECharts to achieve a high-quality visual presentation
3. Data shall be transmitted via MQTT, and the backend shall push data to the frontend in real-time via WebSocket
4. Database storage shall use MySQL
5. The system shall include four core pages: Monitoring Dashboard, AI Dialogue Interface, Device Control Panel, and Device Management Page
6. The system shall integrate a lightweight RAG knowledge base and implement AI dialogue capabilities via the DeepSeek Chat API
7. The overall system shall maintain clear structure, consistent page design, and complete functionality suitable for demonstration and evaluationInitialize MySQL
powershell
mysql -uroot -p < .\sql\mysql_init.sql
Project configuration is already written directly in the code:

Flask main application configuration file: config\config.py

Simulator configuration file: simulator\config.py

If you need to change the host, port, database account, MQTT address, or default administrator account, edit these two configuration files directly.

If PyMySQL is not installed on the current machine, the project will automatically fall back to instance\aquaponics_demo.db as a local development database. For formal integration testing with MySQL, please install PyMySQL first.

3. Start Flask Application
powershell
python .\run.py
Default access URL: http://127.0.0.1:5000

Default account:

Username: admin

Password: 123456

4. Data Simulator
The data simulator is already started together with the Flask main application and does not need to be run separately. The simulator still reports device data to the backend via MQTT and receives control commands.

Note:

The default MQTT address is 127.0.0.1:1883. Please ensure that the local MQTT Broker is already running.

After adding or deleting devices, or saving simulator configuration, the main application will automatically restart the built-in data simulator.

python .\simulator\run_simulator.py is retained only as a debugging entry point and does not need to be executed for daily operation. 

Testing
python -m unittest tests.test_app -v



