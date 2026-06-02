// web/static/js/app.js

// 状态管理
let sessionId = generateSessionId();
let isTyping = false;

// 生成会话ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// DOM元素
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const clearBtn = document.getElementById('clearBtn');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
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

    // 快捷操作按钮
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.dataset.query;
            messageInput.value = query;
            sendMessage();
        });
    });

    // 自动调整输入框高度
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
});

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
        sessionId = response.session_id;

        // 移除加载动画
        removeLoading(loadingId);

        // 显示助手回复
        appendMessage('assistant', response.response, {
            intent: response.intent
        });

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
    sessionId = generateSessionId();
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

    // 重新绑定快捷按钮事件
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.dataset.query;
            messageInput.value = query;
            sendMessage();
        });
    });
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
