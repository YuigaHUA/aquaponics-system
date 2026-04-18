// 中文注释：设备页负责展示表格、详情和设备维护表单。
(function () {
    const endpoints = window.DEVICE_ENDPOINTS;
    const api = window.AppApi;
    const utils = window.AppUtils;
    const socket = window.AppSocket;

    const alertContainer = document.getElementById("deviceAlert");
    const tableBody = document.getElementById("devicesTableBody");
    const detailModal = new bootstrap.Modal(document.getElementById("deviceDetailModal"));
    const formModal = new bootstrap.Modal(document.getElementById("deviceFormModal"));
    const form = document.getElementById("deviceForm");
    const formTitle = document.getElementById("deviceFormTitle");
    let devices = [];

    const fields = {
        code: document.getElementById("detailCode"),
        name: document.getElementById("detailName"),
        type: document.getElementById("detailType"),
        online: document.getElementById("detailOnline"),
        reading: document.getElementById("detailReading"),
        reportedAt: document.getElementById("detailReportedAt"),
        description: document.getElementById("detailDescription"),
    };
    const formFields = {
        code: document.getElementById("deviceCode"),
        name: document.getElementById("deviceName"),
        type: document.getElementById("deviceType"),
        dataType: document.getElementById("deviceDataType"),
        unit: document.getElementById("deviceUnit"),
        thresholdMin: document.getElementById("thresholdMin"),
        thresholdMax: document.getElementById("thresholdMax"),
        description: document.getElementById("deviceDescription"),
    };

    function showAlert(message, level) {
        alertContainer.innerHTML = `
            <div class="alert alert-${level} alert-dismissible fade show" role="alert">
                ${utils.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
            </div>
        `;
    }

    function deviceUrl(code) {
        return endpoints.detailUrlTemplate.replace("__DEVICE__", encodeURIComponent(code));
    }

    function openForm(device) {
        form.reset();
        formFields.code.value = device ? device.code : "";
        formFields.name.value = device ? device.name : "";
        formFields.type.value = device ? device.device_type : "";
        formFields.dataType.value = device ? device.data_type : "numeric";
        formFields.unit.value = device ? device.unit : "";
        formFields.thresholdMin.value = device && device.threshold_min !== null ? device.threshold_min : "";
        formFields.thresholdMax.value = device && device.threshold_max !== null ? device.threshold_max : "";
        formFields.description.value = device ? device.description : "";
        formFields.code.disabled = Boolean(device);
        toggleThresholdFields();
        formTitle.textContent = device ? "编辑设备" : "新增设备";
        formModal.show();
    }

    function toggleThresholdFields() {
        const isNumeric = formFields.dataType.value === "numeric";
        formFields.unit.disabled = !isNumeric;
        formFields.thresholdMin.disabled = !isNumeric;
        formFields.thresholdMax.disabled = !isNumeric;
        if (!isNumeric) {
            formFields.unit.value = "";
            formFields.thresholdMin.value = "";
            formFields.thresholdMax.value = "";
        }
    }

    function collectPayload() {
        return {
            code: formFields.code.value,
            name: formFields.name.value,
            device_type: formFields.type.value,
            data_type: formFields.dataType.value,
            unit: formFields.unit.value,
            threshold_min: formFields.thresholdMin.value,
            threshold_max: formFields.thresholdMax.value,
            description: formFields.description.value,
        };
    }

    function formatReading(item) {
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

    function formatThreshold(item) {
        if (item.data_type !== "numeric") {
            return "--";
        }
        if (item.threshold_min !== null && item.threshold_max !== null) {
            return `${item.threshold_min} - ${item.threshold_max} ${item.unit || ""}`.trim();
        }
        if (item.threshold_min !== null) {
            return `>= ${item.threshold_min} ${item.unit || ""}`.trim();
        }
        if (item.threshold_max !== null) {
            return `<= ${item.threshold_max} ${item.unit || ""}`.trim();
        }
        return "未设置";
    }

    async function showDetail(deviceCode) {
        const detail = await api.getJson(deviceUrl(deviceCode));
        fields.code.textContent = detail.code || "--";
        fields.name.textContent = detail.name || "--";
        fields.type.textContent = detail.device_type || "--";
        fields.online.textContent = detail.online ? "在线" : "离线";
        fields.reading.textContent = formatReading(detail);
        fields.reportedAt.textContent = utils.formatDateTime(detail.last_reported_at);
        fields.description.textContent = detail.description || "--";
        detailModal.show();
    }

    function renderTable(items) {
        if (!items || !items.length) {
            tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-body-secondary">暂无设备数据</td></tr>';
            return;
        }

        tableBody.innerHTML = items.map((item) => `
            <tr>
                <td>${utils.escapeHtml(item.code)}</td>
                <td>${utils.escapeHtml(item.name)}</td>
                <td>${utils.escapeHtml(item.device_type)}</td>
                <td>${item.data_type === 'numeric' ? '数值型' : '开关型'}</td>
                <td>${utils.escapeHtml(formatThreshold(item))}</td>
                <td><span class="badge ${item.online ? 'text-bg-success' : 'text-bg-secondary'}">${item.online ? '在线' : '离线'}</span></td>
                <td>${utils.escapeHtml(formatReading(item))}</td>
                <td>${utils.formatDateTime(item.last_reported_at)}</td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary" data-view-device="${utils.escapeHtml(item.code)}">详情</button>
                        <button type="button" class="btn btn-outline-secondary" data-edit-device="${utils.escapeHtml(item.code)}">编辑</button>
                        <button type="button" class="btn btn-outline-danger" data-delete-device="${utils.escapeHtml(item.code)}">删除</button>
                    </div>
                </td>
            </tr>
        `).join("");

        tableBody.querySelectorAll("[data-view-device]").forEach((button) => {
            button.addEventListener("click", function () {
                showDetail(button.dataset.viewDevice).catch((error) => showAlert(error.message, "danger"));
            });
        });
        tableBody.querySelectorAll("[data-edit-device]").forEach((button) => {
            button.addEventListener("click", function () {
                const device = devices.find((item) => item.code === button.dataset.editDevice);
                openForm(device);
            });
        });
        tableBody.querySelectorAll("[data-delete-device]").forEach((button) => {
            button.addEventListener("click", async function () {
                if (!window.confirm("确认删除该设备吗？相关状态和命令记录也会删除。")) {
                    return;
                }
                try {
                    await api.deleteJson(deviceUrl(button.dataset.deleteDevice));
                    showAlert("设备已删除", "success");
                    await loadDevices();
                } catch (error) {
                    showAlert(error.message, "danger");
                }
            });
        });
    }

    async function loadDevices() {
        devices = await api.getJson(endpoints.devicesUrl);
        renderTable(devices);
    }

    document.getElementById("addDeviceButton").addEventListener("click", function () {
        openForm(null);
    });

    formFields.dataType.addEventListener("change", toggleThresholdFields);

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        const payload = collectPayload();
        try {
            if (formFields.code.disabled) {
                await api.putJson(deviceUrl(formFields.code.value), payload);
                showAlert("设备已更新", "success");
            } else {
                await api.postJson(endpoints.devicesUrl, payload);
                showAlert("设备已创建", "success");
            }
            formModal.hide();
            await loadDevices();
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });

    if (socket) {
        socket.on("device_status_changed", loadDevices);
    }

    loadDevices().catch((error) => showAlert(error.message, "danger"));
})();
