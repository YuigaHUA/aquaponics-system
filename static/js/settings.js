// 中文注释：系统配置页负责渲染固定配置项并保存到后端。
(function () {
    const endpoints = window.SETTINGS_ENDPOINTS;
    const api = window.AppApi;
    const utils = window.AppUtils;

    const alertContainer = document.getElementById("settingsAlert");
    const fieldsContainer = document.getElementById("settingsFields");
    const form = document.getElementById("settingsForm");

    function showAlert(message, level) {
        alertContainer.innerHTML = `
            <div class="alert alert-${level} alert-dismissible fade show" role="alert">
                ${utils.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
            </div>
        `;
    }

    function renderFields(items) {
        fieldsContainer.innerHTML = (items || []).map((item) => {
            const type = item.is_secret ? "password" : "text";
            const value = item.is_secret ? "" : item.value;
            const placeholder = item.is_secret && item.value ? "已保存，留空表示不修改" : "";
            return `
                <div class="col-md-6">
                    <label class="form-label" for="config_${utils.escapeHtml(item.key)}">${utils.escapeHtml(item.label)}</label>
                    <input type="${type}" class="form-control" id="config_${utils.escapeHtml(item.key)}"
                           name="${utils.escapeHtml(item.key)}" value="${utils.escapeHtml(value)}"
                           placeholder="${utils.escapeHtml(placeholder)}">
                    <div class="form-text">${utils.escapeHtml(item.description || '')}</div>
                </div>
            `;
        }).join("");
    }

    async function loadConfigs() {
        const data = await api.getJson(endpoints.configsUrl);
        renderFields(data);
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        const payload = {};
        new FormData(form).forEach((value, key) => {
            payload[key] = value;
        });
        try {
            const data = await api.putJson(endpoints.configsUrl, payload);
            renderFields(data);
            showAlert("系统配置已保存，部分配置需重启后生效。", "success");
        } catch (error) {
            showAlert(error.message, "danger");
        }
    });

    loadConfigs().catch((error) => showAlert(error.message, "danger"));
})();
