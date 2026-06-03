// web/static/js/api.js

const API_BASE = '/api';

// API调用封装
const api = {
    // 发送消息
    async chat(message, sessionId = null) {
        const response = await fetch(`${API_BASE}/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                session_id: sessionId
            })
        });
        return response.json();
    },

    // 获取对话历史
    async getHistory(sessionId) {
        const response = await fetch(`${API_BASE}/chat/history/${sessionId}`);
        return response.json();
    },

    // 获取会话列表
    async getSessions(limit = 20) {
        const response = await fetch(`${API_BASE}/chat/sessions?limit=${limit}`);
        return response.json();
    },

    // 清空历史
    async clearHistory(sessionId) {
        const response = await fetch(`${API_BASE}/chat/history/${sessionId}`, {
            method: 'DELETE'
        });
        return response.json();
    },

    // 上传文档
    async uploadDocument(formData) {
        const response = await fetch(`${API_BASE}/knowledge/upload`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    },

    // 获取文档列表
    async getDocuments(subject = null) {
        let url = `${API_BASE}/knowledge/list`;
        if (subject) url += `?subject=${encodeURIComponent(subject)}`;
        const response = await fetch(url);
        return response.json();
    },

    // 删除文档
    async deleteDocument(docId) {
        const response = await fetch(`${API_BASE}/knowledge/${docId}`, {
            method: 'DELETE'
        });
        return response.json();
    },

    // 获取统计
    async getStats() {
        const response = await fetch(`${API_BASE}/knowledge/stats`);
        return response.json();
    },

    // 获取文档切片
    async getChunks(docId) {
        const response = await fetch(`${API_BASE}/knowledge/chunks/${docId}`);
        return response.json();
    }
};
