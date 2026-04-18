// 中文注释：AI 页负责提交问题、展示 Markdown 回复并维护聊天历史。
(function () {
    const endpoints = window.AI_ENDPOINTS;
    const api = window.AppApi;
    const utils = window.AppUtils;
    const form = document.getElementById("aiChatForm");
    const input = document.getElementById("aiMessageInput");
    const submitButton = document.getElementById("aiSubmitButton");
    const clearButton = document.getElementById("clearAiHistoryButton");
    const messages = document.getElementById("aiMessages");
    const welcomeText = "可以询问：我有几个设备？每个设备当前是什么值？哪些设备离线？";

    function formatInline(text) {
        let html = utils.escapeHtml(text);
        html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
        html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        return html;
    }

    function closeList(state, output) {
        if (!state.type) {
            return;
        }
        output.push(`</${state.type}>`);
        state.type = null;
    }

    function renderMarkdown(message) {
        const lines = String(message ?? "").replace(/\r\n/g, "\n").split("\n");
        const output = [];
        const listState = { type: null };
        let paragraph = [];
        let inCode = false;
        let codeLines = [];
        let codeLang = "";

        function flushParagraph() {
            if (!paragraph.length) {
                return;
            }
            output.push(`<p>${paragraph.map(formatInline).join("<br>")}</p>`);
            paragraph = [];
        }

        lines.forEach((line) => {
            const fenceMatch = line.match(/^```([A-Za-z0-9_-]*)\s*$/);
            if (fenceMatch) {
                if (inCode) {
                    output.push(`<pre><code class="language-${utils.escapeHtml(codeLang)}">${utils.escapeHtml(codeLines.join("\n"))}</code></pre>`);
                    codeLines = [];
                    codeLang = "";
                    inCode = false;
                    return;
                }
                flushParagraph();
                closeList(listState, output);
                inCode = true;
                codeLang = fenceMatch[1] || "";
                return;
            }

            if (inCode) {
                codeLines.push(line);
                return;
            }

            if (!line.trim()) {
                flushParagraph();
                closeList(listState, output);
                return;
            }

            const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
            if (headingMatch) {
                flushParagraph();
                closeList(listState, output);
                const level = headingMatch[1].length;
                output.push(`<h${level}>${formatInline(headingMatch[2])}</h${level}>`);
                return;
            }

            const unorderedMatch = line.match(/^\s*[-*]\s+(.+)$/);
            const orderedMatch = line.match(/^\s*\d+\.\s+(.+)$/);
            if (unorderedMatch || orderedMatch) {
                flushParagraph();
                const targetType = unorderedMatch ? "ul" : "ol";
                if (listState.type !== targetType) {
                    closeList(listState, output);
                    output.push(`<${targetType}>`);
                    listState.type = targetType;
                }
                output.push(`<li>${formatInline((unorderedMatch || orderedMatch)[1])}</li>`);
                return;
            }

            closeList(listState, output);
            paragraph.push(line);
        });

        if (inCode) {
            output.push(`<pre><code class="language-${utils.escapeHtml(codeLang)}">${utils.escapeHtml(codeLines.join("\n"))}</code></pre>`);
        }
        flushParagraph();
        closeList(listState, output);
        return output.join("");
    }

    function renderContent(message, format) {
        if (format === "markdown") {
            return `<div class="ai-markdown">${renderMarkdown(message)}</div>`;
        }
        return utils.escapeHtml(message);
    }

    function appendMessage(side, name, message, timeText, format) {
        const isRight = side === "right";
        const content = renderContent(message, format);
        messages.insertAdjacentHTML("beforeend", `
            <div class="direct-chat-msg ${isRight ? "right" : ""}">
                <div class="direct-chat-infos clearfix">
                    <span class="direct-chat-name ${isRight ? "float-end" : "float-start"}">${utils.escapeHtml(name)}</span>
                    <span class="direct-chat-timestamp ${isRight ? "float-start" : "float-end"}">${utils.escapeHtml(timeText)}</span>
                </div>
                <div class="direct-chat-text" data-ai-message-content>${content}</div>
            </div>
        `);
        messages.scrollTop = messages.scrollHeight;
        return messages.lastElementChild.querySelector("[data-ai-message-content]");
    }

    function updateMessage(contentElement, message, format) {
        contentElement.innerHTML = renderContent(message, format);
        messages.scrollTop = messages.scrollHeight;
    }

    function appendWelcome() {
        appendMessage("left", "系统", welcomeText, utils.formatDateTime(new Date()), "text");
    }

    function setLoading(isLoading) {
        input.disabled = isLoading;
        submitButton.disabled = isLoading;
        submitButton.textContent = isLoading ? "正在思考..." : "发送";
    }

    async function loadHistory() {
        messages.innerHTML = "";
        try {
            const history = await api.getJson(endpoints.historyUrl);
            if (!history.length) {
                appendWelcome();
                return;
            }
            history.forEach((item) => {
                const isUser = item.role === "user";
                appendMessage(
                    isUser ? "right" : "left",
                    isUser ? "我" : "AI 助手",
                    item.content,
                    utils.formatDateTime(item.created_at),
                    isUser ? "text" : "markdown",
                );
            });
        } catch (error) {
            appendMessage("left", "系统", error.message, utils.formatDateTime(new Date()), "text");
        }
    }

    function parseSsePacket(packet) {
        const event = { name: "message", data: "" };
        packet.split("\n").forEach((line) => {
            if (line.startsWith("event:")) {
                event.name = line.slice(6).trim();
            }
            if (line.startsWith("data:")) {
                event.data += line.slice(5).trim();
            }
        });
        if (!event.data) {
            return event;
        }
        try {
            event.payload = JSON.parse(event.data);
        } catch (error) {
            event.payload = { message: "AI 流式响应格式异常。" };
        }
        return event;
    }

    async function submitNormalChat(value) {
        const data = await api.postJson(endpoints.chatUrl, { message: value });
        appendMessage("left", "AI 助手", data.reply, utils.formatDateTime(new Date()), "markdown");
    }

    async function submitStreamChat(value) {
        if (!endpoints.streamChatUrl || !window.ReadableStream) {
            await submitNormalChat(value);
            return;
        }

        const aiContent = appendMessage("left", "AI 助手", "", utils.formatDateTime(new Date()), "markdown");
        const response = await fetch(endpoints.streamChatUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({ message: value }),
        });
        if (!response.ok || !response.body) {
            throw new Error("AI 流式请求失败。");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let reply = "";
        let finished = false;

        while (true) {
            const { value: chunk, done } = await reader.read();
            if (done) {
                break;
            }
            buffer += decoder.decode(chunk, { stream: true });
            const packets = buffer.split("\n\n");
            buffer = packets.pop() || "";

            for (const packet of packets) {
                const event = parseSsePacket(packet);
                if (event.name === "delta") {
                    reply += event.payload.content || "";
                    updateMessage(aiContent, reply, "markdown");
                }
                if (event.name === "done") {
                    finished = true;
                }
                if (event.name === "error") {
                    const message = event.payload.message || "AI 对话失败。";
                    updateMessage(aiContent, message, "text");
                    const error = new Error(message);
                    error.handledInMessage = true;
                    throw error;
                }
            }
        }

        if (buffer.trim()) {
            const event = parseSsePacket(buffer);
            if (event.name === "error") {
                const message = event.payload.message || "AI 对话失败。";
                updateMessage(aiContent, message, "text");
                const error = new Error(message);
                error.handledInMessage = true;
                throw error;
            }
        }
        if (!reply) {
            updateMessage(aiContent, "AI 没有返回内容。", "text");
        }
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        const value = input.value.trim();
        if (!value) {
            return;
        }

        appendMessage("right", "我", value, utils.formatDateTime(new Date()), "text");
        input.value = "";

        try {
            setLoading(true);
            await submitStreamChat(value);
        } catch (error) {
            if (!error.handledInMessage) {
                appendMessage("left", "系统", error.message, utils.formatDateTime(new Date()), "text");
            }
        } finally {
            setLoading(false);
            input.focus();
        }
    });

    clearButton.addEventListener("click", async function () {
        try {
            await api.deleteJson(endpoints.historyUrl);
            messages.innerHTML = "";
            appendWelcome();
        } catch (error) {
            appendMessage("left", "系统", error.message, utils.formatDateTime(new Date()), "text");
        }
    });

    loadHistory();
})();
