// 中文注释：监控页只负责渲染现有卡片、表格与图表内容。
(function () {
    const endpoints = window.DASHBOARD_ENDPOINTS;
    const utils = window.AppUtils;
    const api = window.AppApi;
    const socket = window.AppSocket;

    const metricCards = document.getElementById("metricCards");
    const alarmTableBody = document.getElementById("alarmTableBody");
    const deviceStatusList = document.getElementById("deviceStatusList");
    const commandTableBody = document.getElementById("commandTableBody");
    const updatedAt = document.getElementById("dashboardUpdatedAt");
    const metricSelect = document.getElementById("historyMetricSelect");
    const statDeviceTotal = document.getElementById("statDeviceTotal");
    const statDeviceOnline = document.getElementById("statDeviceOnline");
    const statAlarmTotal = document.getElementById("statAlarmTotal");

    let chart = null;

    function severityClass(value) {
        return value === "danger" ? "text-bg-danger" : "text-bg-success";
    }

    function renderMetricCards(items) {
        metricCards.innerHTML = (items || []).map((item) => `
            <div class="col-xl col-md-4 col-sm-6">
                <div class="small-box ${severityClass(item.severity)}">
                    <div class="inner">
                        <h3>${utils.escapeHtml(item.display_value)}</h3>
                        <p>${utils.escapeHtml(item.label)}</p>
                    </div>
                    <div class="icon"><i class="fas fa-wave-square"></i></div>
                </div>
            </div>
        `).join("");
    }

    function renderHistoryOptions(deviceCards) {
        const currentValue = metricSelect.value;
        const numericCards = (deviceCards || []).filter((item) => item.data_type === "numeric");
        metricSelect.innerHTML = "";
        numericCards.forEach((item) => {
            const option = document.createElement("option");
            option.value = item.key;
            option.textContent = item.label;
            metricSelect.appendChild(option);
        });
        if (Array.from(metricSelect.options).some((item) => item.value === currentValue)) {
            metricSelect.value = currentValue;
        } else if (metricSelect.options.length) {
            metricSelect.value = metricSelect.options[0].value;
        }
        metricSelect.disabled = metricSelect.options.length === 0;
    }

    function deviceReadingText(item) {
        const reading = item.latest_reading;
        if (!reading) {
            return "--";
        }
        if (!reading.online) {
            return "离线";
        }
        if (item.data_type === "switch") {
            return reading.switch_value === "on" ? "开启" : "关闭";
        }
        if (reading.numeric_value === null || reading.numeric_value === undefined) {
            return "--";
        }
        return `${Number(reading.numeric_value).toFixed(2)} ${item.unit || ""}`.trim();
    }

    function renderDevices(items) {
        if (!items || !items.length) {
            deviceStatusList.innerHTML = '<li class="list-group-item text-body-secondary">暂无设备数据</li>';
            return;
        }
        deviceStatusList.innerHTML = items.map((item) => `
            <li class="list-group-item">
                <div class="d-flex justify-content-between align-items-start gap-2">
                    <div>
                            <div class="fw-semibold">${utils.escapeHtml(item.name)}</div>
                            <div class="text-body-secondary small">${utils.escapeHtml(deviceReadingText(item))}</div>
                    </div>
                    <div class="d-flex gap-2">
                        <span class="badge ${item.online ? 'text-bg-success' : 'text-bg-secondary'}">${item.online ? '在线' : '离线'}</span>
                    </div>
                </div>
            </li>
        `).join("");
    }

    function renderAlarms(items) {
        if (!items || !items.length) {
            alarmTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-body-secondary">当前无活动告警</td></tr>';
            return;
        }
        alarmTableBody.innerHTML = items.map((item) => `
            <tr>
                <td><span class="badge text-bg-danger">${utils.escapeHtml(item.metric_label)}</span></td>
                <td>${utils.escapeHtml(item.message)}</td>
                <td>${utils.escapeHtml(item.threshold_text)}</td>
                <td>${utils.formatDateTime(item.triggered_at)}</td>
            </tr>
        `).join("");
    }

    function renderCommands(items) {
        if (!items || !items.length) {
            commandTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-body-secondary">暂无控制记录</td></tr>';
            return;
        }
        commandTableBody.innerHTML = items.map((item) => `
            <tr>
                <td class="small">${utils.escapeHtml(item.command_id)}</td>
                <td>${utils.escapeHtml(item.device_code)}</td>
                <td>${item.action === 'on' ? '开启' : '关闭'}</td>
                <td><span class="badge ${item.status === 'success' ? 'text-bg-success' : item.status === 'failed' ? 'text-bg-danger' : 'text-bg-warning'}">${utils.escapeHtml(item.status)}</span></td>
                <td>${utils.escapeHtml(item.message || '')}</td>
                <td>${utils.formatDateTime(item.issued_at)}</td>
            </tr>
        `).join("");
    }

    function renderStats(summary) {
        const totals = summary.device_totals || {};
        statDeviceTotal.textContent = totals.total || 0;
        statDeviceOnline.textContent = totals.online || 0;
        statAlarmTotal.textContent = totals.alarms || 0;
        updatedAt.textContent = `最近刷新：${utils.formatDateTime(summary.generated_at)}`;
    }

    function renderSummary(summary) {
        const cards = summary.dashboard_cards || summary.device_reading_cards || [];
        renderMetricCards(cards);
        renderHistoryOptions(summary.device_reading_cards || []);
        renderDevices(summary.devices || []);
        renderAlarms(summary.active_alarms || []);
        renderCommands(summary.recent_commands || []);
        renderStats(summary);
    }

    function ensureChart() {
        if (!chart) {
            chart = echarts.init(document.getElementById("historyChart"));
        }
        return chart;
    }

    async function loadHistory() {
        if (!metricSelect.value) {
            ensureChart().clear();
            ensureChart().setOption({
                title: {
                    text: "暂无数值型设备可查看趋势",
                    left: "center",
                    top: "middle",
                    textStyle: { color: "#6c757d", fontSize: 16 },
                },
            });
            return;
        }
        const metric = metricSelect.value;
        const data = await api.getJson(`${endpoints.historyUrl}?metric=${encodeURIComponent(metric)}&hours=12&limit=80`);
        ensureChart().setOption({
            tooltip: { trigger: "axis" },
            grid: { left: 48, right: 16, top: 24, bottom: 32 },
            xAxis: {
                type: "category",
                data: data.items.map((item) => utils.formatDateTime(item.reported_at)),
            },
            yAxis: {
                type: "value",
                name: data.unit || "",
            },
            series: [
                {
                    type: "line",
                    smooth: true,
                    data: data.items.map((item) => item.value),
                    areaStyle: {},
                    name: data.label,
                },
            ],
        });
    }

    async function loadSummary() {
        const data = await api.getJson(endpoints.summaryUrl);
        renderSummary(data);
    }

    metricSelect.addEventListener("change", function () {
        loadHistory().catch(console.error);
    });

    if (socket) {
        socket.on("dashboard_snapshot", renderSummary);
        socket.on("alarm_changed", function (payload) {
            renderAlarms(payload.items || []);
        });
    }

    loadSummary().then(loadHistory).catch(console.error);
    window.addEventListener("resize", function () {
        if (chart) {
            chart.resize();
        }
    });
})();
