// web/static/js/app.js

// 状态管理
let sessionId = null;
let isTyping = false;
let isComposing = false;  // 输入法组合状态

// 生成会话ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 获取或创建会话ID
function getOrCreateSessionId() {
    let storedId = localStorage.getItem('chat_session_id');
    if (storedId) {
        return storedId;
    }
    const newId = generateSessionId();
    localStorage.setItem('chat_session_id', newId);
    return newId;
}

// 保存会话ID
function saveSessionId(id) {
    sessionId = id;
    localStorage.setItem('chat_session_id', id);
}

// DOM元素
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const historyList = document.getElementById('historyList');

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 检查URL参数，是否需要新建对话
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('new') === 'true') {
        // 清除旧会话，创建新会话
        sessionId = generateSessionId();
        localStorage.setItem('chat_session_id', sessionId);
        // 清除URL参数
        window.history.replaceState({}, '', '/');
    } else {
        // 获取或创建会话ID
        sessionId = getOrCreateSessionId();
    }

    // 绑定事件
    sendBtn.addEventListener('click', sendMessage);
    newChatBtn.addEventListener('click', newChat);

    // 输入法组合事件
    messageInput.addEventListener('compositionstart', () => {
        isComposing = true;
    });

    messageInput.addEventListener('compositionend', () => {
        isComposing = false;
    });

    // 回车发送（排除输入法组合状态）
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !isComposing && !e.isComposing) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 自动调整输入框高度
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });

    // 加载历史会话列表
    await loadSessionList();

    // 加载当前会话历史
    await loadHistory();

    // 绑定快捷按钮
    bindQuickButtons();
});

// 绑定快捷按钮
function bindQuickButtons() {
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.dataset.query;
            messageInput.value = query;
            sendMessage();
        });
    });
}

// 加载历史会话列表
async function loadSessionList() {
    try {
        const result = await api.getSessions();
        if (result.sessions && result.sessions.length > 0) {
            renderSessionList(result.sessions);
        }
    } catch (error) {
        console.log('加载会话列表失败:', error);
    }
}

// 渲染会话列表
function renderSessionList(sessions) {
    historyList.innerHTML = '';

    sessions.forEach(session => {
        const li = document.createElement('li');
        li.className = 'history-item' + (session.session_id === sessionId ? ' active' : '');
        li.dataset.sessionId = session.session_id;

        const time = new Date(session.updated_at).toLocaleString('zh-CN', {
            month: 'numeric',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        li.innerHTML = `
            <div class="history-item-title">${session.title || '新对话'}</div>
            <div class="history-item-time">${time}</div>
            <button class="history-item-delete" title="删除对话">✕</button>
        `;

        // 点击切换会话
        li.addEventListener('click', (e) => {
            if (!e.target.classList.contains('history-item-delete')) {
                switchSession(session.session_id);
            }
        });

        // 点击删除
        li.querySelector('.history-item-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSession(session.session_id);
        });

        historyList.appendChild(li);
    });
}

// 删除会话
async function deleteSession(targetSessionId) {
    if (!confirm('确定要删除这个对话吗？')) return;

    try {
        await api.clearHistory(targetSessionId);

        // 如果删除的是当前会话，新建一个
        if (targetSessionId === sessionId) {
            newChat();
        }

        // 刷新列表
        await loadSessionList();
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

// 切换会话
async function switchSession(targetSessionId) {
    saveSessionId(targetSessionId);
    messagesContainer.innerHTML = '';

    // 重新加载历史
    await loadHistory();
    await loadSessionList();
}

// 加载历史记录
async function loadHistory() {
    try {
        const result = await api.getHistory(sessionId);
        if (result.history && result.history.length > 0) {
            // 有历史记录，隐藏欢迎消息
            const welcomeMsg = document.querySelector('.welcome-message');
            if (welcomeMsg) welcomeMsg.remove();

            result.history.forEach(msg => {
                appendMessage(msg.role, msg.content);
            });
        }
    } catch (error) {
        console.log('加载历史失败:', error);
    }
}

// 发送消息（流式）
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isTyping) return;

    // 清空输入
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // 隐藏欢迎消息
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    // 显示用户消息
    appendMessage('user', message);

    // 显示加载状态
    isTyping = true;
    sendBtn.disabled = true;

    // 创建助手消息容器（带光标）
    const assistantMsg = createStreamingMessage();

    try {
        // 使用流式API
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // 解码并添加到缓冲区
            buffer += decoder.decode(value, { stream: true });

            // 按双换行分割消息
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || ''; // 保留最后一个不完整的部分

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'session') {
                            saveSessionId(data.session_id);
                        } else if (data.type === 'rag_info') {
                            showRagDebug(assistantMsg, data.rag_info);
                        } else if (data.type === 'content') {
                            fullResponse += data.content;
                            updateStreamingMessage(assistantMsg, fullResponse);
                        } else if (data.type === 'done') {
                            // 完成，移除光标
                            removeCursor(assistantMsg);
                        } else if (data.type === 'error') {
                            updateStreamingMessage(assistantMsg, '抱歉，发生了错误：' + data.message);
                        }
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        }

        // 刷新会话列表
        await loadSessionList();

    } catch (error) {
        removeCursor(assistantMsg);
        updateStreamingMessage(assistantMsg, '抱歉，发生了错误，请稍后重试。');
        console.error('Chat error:', error);
    } finally {
        isTyping = false;
        sendBtn.disabled = false;
    }
}

