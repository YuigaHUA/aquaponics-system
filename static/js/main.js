// 中文注释：统一放置轻量业务工具和全局格式化逻辑。
(function () {
    function formatDateTime(value) {
        if (!value) {
            return "--";
        }
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        return new Intl.DateTimeFormat("zh-CN", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        }).format(date);
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    async function getJson(url) {
        const response = await fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        const payload = await response.json();
        if (!response.ok || payload.code !== 0) {
            throw new Error(payload.error || payload.message || "请求失败");
        }
        return payload.data;
    }

    async function postJson(url, body) {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify(body || {}),
        });
        const payload = await response.json();
        if (!response.ok || payload.code !== 0) {
            throw new Error(payload.error || payload.message || "请求失败");
        }
        return payload.data;
    }

    async function putJson(url, body) {
        const response = await fetch(url, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify(body || {}),
        });
        const payload = await response.json();
        if (!response.ok || payload.code !== 0) {
            throw new Error(payload.error || payload.message || "请求失败");
        }
        return payload.data;
    }

    async function deleteJson(url) {
        const response = await fetch(url, {
            method: "DELETE",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        const payload = await response.json();
        if (!response.ok || payload.code !== 0) {
            throw new Error(payload.error || payload.message || "请求失败");
        }
        return payload.data;
    }

    window.AppApi = {
        getJson,
        postJson,
        putJson,
        deleteJson,
    };
    window.AppUtils = {
        escapeHtml,
        formatDateTime,
    };
    window.AppSocket = window.io ? window.io() : null;
})();
