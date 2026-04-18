// 中文注释：控制页只拼装框架卡片和按钮，并调用后端控制接口。
(function () {
    const endpoints = window.CONTROL_ENDPOINTS;
    const api = window.AppApi;
    const utils = window.AppUtils;
    const socket = window.AppSocket;

    const alertContainer = document.getElementById("controlAlert");
    const deviceCards = document.getElementById("controlDeviceCards");
    const commandTableBody = document.getElementById("controlCommandTableBody");

    function statusText(value) {
        if (value === "success") {
            return "执行成功";
        }
        if (value === "failed") {
            return "执行失败";
        }
        return "等待回执";
    }

    function statusClass(value) {
        if (value === "success") {
            return "text-bg-success";
        }
        if (value === "failed") {
            return "text-bg-danger";
        }
        return "text-bg-warning";
    }

    function showAlert(message, level) {
        alertContainer.innerHTML = `
            <div class="alert alert-${level} alert-dismissible fade show" role="alert">
                ${utils.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
            </div>
        `;
    }

    function readingText(item) {
        const reading = item.latest_reading;
        if (!reading || !reading.online) {
            return "离线";
        }
        return reading.switch_value === "on" ? "开启" : "关闭";
    }

    function renderDevices(items) {
        const switchDevices = (items || []).filter((item) => item.data_type === "switch");
        if (!switchDevices.length) {
            deviceCards.innerHTML = '<div class="col-12"><div class="alert alert-info">暂无可控制的开关型设备</div></div>';
            return;
        }
        deviceCards.innerHTML = switchDevices.map((item) => `
            <div class="col-lg-3 col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">${utils.escapeHtml(item.name)}</h3>
                        <div class="card-tools d-flex gap-2">
                            <span class="badge ${item.online ? 'text-bg-success' : 'text-bg-secondary'}">${item.online ? '在线' : '离线'}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="text-body-secondary small mb-3">${utils.escapeHtml(item.description || '')}</p>
                        <p class="fw-semibold">当前状态：${readingText(item)}</p>
                        <div class="btn-group w-100" role="group">
                            <button type="button" class="btn btn-success" data-action="on" data-device="${utils.escapeHtml(item.code)}" ${item.online ? '' : 'disabled'}>开启</button>
                            <button type="button" class="btn btn-outline-secondary" data-action="off" data-device="${utils.escapeHtml(item.code)}" ${item.online ? '' : 'disabled'}>关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `).join("");

        deviceCards.querySelectorAll("[data-action]").forEach((button) => {
            button.addEventListener("click", async function () {
                const action = button.dataset.action;
                const deviceCode = button.dataset.device;
                const url = endpoints.controlUrlTemplate.replace("__DEVICE__", deviceCode);
                try {
                    const data = await api.postJson(url, { action });
                    showAlert(`${deviceCode}：${data.message}`, data.status === "failed" ? "danger" : "success");
                    loadCommands();
                } catch (error) {
                    showAlert(error.message, "danger");
                }
            });
        });
    }

    function renderCommands(items) {
        if (!items || !items.length) {
            commandTableBody.innerHTML = '<tr><td colspan="7" class="text-center text-body-secondary">暂无控制记录</td></tr>';
            return;
        }
        commandTableBody.innerHTML = items.map((item) => `
            <tr>
                <td class="small">${utils.escapeHtml(item.command_id)}</td>
                <td>${utils.escapeHtml(item.device_code)}</td>
                <td>${item.action === 'on' ? '开启' : '关闭'}</td>
                <td><span class="badge ${statusClass(item.status)}">${statusText(item.status)}</span></td>
                <td>${utils.escapeHtml(item.message || '')}</td>
                <td>${utils.formatDateTime(item.issued_at)}</td>
                <td>${utils.formatDateTime(item.acknowledged_at)}</td>
            </tr>
        `).join("");
    }

    async function loadDevices() {
        const data = await api.getJson(endpoints.devicesUrl);
        renderDevices(data);
    }

    async function loadCommands() {
        const data = await api.getJson(`${endpoints.commandsUrl}?limit=12`);
        renderCommands(data);
    }

    if (socket) {
        socket.on("device_status_changed", loadDevices);
        socket.on("command_feedback", function (payload) {
            const command = payload.command || {};
            if (command.status === "success") {
                showAlert(`${command.device_code} 执行成功：${command.message}`, "success");
            } else if (command.status === "failed") {
                showAlert(`${command.device_code} 执行失败：${command.message}`, "danger");
            }
            loadCommands();
            loadDevices();
        });
    }

    Promise.all([loadDevices(), loadCommands()]).catch((error) => showAlert(error.message, "danger"));
})();