// 创建流式消息容器（带光标动画）
function createStreamingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    messageDiv.innerHTML = `
        <div class="message-avatar">K</div>
        <div class="message-content">
            <div class="rag-debug" style="display: none;"></div>
            <span class="streaming-text"></span><span class="cursor">▊</span>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

// 更新流式消息
function updateStreamingMessage(messageDiv, content) {
    const contentSpan = messageDiv.querySelector('.streaming-text');
    if (contentSpan) {
        contentSpan.innerHTML = renderMarkdown(content);
        scrollToBottom();
    }
}

// 显示RAG调试信息
function showRagDebug(messageDiv, ragInfo) {
    const debugDiv = messageDiv.querySelector('.rag-debug');
    if (!debugDiv || !ragInfo) return;

    if (ragInfo.total === 0) {
        debugDiv.innerHTML = `<span class="rag-debug-label">📚 知识库检索: 无相关结果</span>`;
    } else {
        const resultsHtml = ragInfo.results.map(r =>
            `<span class="rag-debug-item" title="${r.preview}">${r.source} (${r.score})</span>`
        ).join('');

        debugDiv.innerHTML = `
            <span class="rag-debug-label">📚 知识库检索: ${ragInfo.total}条结果</span>
            <div class="rag-debug-results">${resultsHtml}</div>
        `;
    }

    debugDiv.style.display = 'block';
}

// 移除光标
function removeCursor(messageDiv) {
    const cursor = messageDiv.querySelector('.cursor');
    if (cursor) cursor.remove();
}

// 添加消息
function appendMessage(role, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '我' : 'K';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // 渲染Markdown
    if (role === 'assistant') {
        contentDiv.innerHTML = renderMarkdown(content);
    } else {
        contentDiv.textContent = content;
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

// 更新消息内容（用于流式更新）
function updateMessage(messageDiv, content) {
    const contentDiv = messageDiv.querySelector('.message-content');
    if (contentDiv) {
        contentDiv.innerHTML = renderMarkdown(content);
        scrollToBottom();
    }
}

// 新建对话
function newChat() {
    const newId = generateSessionId();
    saveSessionId(newId);

    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🎓</div>
            <h2>你好，我是K12学习助手</h2>
            <p>我可以帮你解答学科问题、辅导作业、疏导情绪</p>
            <div class="quick-actions">
                <button class="quick-btn" data-query="请帮我讲解勾股定理">
                    📐 勾股定理讲解
                </button>
                <button class="quick-btn" data-query="这道方程题怎么做：2x + 5 = 13">
                    📝 作业辅导
                </button>
                <button class="quick-btn" data-query="最近学习压力有点大">
                    💬 情绪疏导
                </button>
            </div>
        </div>
    `;

    bindQuickButtons();
    loadSessionList();
}

// 滚动到底部
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
