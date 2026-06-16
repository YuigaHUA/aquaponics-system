// Simulator config page renders different inputs by device type.
(function () {
    const endpoints = window.SIMULATOR_ENDPOINTS;
    const api = window.AppApi;
    const utils = window.AppUtils;

    const alertContainer = document.getElementById("simulatorAlert");
    const tableBody = document.getElementById("simulatorConfigBody");
    const form = document.getElementById("simulatorForm");
    let rows = [];

    function showAlert(message, level) {
        alertContainer.innerHTML = `
            <div class="alert alert-${level} alert-dismissible fade show" role="alert">
                ${utils.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }

    function renderRows() {
        if (!rows.length) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-body-secondary">No devices available</td></tr>';
            return;
        }
        tableBody.innerHTML = rows.map((row) => {
            const device = row.device;
            const config = row.config;
            const numericDisabled = device.data_type === "numeric" ? "" : "disabled";
            const switchDisabled = device.data_type === "switch" ? "" : "disabled";
            return `
                <tr data-device-code="${utils.escapeHtml(device.code)}">
                    <td>
                        <div class="fw-semibold">${utils.escapeHtml(device.name)}</div>
                        <div class="small text-body-secondary">${utils.escapeHtml(device.code)}</div>
                    </td>
                    <td>${device.data_type === "numeric" ? "Numeric" : "Switch"}</td>
                    <td>
                        <select class="form-select form-select-sm" data-field="online">
                            <option value="true" ${config.online ? "selected" : ""}>Online</option>
                            <option value="false" ${!config.online ? "selected" : ""}>Offline</option>
                        </select>
                    </td>
                    <td><input type="number" step="0.01" class="form-control form-control-sm" data-field="numeric_min" value="${config.numeric_min ?? ''}" ${numericDisabled}></td>
                    <td><input type="number" step="0.01" class="form-control form-control-sm" data-field="numeric_max" value="${config.numeric_max ?? ''}" ${numericDisabled}></td>
                    <td><input type="number" step="0.01" class="form-control form-control-sm" data-field="fluctuation" value="${config.fluctuation ?? ''}" ${numericDisabled}></td>
                    <td>
                        <select class="form-select form-select-sm" data-field="switch_value" ${switchDisabled}>
                            <option value="on" ${config.switch_value === "on" ? "selected" : ""}>On</option>
                            <option value="off" ${config.switch_value !== "on" ? "selected" : ""}>Off</option>
                        </select>
                    </td>
                </tr>
            `;
        }).join("");
    }

    async function loadConfigs() {
        rows = await api.getJson(endpoints.configsUrl);
        renderRows();
    }

    function collectRows() {
        return Array.from(tableBody.querySelectorAll("tr[data-device-code]")).map((row) => {
            const valueOf = (field) => row.querySelector(`[data-field="${field}"]`)?.value;
            return {
                device_code: row.dataset.deviceCode,
                online: valueOf("online") === "true",
                numeric_min: valueOf("numeric_min"),
                numeric_max: valueOf("numeric_max"),
                fluctuation: valueOf("fluctuation"),
                switch_value: valueOf("switch_value") || "off",
            };
        });
    }

    document.getElementById("reloadSimulatorButton").addEventListener("click", function () {
        loadConfigs().catch((error) => showAlert(error.message, "danger"));
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        try {
            rows = await api.putJson(endpoints.configsUrl, { items: collectRows() });
            renderRows();
            showAlert("Simulator config saved and restarted.", "success");
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });

    loadConfigs().catch((error) => showAlert(error.message, "danger"));
})();
