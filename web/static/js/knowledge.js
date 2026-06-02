// web/static/js/knowledge.js

// DOM元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');
const uploadBtn = document.getElementById('uploadBtn');
const subjectSelect = document.getElementById('subjectSelect');
const gradeSelect = document.getElementById('gradeSelect');
const titleInput = document.getElementById('titleInput');
const documentsList = document.getElementById('documentsList');
const filterSubject = document.getElementById('filterSubject');
const totalDocs = document.getElementById('totalDocs');
const totalChunks = document.getElementById('totalChunks');
const storageSize = document.getElementById('storageSize');
const subjectStats = document.getElementById('subjectStats');

let selectedFile = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 新建对话按钮 - 清除旧会话ID
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('chat_session_id');
            window.location.href = '/';
        });
    }

    // 上传区域点击
    uploadArea.addEventListener('click', () => fileInput.click());

    // 文件选择
    fileInput.addEventListener('change', handleFileSelect);

    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // 上传按钮
    uploadBtn.addEventListener('click', uploadDocument);

    // 学科筛选
    filterSubject.addEventListener('change', loadDocuments);

    // 加载数据
    loadDocuments();
    loadStats();
});

// 处理文件选择
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// 处理文件
function handleFile(file) {
    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.md'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(fileExt)) {
        alert('不支持的文件类型，请上传 PDF, Word, TXT 或 Markdown 文件');
        return;
    }

    selectedFile = file;
    uploadArea.style.display = 'none';
    uploadForm.style.display = 'block';
    titleInput.value = file.name.replace(/\.[^/.]+$/, '');
}

// 上传文档
async function uploadDocument() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('subject', subjectSelect.value);
    formData.append('title', titleInput.value || selectedFile.name);

    // 获取选中的年级
    const selectedGrades = Array.from(gradeSelect.selectedOptions).map(opt => opt.value);
    selectedGrades.forEach(grade => formData.append('grade', grade));

    uploadBtn.disabled = true;
    uploadBtn.textContent = '处理中...';

    try {
        const result = await api.uploadDocument(formData);
        if (result.status === 'success') {
            alert(`上传成功！文档ID: ${result.doc_id}, 切片数: ${result.chunk_count}`);
            // 重置表单
            resetUploadForm();
            // 刷新列表
            loadDocuments();
            loadStats();
        } else {
            alert('上传失败: ' + (result.detail || '未知错误'));
        }
    } catch (error) {
        alert('上传失败: ' + error.message);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '上传并处理';
    }
}

// 重置上传表单
function resetUploadForm() {
    selectedFile = null;
    fileInput.value = '';
    uploadArea.style.display = 'block';
    uploadForm.style.display = 'none';
}

// 加载文档列表
async function loadDocuments() {
    const subject = filterSubject.value || null;
    const result = await api.getDocuments(subject);
    const documents = result.documents || [];

    documentsList.innerHTML = documents.map(doc => `
        <tr>
            <td>${doc.filename}</td>
            <td>${doc.subject}</td>
            <td>${doc.chunk_count}</td>
            <td>${formatDate(doc.create_time)}</td>
            <td>
                <button class="delete-btn" onclick="deleteDocument('${doc.doc_id}')">删除</button>
            </td>
        </tr>
    `).join('');
}

// 删除文档
async function deleteDocument(docId) {
    if (!confirm('确定要删除这个文档吗？')) return;

    try {
        const result = await api.deleteDocument(docId);
        if (result.status === 'success') {
            loadDocuments();
            loadStats();
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 加载统计信息
async function loadStats() {
    const stats = await api.getStats();

    totalDocs.textContent = stats.total_documents || 0;
    totalChunks.textContent = stats.total_chunks || 0;
    storageSize.textContent = (stats.storage_size_mb || 0) + ' MB';

    // 学科分布
    if (stats.by_subject) {
        subjectStats.innerHTML = Object.entries(stats.by_subject).map(([subject, data]) => `
            <div class="subject-stat">
                <div class="subject-stat-name">${subject}</div>
                <div class="subject-stat-count">${data.docs} 文档 / ${data.chunks} 切片</div>
            </div>
        `).join('');
    }
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
