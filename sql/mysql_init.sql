-- 中文注释：鱼菜共生演示系统 MySQL 初始化脚本。
CREATE DATABASE IF NOT EXISTS aquaponics_demo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aquaponics_demo;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    device_type VARCHAR(64) NOT NULL,
    data_type VARCHAR(16) NOT NULL DEFAULT 'switch',
    unit VARCHAR(32) NULL,
    threshold_min DOUBLE NULL,
    threshold_max DOUBLE NULL,
    description TEXT NULL,
    online TINYINT(1) NOT NULL DEFAULT 0,
    power_state VARCHAR(16) NOT NULL DEFAULT 'off',
    last_reported_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS device_reading_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_code VARCHAR(64) NOT NULL,
    device_name VARCHAR(128) NOT NULL,
    data_type VARCHAR(16) NOT NULL,
    numeric_value DOUBLE NULL,
    switch_value VARCHAR(16) NULL,
    online TINYINT(1) NOT NULL DEFAULT 1,
    reported_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_reading_device_code (device_code),
    INDEX idx_device_reading_data_type (data_type),
    INDEX idx_device_reading_reported_at (reported_at)
);

CREATE TABLE IF NOT EXISTS device_simulator_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_code VARCHAR(64) NOT NULL UNIQUE,
    online TINYINT(1) NOT NULL DEFAULT 1,
    numeric_min DOUBLE NULL,
    numeric_max DOUBLE NULL,
    fluctuation DOUBLE NULL,
    switch_value VARCHAR(16) NOT NULL DEFAULT 'off',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_simulator_config_code (device_code)
);

CREATE TABLE IF NOT EXISTS telemetry_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reported_at DATETIME NOT NULL,
    water_temperature DOUBLE NOT NULL,
    ph DOUBLE NOT NULL,
    dissolved_oxygen DOUBLE NOT NULL,
    air_temperature DOUBLE NOT NULL,
    air_humidity DOUBLE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_telemetry_reported_at (reported_at)
);

CREATE TABLE IF NOT EXISTS device_status_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_code VARCHAR(64) NOT NULL,
    device_name VARCHAR(128) NOT NULL,
    device_type VARCHAR(64) NOT NULL,
    online TINYINT(1) NOT NULL,
    power_state VARCHAR(16) NOT NULL,
    reported_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_status_device_code (device_code),
    INDEX idx_device_status_reported_at (reported_at)
);

CREATE TABLE IF NOT EXISTS alarm_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_key VARCHAR(64) NOT NULL,
    metric_label VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'warning',
    message VARCHAR(255) NOT NULL,
    current_value DOUBLE NOT NULL,
    threshold_text VARCHAR(128) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    triggered_at DATETIME NOT NULL,
    resolved_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_alarm_metric_key (metric_key),
    INDEX idx_alarm_status (status),
    INDEX idx_alarm_triggered_at (triggered_at)
);

CREATE TABLE IF NOT EXISTS command_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    command_id VARCHAR(64) NOT NULL UNIQUE,
    device_code VARCHAR(64) NOT NULL,
    action VARCHAR(16) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    source VARCHAR(32) NOT NULL DEFAULT 'web',
    message VARCHAR(255) NULL,
    issued_at DATETIME NOT NULL,
    acknowledged_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_command_device_code (device_code),
    INDEX idx_command_status (status),
    INDEX idx_command_issued_at (issued_at)
);

CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(64) NOT NULL UNIQUE,
    value TEXT NULL,
    label VARCHAR(128) NOT NULL,
    description VARCHAR(255) NULL,
    is_secret TINYINT(1) NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_system_config_key (`key`)
);

CREATE TABLE IF NOT EXISTS ai_chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    model VARCHAR(64) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ai_chat_user_id (user_id),
    INDEX idx_ai_chat_created_at (created_at),
    CONSTRAINT fk_ai_chat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
