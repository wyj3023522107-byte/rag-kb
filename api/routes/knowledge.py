# api/routes/knowledge.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(default=None),
    grade: List[str] = Form(default=[]),
    title: str = Form(default=""),
    auto_classify: bool = Form(default=True)
):
    """上传文档

    参数:
    - file: 上传的文件 (PDF/DOCX/TXT/MD)
    - subject: 科目/分类 (可选，不填则自动识别)
    - grade: 适用年级 (可选)
    - title: 文档标题 (可选，默认使用文件名)
    - auto_classify: 是否启用智能分类 (默认 True)
    """
    from src.knowledge.manager import get_knowledge_manager
    import tempfile
    import os

    # 检查文件类型
    allowed = [".pdf", ".docx", ".doc", ".txt", ".md", ".xlsx", ".xls"]
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        manager = get_knowledge_manager()
        result = await manager.upload(
            file_path=tmp_path,
            original_filename=file.filename,  # 传入原始文件名
            subject=subject,
            grade_range=grade,
            title=title or file.filename,
            auto_classify=auto_classify
        )

        return {
            "status": "success",
            "doc_id": result.doc_id,
            "chunk_count": result.chunk_count,
            "filename": result.filename,
            "category": result.category,
            "auto_classified": result.auto_classified
        }
    finally:
        os.unlink(tmp_path)


@router.get("/list")
async def list_documents(subject: Optional[str] = None):
    """获取文档列表"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()
    docs = manager.list(subject=subject)

    return {"documents": [
        {
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "subject": doc.subject,
            "chunk_count": doc.chunk_count,
            "create_time": doc.create_time
        }
        for doc in docs
    ]}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()
    success = manager.delete(doc_id)

    if success:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="文档不存在")


@router.get("/stats")
async def get_stats():
    """获取统计信息"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()
    return manager.stats()


@router.get("/chunks/{doc_id}")
async def get_document_chunks(doc_id: str):
    """获取文档的所有切片"""
    from src.storage.vector_store import get_vector_store

    vector_store = get_vector_store()
    chunks = vector_store.get_by_doc_id(doc_id)

    return {"chunks": chunks}
