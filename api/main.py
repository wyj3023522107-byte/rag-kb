# api/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from api.routes import chat, knowledge

app = FastAPI(
    title="K12智能学习助手",
    description="K12学生学习助手API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(knowledge.router)

# 静态文件
static_dir = Path(__file__).parent.parent / "web" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    """主页"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "K12智能学习助手 API"}


@app.get("/knowledge")
async def knowledge_page():
    """知识库管理页面"""
    knowledge_path = static_dir / "knowledge.html"
    if knowledge_path.exists():
        return FileResponse(str(knowledge_path))
    return {"message": "Knowledge page not found"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
