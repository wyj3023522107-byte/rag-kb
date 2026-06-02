// web/static/js/app.js

// 状态管理
let sessionId = null;
let isTyping = false;

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
const clearBtn = document.getElementById('clearBtn');
const historyList = document.getElementById('historyList');

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 获取或创建会话ID
    sessionId = getOrCreateSessionId();

    // 绑定事件
    sendBtn.addEventListener('click', sendMessage);
    newChatBtn.addEventListener('click', newChat);
    clearBtn.addEventListener('click', clearChat);

    // 回车发送
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
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
            <div class="history-content">
                <span class="history-title">${session.title || '新对话'}</span>
                <span class="history-time">${time}</span>
            </div>
            <button class="history-delete" title="删除对话">🗑️</button>
        `;

        // 点击切换会话
        li.querySelector('.history-content').addEventListener('click', () => switchSession(session.session_id));

        // 点击删除
        li.querySelector('.history-delete').addEventListener('click', (e) => {
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

// 发送消息
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
    const loadingId = appendLoading();

    try {
        // 发送请求
        const response = await api.chat(message, sessionId);

        // 保存服务器返回的session_id
        saveSessionId(response.session_id);

        // 移除加载动画
        removeLoading(loadingId);

        // 显示助手回复
        appendMessage('assistant', response.response, {
            intent: response.intent
        });

        // 刷新会话列表
        await loadSessionList();

    } catch (error) {
        removeLoading(loadingId);
        appendMessage('assistant', '抱歉，发生了错误，请稍后重试。');
        console.error('Chat error:', error);
    } finally {
        isTyping = false;
        sendBtn.disabled = false;
    }
}

// 添加消息
function appendMessage(role, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';

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

// 添加加载动画
function appendLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loading-' + Date.now();

    loadingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;

    messagesContainer.appendChild(loadingDiv);
    scrollToBottom();

    return loadingDiv.id;
}

// 移除加载动画
function removeLoading(loadingId) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) loadingDiv.remove();
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
                    ✏️ 作业辅导
                </button>
                <button class="quick-btn" data-query="最近学习压力有点大">
                    💚 情绪疏导
                </button>
            </div>
        </div>
    `;

    bindQuickButtons();
    loadSessionList();
}

// 清空对话
async function clearChat() {
    if (confirm('确定要清空对话吗？')) {
        await api.clearHistory(sessionId);
        newChat();
    }
}

// 滚动到底部
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
