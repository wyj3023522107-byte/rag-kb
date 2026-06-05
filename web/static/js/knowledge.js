// web/static/js/knowledge.js

// DOM元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');
const uploadBtn = document.getElementById('uploadBtn');
const cancelBtn = document.getElementById('cancelBtn');
const subjectSelect = document.getElementById('subjectSelect');
const gradeSelect = document.getElementById('gradeSelect');
const titleInput = document.getElementById('titleInput');
const autoClassifyCheckbox = document.getElementById('autoClassify');
const documentsList = document.getElementById('documentsList');
const filterSubject = document.getElementById('filterSubject');
const totalDocs = document.getElementById('totalDocs');
const totalChunks = document.getElementById('totalChunks');
const storageSize = document.getElementById('storageSize');

let selectedFile = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
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

    // 取消按钮
    if (cancelBtn) {
        cancelBtn.addEventListener('click', resetUploadForm);
    }

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
    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.md', '.xlsx', '.xls'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(fileExt)) {
        alert('不支持的文件类型，请上传 PDF, Word, TXT 或 Markdown 文件');
        return;
    }

    selectedFile = file;
    uploadArea.style.display = 'none';
    uploadForm.style.display = 'block';

    // 显示选中的文件名
    document.getElementById('selectedFileName').textContent = file.name;
    titleInput.value = file.name.replace(/\.[^/.]+$/, '');
}

// 上传文档
async function uploadDocument() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    // 分类：如果选择了具体分类则使用，否则留空让后端自动识别
    if (subjectSelect.value) {
        formData.append('subject', subjectSelect.value);
    }

    formData.append('title', titleInput.value || selectedFile.name);

    // 获取选中的年级
    const selectedGrades = Array.from(gradeSelect.selectedOptions).map(opt => opt.value);
    selectedGrades.forEach(grade => formData.append('grade', grade));

    // 智能分类开关
    formData.append('auto_classify', autoClassifyCheckbox.checked);

    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '处理中...';

    try {
        const result = await api.uploadDocument(formData);
        if (result.status === 'success') {
            let message = `上传成功！\n`;
            message += `文档: ${result.filename}\n`;
            message += `切片数: ${result.chunk_count}\n`;

            // 显示智能分类结果
            if (result.auto_classified && result.category) {
                message += `自动识别分类: ${result.category}`;
            }

            alert(message);
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
        uploadBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            上传
        `;
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

    // 学科标签颜色映射
    const tagClass = {
        '数学': 'tag-purple',
        '物理': 'tag-blue',
        '化学': 'tag-emerald',
        '英语': 'tag-cyan',
        '语文': 'tag-rose',
        '生物': 'tag-emerald',
        '历史': 'tag-amber',
        '地理': 'tag-cyan',
        '政治': 'tag-purple',
        '公司文档': 'tag-blue',
        '技术文档': 'tag-purple',
        '产品文档': 'tag-cyan',
        '研究报告': 'tag-amber',
        '政策法规': 'tag-rose',
        '其他': 'tag-blue'
    };

    documentsList.innerHTML = documents.map(doc => `
        <tr>
            <td>${doc.filename}</td>
            <td><span class="tag ${tagClass[doc.subject] || 'tag-cyan'}">${doc.subject}</span></td>
            <td>${doc.chunk_count}</td>
            <td>${formatDate(doc.create_time)}</td>
            <td>
                <button class="view-btn" onclick="viewChunks('${doc.doc_id}', '${doc.filename}')">查看切片</button>
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

// 查看文档切片
async function viewChunks(docId, filename) {
    const modal = document.getElementById('chunksModal');
    const modalTitle = document.getElementById('chunksModalTitle');
    const modalBody = document.getElementById('chunksModalBody');

    modalTitle.textContent = `文档切片 - ${filename}`;
    modalBody.innerHTML = '<div class="loading">加载中...</div>';
    modal.classList.add('open');

    try {
        const result = await api.getChunks(docId);
        const chunks = result.chunks || [];

        if (chunks.length === 0) {
            modalBody.innerHTML = '<div class="empty-state">暂无切片数据</div>';
            return;
        }

        modalBody.innerHTML = chunks.map((chunk, index) => `
            <div class="chunk-item">
                <div class="chunk-header">
                    <span class="chunk-index">切片 ${index + 1}</span>
                    <span class="chunk-id">${chunk.chunk_id.substring(0, 8)}...</span>
                </div>
                <div class="chunk-content">${escapeHtml(chunk.content)}</div>
            </div>
        `).join('');
    } catch (error) {
        modalBody.innerHTML = `<div class="error-state">加载失败: ${error.message}</div>`;
    }
}

// 关闭切片模态框
function closeChunksModal() {
    const modal = document.getElementById('chunksModal');
    modal.classList.remove('open');
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 点击模态框外部关闭
document.getElementById('chunksModal').addEventListener('click', (e) => {
    if (e.target.id === 'chunksModal') {
        closeChunksModal();
    }
});
