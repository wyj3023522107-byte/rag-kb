# K12智能学习助手 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个完整的K12学习助手系统，包含意图识别、槽位填充、RAG检索、知识库管理和Web前端。

**Architecture:** 基于LangGraph的Agent编排系统，使用FastAPI提供REST API，原生HTML/CSS/JavaScript作为前端，Chroma+Whoosh作为混合检索存储。

**Tech Stack:** Python 3.10+, LangGraph, LangChain, FastAPI, Chroma, Whoosh, 通义千问LLM, DashScope Embedding

---

## 文件结构

```
k12-study-assistant/
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── prompts.py
│
├── src/
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── embeddings.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   ├── keyword_index.py
│   │   └── metadata_store.py
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── loader/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── pdf_loader.py
│   │   │   ├── docx_loader.py
│   │   │   └── txt_loader.py
│   │   ├── splitter.py
│   │   └── embedder.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   └── generator.py
│   ├── conversation/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   └── history.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── graph.py
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── intent_classifier.py
│   │       ├── slot_filler.py
│   │       ├── slot_checker.py
│   │       ├── router.py
│   │       └── handlers/
│   │           ├── __init__.py
│   │           ├── base.py
│   │           ├── study_qa.py
│   │           ├── homework.py
│   │           ├── emotion.py
│   │           └── chitchat.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── routes/
│       ├── __init__.py
│       ├── chat.py
│       └── knowledge.py
│
├── cli/
│   ├── __init__.py
│   └── main.py
│
├── web/
│   └── static/
│       ├── index.html
│       ├── knowledge.html
│       ├── css/
│       │   ├── style.css
│       │   ├── chat.css
│       │   └── knowledge.css
│       └── js/
│           ├── api.js
│           ├── app.js
│           ├── knowledge.js
│           └── markdown.js
│
├── data/
│   ├── chroma/
│   ├── bm25_index/
│   └── metadata/
│
├── tests/
│   ├── __init__.py
│   ├── test_llm/
│   ├── test_storage/
│   ├── test_knowledge/
│   ├── test_rag/
│   └── test_agent/
│
└── docs/
    └── superpowers/
        ├── specs/
        └── plans/
```

---

## Task 1: 项目初始化

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`
- Create: `config/__init__.py`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建项目根目录结构**

```bash
mkdir -p config src tests
mkdir -p src/llm src/storage src/knowledge src/rag src/conversation src/agent src/utils
mkdir -p src/knowledge/loader src/agent/nodes src/agent/nodes/handlers
mkdir -p api api/routes cli web web/static web/static/css web/static/js
mkdir -p data data/chroma data/bm25_index data/metadata
mkdir -p tests/test_llm tests/test_storage tests/test_knowledge tests/test_rag tests/test_agent
```

- [ ] **Step 2: 创建 pyproject.toml**

```toml
[project]
name = "k12-study-assistant"
version = "1.0.0"
description = "K12智能学习助手系统"
requires-python = ">=3.10"

dependencies = [
    # Agent框架
    "langgraph>=0.2.0",
    "langchain>=0.2.0",
    "langchain-core>=0.2.0",
    "langchain-community>=0.2.0",

    # LLM
    "dashscope>=1.17.0",

    # 向量存储
    "chromadb>=0.4.0",
    "whoosh>=2.7.4",

    # 文档处理
    "pymupdf>=1.23.0",
    "python-docx>=1.1.0",

    # Web后端
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "python-multipart>=0.0.6",

    # 工具库
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "loguru>=0.7.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "httpx>=0.25.0",
    "tenacity>=8.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.black]
line-length = 88
target-version = ['py310']

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]
```

- [ ] **Step 3: 创建 .env.example**

```env
# 阿里云DashScope API配置
DASHSCOPE_API_KEY=your-api-key-here

# 模型配置
CHAT_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v2

# 存储路径
CHROMA_PERSIST_DIR=./data/chroma
BM25_INDEX_DIR=./data/bm25_index
METADATA_DIR=./data/metadata

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

- [ ] **Step 4: 创建 .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local

# Data
data/chroma/
data/bm25_index/
data/metadata/
*.pdf
*.docx

# Logs
logs/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 5: 创建 README.md**

```markdown
# K12智能学习助手

一个基于LangGraph的智能学习助手系统，支持学科问答、作业辅导、情绪疏导等功能。

## 功能特性

- 🎯 意图识别：自动识别用户意图类型
- 📝 槽位填充：提取关键信息，支持多轮追问
- 🔍 混合检索：向量检索 + 关键词检索
- 📚 RAG问答：基于知识库的智能问答
- 💬 Web界面：友好的对话交互界面

## 快速开始

### 安装依赖

```bash
pip install -e .
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 启动Web服务

```bash
uvicorn api.main:app --reload
```

### 使用CLI

```bash
python -m cli.main chat
python -m cli.main knowledge upload ./docs/math.pdf --subject 数学
```

## 项目结构

```
k12-study-assistant/
├── config/         # 配置
├── src/            # 源代码
│   ├── agent/      # Agent核心
│   ├── rag/        # RAG检索
│   ├── knowledge/  # 知识库管理
│   ├── storage/    # 存储层
│   └── llm/        # LLM封装
├── api/            # FastAPI接口
├── cli/            # 命令行工具
├── web/            # 前端静态文件
└── tests/          # 测试
```

## License

MIT
```

- [ ] **Step 6: 创建 __init__.py 文件**

```bash
touch config/__init__.py
touch src/__init__.py
touch src/llm/__init__.py
touch src/storage/__init__.py
touch src/knowledge/__init__.py
touch src/knowledge/loader/__init__.py
touch src/rag/__init__.py
touch src/conversation/__init__.py
touch src/agent/__init__.py
touch src/agent/nodes/__init__.py
touch src/agent/nodes/handlers/__init__.py
touch src/utils/__init__.py
touch api/__init__.py
touch api/routes/__init__.py
touch cli/__init__.py
touch tests/__init__.py
```

- [ ] **Step 7: 提交初始化代码**

```bash
git init
git add .
git commit -m "feat: project initialization"
```

---

## Task 2: 配置模块

**Files:**
- Create: `config/settings.py`
- Create: `config/prompts.py`
- Create: `src/utils/logger.py`

- [ ] **Step 1: 创建配置管理 settings.py**

```python
# config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "K12智能学习助手"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # LLM配置
    DASHSCOPE_API_KEY: str = Field(..., env="DASHSCOPE_API_KEY")
    CHAT_MODEL: str = "qwen-plus"
    EMBEDDING_MODEL: str = "text-embedding-v2"

    # 模型参数
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048
    TOP_P: float = 0.9

    # 存储路径
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    BM25_INDEX_DIR: str = "./data/bm25_index"
    METADATA_DIR: str = "./data/metadata"

    # 文档处理
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # 对话配置
    MAX_HISTORY_TURNS: int = 20

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # 支持的学科
    SUBJECTS: List[str] = [
        "语文", "数学", "英语", "物理", "化学",
        "生物", "历史", "地理", "政治"
    ]

    # 支持的年级
    GRADES: List[str] = [
        "小学", "初一", "初二", "初三",
        "高一", "高二", "高三"
    ]

    # 意图类型
    INTENTS: List[str] = [
        "study_qa",
        "homework_help",
        "emotion_support",
        "chitchat"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
```

- [ ] **Step 2: 创建Prompt模板 prompts.py**

```python
# config/prompts.py

# 意图识别Prompt
INTENT_CLASSIFICATION_PROMPT = """你是一个意图识别助手，需要判断学生输入的意图类别。

【意图类别】
- study_qa: 学科知识问答（概念解释、知识点讲解）
- homework_help: 作业辅导（具体题目求解、作业检查）
- emotion_support: 情绪疏导（倾诉压力、寻求安慰）
- chitchat: 闲聊（日常对话、打招呼）

【示例】
用户: "勾股定理是什么？"
意图: study_qa

用户: "这道方程题我不会做，x+5=12"
意图: homework_help

用户: "这次考试没考好，感觉好沮丧"
意图: emotion_support

用户: "你好呀"
意图: chitchat

【用户输入】
{query}

请输出意图类别（只输出类别名称，不要解释）:"""

# 槽位填充Prompt
SLOT_FILLING_PROMPT = """你是一个槽位提取助手。根据用户输入，提取以下槽位信息。

【意图类型】{intent}
【槽位定义】
{slot_definition}

【用户输入】
{query}

【历史对话】
{history}

请以JSON格式输出提取的槽位，缺失的槽位填null。只输出JSON，不要其他内容:"""

# 学科问答槽位定义
STUDY_QA_SLOTS = """
- subject: 学科（语文/数学/英语/物理/化学/生物/历史/地理/政治）
- grade: 年级（小学/初一/初二/初三/高一/高二/高三），可选
- topic: 具体知识点或问题
"""

# 作业辅导槽位定义
HOMEWORK_HELP_SLOTS = """
- subject: 学科（语文/数学/英语/物理/化学/生物/历史/地理/政治）
- question: 具体题目内容
"""

# 情绪疏导槽位定义
EMOTION_SUPPORT_SLOTS = """
- emotion_type: 情绪类型（焦虑/沮丧/愤怒/迷茫/压力），可选
- context: 具体原因或背景，可选
"""

# 槽位定义映射
SLOT_DEFINITIONS = {
    "study_qa": STUDY_QA_SLOTS,
    "homework_help": HOMEWORK_HELP_SLOTS,
    "emotion_support": EMOTION_SUPPORT_SLOTS,
    "chitchat": ""
}

# 追问模板
ASK_MISSING_TEMPLATES = {
    "subject": "请问是哪个学科的问题呢？",
    "topic": "请问你想了解哪个具体的知识点呢？",
    "question": "请告诉我具体的题目内容，我来帮你分析。",
}

# RAG回答生成Prompt
RAG_PROMPT = """你是一位专业的K12学习辅导老师。请根据参考知识回答学生的问题。

【学生问题】
{query}

【学科信息】
学科: {subject}
年级: {grade}

【参考知识】
{context}

【回答要求】
1. 准确回答问题，内容要有依据
2. 语言通俗易懂，适合学生年级
3. 如有例题，给出详细讲解
4. 适当延伸相关知识
5. 如果参考知识不足以回答，请诚实说明

请开始回答:"""

# 作业辅导Prompt
HOMEWORK_GUIDANCE_PROMPT = """你是一位耐心的K12辅导老师。请用启发式方法引导学生解题，不要直接给出答案。

【学生题目】
学科: {subject}
题目: {question}

【相关知识点】
{knowledge_context}

【输出要求】
1. 先分析这道题考查什么知识点
2. 用提问方式引导学生思考第一步
3. 给出提示，让学生自己尝试
4. 如果学生仍困惑，再逐步给出更详细的指导

注意: 保持鼓励和耐心的语气。"""

# 情绪疏导Prompt
EMOTION_SUPPORT_PROMPT = """你是一位温暖、有同理心的学生心理辅导员。

【学生倾诉】
{query}

【情绪类型】
{emotion_type}

【回应原则】
1. 首先表达理解和接纳
2. 用开放式问题引导学生表达更多
3. 给予积极的支持和建议
4. 如果情况严重，温和地建议寻求专业帮助

请给予温暖的回应:"""

# 闲聊Prompt
CHITCHAT_PROMPT = """你是一个友好、活泼的学习助手。

【用户输入】
{query}

【回应原则】
1. 保持轻松友好的语气
2. 可以聊学习之外的话题
3. 适当引导回到学习话题

请回应:"""
```

- [ ] **Step 3: 创建日志工具 logger.py**

```python
# src/utils/logger.py

import sys
from loguru import logger
from pathlib import Path

from config.settings import settings


def setup_logger():
    """配置日志"""
    # 移除默认处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # 文件输出
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )

    return logger


# 初始化日志
setup_logger()

# 导出logger实例
__all__ = ["logger"]
```

- [ ] **Step 4: 提交配置模块**

```bash
git add config/ src/utils/
git commit -m "feat: add config and logger modules"
```

---

## Task 3: LLM模块

**Files:**
- Create: `src/llm/client.py`
- Create: `src/llm/embeddings.py`
- Create: `tests/test_llm/__init__.py`
- Create: `tests/test_llm/test_client.py`

- [ ] **Step 1: 编写LLM客户端测试**

```python
# tests/test_llm/test_client.py

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestLLMClient:
    """LLM客户端测试"""

    @pytest.mark.asyncio
    async def test_generate_returns_response(self):
        """测试生成响应"""
        with patch("src.llm.client.Tongyi") as mock_tongyi:
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value="这是测试响应")
            mock_tongyi.return_value = mock_instance

            from src.llm.client import LLMClient

            client = LLMClient()
            result = await client.generate("你好")

            assert result == "这是测试响应"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """测试带系统提示的生成"""
        with patch("src.llm.client.Tongyi") as mock_tongyi:
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value="响应内容")
            mock_tongyi.return_value = mock_instance

            from src.llm.client import LLMClient

            client = LLMClient()
            result = await client.generate(
                "用户问题",
                system_prompt="你是一个助手"
            )

            # 验证调用了ainvoke
            mock_instance.ainvoke.assert_called_once()
            assert result == "响应内容"
```

- [ ] **Step 2: 创建LLM客户端 client.py**

```python
# src/llm/client.py

from langchain_community.llms import Tongyi
from typing import Optional, List
from loguru import logger

from config.settings import settings


class LLMClient:
    """LLM客户端封装"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        self.model_name = model_name or settings.CHAT_MODEL
        self.temperature = temperature or settings.TEMPERATURE
        self.max_tokens = max_tokens or settings.MAX_TOKENS

        self._client = Tongyi(
            model_name=self.model_name,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=settings.TOP_P
        )

        logger.info(f"LLM客户端初始化完成: model={self.model_name}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stop: Optional[List[str]] = None
    ) -> str:
        """生成响应"""
        messages = []

        if system_prompt:
            messages.append(("system", system_prompt))

        messages.append(("human", prompt))

        try:
            response = await self._client.ainvoke(messages, stop=stop)
            logger.debug(f"LLM响应: {response[:100]}...")
            return response
        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            raise

    async def classify(self, prompt: str, options: List[str]) -> str:
        """分类任务"""
        full_prompt = f"{prompt}\n\n请只从以下选项中选择一个: {', '.join(options)}"
        response = await self.generate(full_prompt)

        # 提取匹配的选项
        response = response.strip()
        for option in options:
            if option in response:
                return option

        return response


# 全局实例
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取LLM客户端实例"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
```

- [ ] **Step 3: 创建Embedding客户端 embeddings.py**

```python
# src/llm/embeddings.py

from langchain_community.embeddings import DashScopeEmbeddings
from typing import List, Optional
from loguru import logger

from config.settings import settings


class EmbeddingClient:
    """Embedding客户端封装"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL

        self._client = DashScopeEmbeddings(
            model=self.model_name,
            dashscope_api_key=settings.DASHSCOPE_API_KEY
        )

        logger.info(f"Embedding客户端初始化完成: model={self.model_name}")

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        try:
            embedding = self._client.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Embedding失败: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        try:
            embeddings = self._client.embed_documents(texts)
            logger.debug(f"成功嵌入 {len(texts)} 个文档")
            return embeddings
        except Exception as e:
            logger.error(f"批量Embedding失败: {e}")
            raise

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入单个查询"""
        try:
            embedding = await self._client.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"异步Embedding失败: {e}")
            raise

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入多个文档"""
        try:
            embeddings = await self._client.aembed_documents(texts)
            logger.debug(f"成功嵌入 {len(texts)} 个文档")
            return embeddings
        except Exception as e:
            logger.error(f"异步批量Embedding失败: {e}")
            raise


# 全局实例
_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """获取Embedding客户端实例"""
    global _client
    if _client is None:
        _client = EmbeddingClient()
    return _client
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_llm/ -v
```

- [ ] **Step 5: 提交LLM模块**

```bash
git add src/llm/ tests/test_llm/
git commit -m "feat: add LLM client and embedding modules"
```

---

## Task 4: 存储层 - 向量存储

**Files:**
- Create: `src/storage/vector_store.py`
- Create: `tests/test_storage/__init__.py`
- Create: `tests/test_storage/test_vector_store.py`

- [ ] **Step 1: 编写向量存储测试**

```python
# tests/test_storage/test_vector_store.py

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock


class TestVectorStore:
    """向量存储测试"""

    def test_init_creates_collection(self):
        """测试初始化创建集合"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.storage.vector_store.Chroma") as mock_chroma:
                mock_client = Mock()
                mock_chroma.return_value = mock_client

                from src.storage.vector_store import VectorStore

                store = VectorStore(persist_dir=tmpdir)

                assert store is not None

    def test_add_documents(self):
        """测试添加文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.storage.vector_store.Chroma") as mock_chroma:
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_chroma.return_value = mock_client

                from src.storage.vector_store import VectorStore

                store = VectorStore(persist_dir=tmpdir)

                ids = ["id1", "id2"]
                embeddings = [[0.1, 0.2], [0.3, 0.4]]
                documents = ["文档1", "文档2"]
                metadatas = [{"subject": "数学"}, {"subject": "物理"}]

                store.add(ids, embeddings, documents, metadatas)

                mock_collection.add.assert_called_once()

    def test_search_returns_results(self):
        """测试搜索返回结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.storage.vector_store.Chroma") as mock_chroma:
                mock_client = Mock()
                mock_collection = Mock()
                mock_collection.query.return_value = {
                    "ids": [["id1", "id2"]],
                    "documents": [["文档1", "文档2"]],
                    "metadatas": [[{"subject": "数学"}, {"subject": "物理"}]],
                    "distances": [[0.1, 0.2]]
                }
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_chroma.return_value = mock_client

                from src.storage.vector_store import VectorStore

                store = VectorStore(persist_dir=tmpdir)

                results = store.search([0.1, 0.2], top_k=2)

                assert len(results) == 2
                assert results[0]["doc_id"] == "id1"
```

- [ ] **Step 2: 创建向量存储 vector_store.py**

```python
# src/storage/vector_store.py

import chromadb
from chromadb.config import Settings
from typing import List, Optional, Dict, Any
from pathlib import Path
from loguru import logger

from config.settings import settings


class VectorStore:
    """向量存储封装"""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_dir: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR

        # 确保目录存在
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # 初始化Chroma客户端
        self._client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建集合
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"向量存储初始化完成: collection={collection_name}, path={self.persist_dir}")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """添加向量"""
        try:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            count = len(ids)
            logger.debug(f"成功添加 {count} 个向量")
            return count
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            raise

    def search(
        self,
        embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            # 格式化结果
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "doc_id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": 1 - results["distances"][0][i] if results["distances"] else 0
                    })

            logger.debug(f"检索返回 {len(formatted)} 条结果")
            return formatted
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            raise

    def delete(self, ids: List[str]) -> int:
        """删除向量"""
        try:
            self._collection.delete(ids=ids)
            count = len(ids)
            logger.debug(f"成功删除 {count} 个向量")
            return count
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            raise

    def delete_by_metadata(self, where: Dict[str, Any]) -> int:
        """按元数据删除"""
        try:
            # 先查询符合条件的ID
            results = self._collection.get(where=where)
            if results["ids"]:
                self._collection.delete(ids=results["ids"])
                count = len(results["ids"])
                logger.debug(f"按条件删除 {count} 个向量")
                return count
            return 0
        except Exception as e:
            logger.error(f"按条件删除失败: {e}")
            raise

    def count(self) -> int:
        """获取向量数量"""
        return self._collection.count()

    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取向量"""
        return self._collection.get(ids=ids, where=where, include=["documents", "metadatas"])


# 全局实例
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_storage/test_vector_store.py -v
```

- [ ] **Step 4: 提交向量存储模块**

```bash
git add src/storage/ tests/test_storage/
git commit -m "feat: add vector store module"
```

---

## Task 5: 存储层 - 关键词索引

**Files:**
- Create: `src/storage/keyword_index.py`
- Create: `tests/test_storage/test_keyword_index.py`

- [ ] **Step 1: 编写关键词索引测试**

```python
# tests/test_storage/test_keyword_index.py

import pytest
import tempfile
from pathlib import Path


class TestKeywordIndex:
    """关键词索引测试"""

    def test_init_creates_index(self):
        """测试初始化创建索引"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.keyword_index import KeywordIndex

            index = KeywordIndex(index_dir=tmpdir)

            assert index is not None

    def test_add_and_search(self):
        """测试添加和搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.keyword_index import KeywordIndex

            index = KeywordIndex(index_dir=tmpdir)

            # 添加文档
            docs = [
                {"doc_id": "doc1", "content": "勾股定理是几何学中的重要定理"},
                {"doc_id": "doc2", "content": "函数单调性描述函数的变化规律"}
            ]
            index.add(docs)

            # 搜索
            results = index.search("勾股定理", top_k=2)

            assert len(results) > 0

    def test_delete(self):
        """测试删除"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.keyword_index import KeywordIndex

            index = KeywordIndex(index_dir=tmpdir)

            # 添加文档
            docs = [
                {"doc_id": "doc1", "content": "勾股定理是几何学中的重要定理"}
            ]
            index.add(docs)

            # 删除
            index.delete(["doc1"])

            # 搜索应该为空
            results = index.search("勾股定理", top_k=2)

            assert len(results) == 0
```

- [ ] **Step 2: 创建关键词索引 keyword_index.py**

```python
# src/storage/keyword_index.py

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.qparser import QueryParser, OrGroup
from whoosh.analysis import ChineseAnalyzer
from typing import List, Optional, Dict, Any
from pathlib import Path
from loguru import logger

from config.settings import settings


class KeywordIndex:
    """BM25关键词索引"""

    def __init__(self, index_dir: Optional[str] = None):
        self.index_dir = index_dir or settings.BM25_INDEX_DIR

        # 确保目录存在
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)

        # 定义schema
        self.schema = Schema(
            doc_id=ID(stored=True, unique=True),
            content=TEXT(analyzer=ChineseAnalyzer(), stored=True),
            subject=KEYWORD(stored=True)
        )

        # 初始化索引
        if exists_in(self.index_dir):
            self._ix = open_dir(self.index_dir)
        else:
            self._ix = create_in(self.index_dir, self.schema)

        logger.info(f"关键词索引初始化完成: path={self.index_dir}")

    def add(self, docs: List[Dict[str, Any]]) -> int:
        """添加文档到索引"""
        try:
            writer = self._ix.writer()
            count = 0

            for doc in docs:
                writer.add_document(
                    doc_id=doc["doc_id"],
                    content=doc["content"],
                    subject=doc.get("metadata", {}).get("subject", "")
                )
                count += 1

            writer.commit()
            logger.debug(f"成功添加 {count} 个文档到索引")
            return count
        except Exception as e:
            logger.error(f"添加文档到索引失败: {e}")
            raise

    def search(self, query: str, top_k: int = 10, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """关键词检索"""
        try:
            searcher = self._ix.searcher()

            # 构建查询
            parser = QueryParser("content", self._ix.schema, group=OrGroup)
            q = parser.parse(query)

            # 如果指定了学科，添加过滤
            if subject:
                from whoosh.query import And, Term
                q = And([q, Term("subject", subject)])

            # 执行搜索
            results = searcher.search(q, limit=top_k)

            # 格式化结果
            formatted = []
            for hit in results:
                formatted.append({
                    "doc_id": hit["doc_id"],
                    "content": hit["content"],
                    "score": hit.score,
                    "metadata": {"subject": hit.get("subject", "")}
                })

            searcher.close()
            logger.debug(f"关键词检索返回 {len(formatted)} 条结果")
            return formatted
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []

    def delete(self, doc_ids: List[str]) -> int:
        """从索引删除文档"""
        try:
            writer = self._ix.writer()
            count = 0

            for doc_id in doc_ids:
                writer.delete_by_term("doc_id", doc_id)
                count += 1

            writer.commit()
            logger.debug(f"从索引删除 {count} 个文档")
            return count
        except Exception as e:
            logger.error(f"从索引删除文档失败: {e}")
            raise

    def count(self) -> int:
        """获取文档数量"""
        searcher = self._ix.searcher()
        count = searcher.doc_count()
        searcher.close()
        return count

    def clear(self):
        """清空索引"""
        writer = self._ix.writer()
        writer.commit(mergetype="clear")
        logger.debug("索引已清空")


# 全局实例
_index: Optional[KeywordIndex] = None


def get_keyword_index() -> KeywordIndex:
    """获取关键词索引实例"""
    global _index
    if _index is None:
        _index = KeywordIndex()
    return _index
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_storage/test_keyword_index.py -v
```

- [ ] **Step 4: 提交关键词索引模块**

```bash
git add src/storage/keyword_index.py tests/test_storage/test_keyword_index.py
git commit -m "feat: add keyword index module"
```

---

## Task 6: 存储层 - 元数据存储

**Files:**
- Create: `src/storage/metadata_store.py`
- Create: `tests/test_storage/test_metadata_store.py`

- [ ] **Step 1: 编写元数据存储测试**

```python
# tests/test_storage/test_metadata_store.py

import pytest
import tempfile
from pathlib import Path
import json


class TestMetadataStore:
    """元数据存储测试"""

    def test_save_and_get_metadata(self):
        """测试保存和获取元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.metadata_store import MetadataStore

            store = MetadataStore(metadata_dir=tmpdir)

            metadata = {
                "doc_id": "doc_001",
                "filename": "test.pdf",
                "subject": "数学",
                "chunk_count": 10
            }

            store.save("doc_001", metadata)

            result = store.get("doc_001")

            assert result["doc_id"] == "doc_001"
            assert result["filename"] == "test.pdf"

    def test_list_metadata(self):
        """测试列出元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.metadata_store import MetadataStore

            store = MetadataStore(metadata_dir=tmpdir)

            store.save("doc_001", {"doc_id": "doc_001", "subject": "数学"})
            store.save("doc_002", {"doc_id": "doc_002", "subject": "物理"})

            results = store.list()

            assert len(results) == 2

    def test_delete_metadata(self):
        """测试删除元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.storage.metadata_store import MetadataStore

            store = MetadataStore(metadata_dir=tmpdir)

            store.save("doc_001", {"doc_id": "doc_001"})
            store.delete("doc_001")

            result = store.get("doc_001")

            assert result is None
```

- [ ] **Step 2: 创建元数据存储 metadata_store.py**

```python
# src/storage/metadata_store.py

import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from loguru import logger

from config.settings import settings


class MetadataStore:
    """元数据存储（JSON文件）"""

    def __init__(self, metadata_dir: Optional[str] = None):
        self.metadata_dir = Path(metadata_dir or settings.METADATA_DIR)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"元数据存储初始化完成: path={self.metadata_dir}")

    def _get_file_path(self, doc_id: str) -> Path:
        """获取元数据文件路径"""
        return self.metadata_dir / f"{doc_id}.json"

    def save(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """保存元数据"""
        file_path = self._get_file_path(doc_id)

        # 添加时间戳
        metadata["updated_at"] = datetime.now().isoformat()
        if "created_at" not in metadata:
            metadata["created_at"] = metadata["updated_at"]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.debug(f"保存元数据: {doc_id}")

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取元数据"""
        file_path = self._get_file_path(doc_id)

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有元数据"""
        results = []

        for file_path in self.metadata_dir.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

                # 按学科过滤
                if subject and metadata.get("subject") != subject:
                    continue

                results.append(metadata)

        # 按创建时间排序
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return results

    def delete(self, doc_id: str) -> bool:
        """删除元数据"""
        file_path = self._get_file_path(doc_id)

        if file_path.exists():
            file_path.unlink()
            logger.debug(f"删除元数据: {doc_id}")
            return True

        return False

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        all_metadata = self.list()

        total_docs = len(all_metadata)
        total_chunks = sum(m.get("chunk_count", 0) for m in all_metadata)

        # 按学科统计
        by_subject = {}
        for m in all_metadata:
            subject = m.get("subject", "未知")
            if subject not in by_subject:
                by_subject[subject] = {"docs": 0, "chunks": 0}
            by_subject[subject]["docs"] += 1
            by_subject[subject]["chunks"] += m.get("chunk_count", 0)

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "by_subject": by_subject,
            "storage_size_mb": self._get_storage_size()
        }

    def _get_storage_size(self) -> float:
        """获取存储大小（MB）"""
        total_size = 0
        for file_path in self.metadata_dir.glob("*.json"):
            total_size += file_path.stat().st_size

        # 加上向量库和索引大小
        chroma_path = Path(settings.CHROMA_PERSIST_DIR)
        if chroma_path.exists():
            for f in chroma_path.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size

        bm25_path = Path(settings.BM25_INDEX_DIR)
        if bm25_path.exists():
            for f in bm25_path.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size

        return round(total_size / (1024 * 1024), 2)


# 全局实例
_store: Optional[MetadataStore] = None


def get_metadata_store() -> MetadataStore:
    """获取元数据存储实例"""
    global _store
    if _store is None:
        _store = MetadataStore()
    return _store
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_storage/test_metadata_store.py -v
```

- [ ] **Step 4: 提交元数据存储模块**

```bash
git add src/storage/metadata_store.py tests/test_storage/test_metadata_store.py
git commit -m "feat: add metadata store module"
```

---

## Task 7: 知识库管理 - 文档加载器

**Files:**
- Create: `src/knowledge/loader/base.py`
- Create: `src/knowledge/loader/pdf_loader.py`
- Create: `src/knowledge/loader/docx_loader.py`
- Create: `src/knowledge/loader/txt_loader.py`
- Create: `tests/test_knowledge/__init__.py`
- Create: `tests/test_knowledge/test_loader.py`

- [ ] **Step 1: 创建文档加载器基类**

```python
# src/knowledge/loader/base.py

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path


class BaseLoader(ABC):
    """文档加载器基类"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

    @abstractmethod
    def load(self) -> str:
        """加载文档内容"""
        pass

    @classmethod
    @abstractmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否支持该文件类型"""
        pass
```

- [ ] **Step 2: 创建PDF加载器**

```python
# src/knowledge/loader/pdf_loader.py

import fitz  # PyMuPDF
from typing import List
from loguru import logger

from .base import BaseLoader


class PDFLoader(BaseLoader):
    """PDF文档加载器"""

    def load(self) -> str:
        """加载PDF内容"""
        try:
            doc = fitz.open(self.file_path)
            text_parts = []

            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

            doc.close()

            full_text = "\n\n".join(text_parts)
            logger.debug(f"PDF加载完成: {self.file_path.name}, {len(full_text)} 字符")

            return full_text
        except Exception as e:
            logger.error(f"PDF加载失败: {e}")
            raise

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否为PDF文件"""
        return Path(file_path).suffix.lower() == ".pdf"
```

- [ ] **Step 3: 创建Word加载器**

```python
# src/knowledge/loader/docx_loader.py

from docx import Document
from pathlib import Path
from loguru import logger

from .base import BaseLoader


class DocxLoader(BaseLoader):
    """Word文档加载器"""

    def load(self) -> str:
        """加载Word内容"""
        try:
            doc = Document(self.file_path)
            text_parts = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            logger.debug(f"Word加载完成: {self.file_path.name}, {len(full_text)} 字符")

            return full_text
        except Exception as e:
            logger.error(f"Word加载失败: {e}")
            raise

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否为Word文件"""
        return Path(file_path).suffix.lower() in [".docx", ".doc"]
```

- [ ] **Step 4: 创建TXT加载器**

```python
# src/knowledge/loader/txt_loader.py

from pathlib import Path
from loguru import logger

from .base import BaseLoader


class TxtLoader(BaseLoader):
    """TXT文本加载器"""

    def load(self) -> str:
        """加载TXT内容"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                text = f.read()

            logger.debug(f"TXT加载完成: {self.file_path.name}, {len(text)} 字符")

            return text
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(self.file_path, "r", encoding="gbk") as f:
                text = f.read()
            return text
        except Exception as e:
            logger.error(f"TXT加载失败: {e}")
            raise

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """检查是否为TXT文件"""
        return Path(file_path).suffix.lower() in [".txt", ".md"]
```

- [ ] **Step 5: 创建加载器工厂**

```python
# src/knowledge/loader/__init__.py

from typing import Optional
from pathlib import Path
from loguru import logger

from .base import BaseLoader
from .pdf_loader import PDFLoader
from .docx_loader import DocxLoader
from .txt_loader import TxtLoader


# 注册的加载器列表
LOADERS = [PDFLoader, DocxLoader, TxtLoader]


def get_loader(file_path: str) -> Optional[BaseLoader]:
    """根据文件类型获取对应的加载器"""
    for loader_cls in LOADERS:
        if loader_cls.supports(file_path):
            return loader_cls(file_path)

    logger.warning(f"不支持的文件类型: {file_path}")
    return None


def get_supported_extensions() -> list:
    """获取支持的文件扩展名"""
    return [".pdf", ".docx", ".doc", ".txt", ".md"]
```

- [ ] **Step 6: 提交文档加载器**

```bash
git add src/knowledge/loader/ tests/test_knowledge/
git commit -m "feat: add document loaders"
```

---

## Task 8: 知识库管理 - 文档切分

**Files:**
- Create: `src/knowledge/splitter.py`
- Create: `tests/test_knowledge/test_splitter.py`

- [ ] **Step 1: 编写文档切分测试**

```python
# tests/test_knowledge/test_splitter.py

import pytest


class TestDocumentSplitter:
    """文档切分测试"""

    def test_split_short_text(self):
        """测试切分短文本"""
        from src.knowledge.splitter import DocumentSplitter

        splitter = DocumentSplitter(chunk_size=100, chunk_overlap=10)

        text = "这是一个短文本。"
        chunks = splitter.split(text)

        assert len(chunks) == 1
        assert chunks[0].content == "这是一个短文本。"

    def test_split_long_text(self):
        """测试切分长文本"""
        from src.knowledge.splitter import DocumentSplitter

        splitter = DocumentSplitter(chunk_size=50, chunk_overlap=10)

        text = "这是第一段内容。" * 10
        chunks = splitter.split(text)

        assert len(chunks) > 1

    def test_split_with_metadata(self):
        """测试带元数据的切分"""
        from src.knowledge.splitter import DocumentSplitter

        splitter = DocumentSplitter()

        text = "这是测试内容。"
        metadata = {"subject": "数学", "source": "test.pdf"}

        chunks = splitter.split(text, metadata)

        assert chunks[0].metadata["subject"] == "数学"
        assert chunks[0].metadata["source"] == "test.pdf"
```

- [ ] **Step 2: 创建文档切分器**

```python
# src/knowledge/splitter.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from config.settings import settings


@dataclass
class DocumentChunk:
    """文档切片"""
    id: str
    content: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata
        }


class DocumentSplitter:
    """文档切分器"""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", "；", "，", " "]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len
        )

        logger.debug(f"文档切分器初始化: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")

    def split(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """切分文档"""
        if not text or not text.strip():
            return []

        # 执行切分
        texts = self._splitter.split_text(text)

        # 创建切片对象
        chunks = []
        base_metadata = metadata or {}

        for i, chunk_text in enumerate(texts):
            chunk_id = self._generate_id(chunk_text, i, base_metadata)

            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                metadata={
                    **base_metadata,
                    "chunk_index": i,
                    "total_chunks": len(texts)
                }
            )
            chunks.append(chunk)

        logger.debug(f"文档切分完成: {len(texts)} 个切片")
        return chunks

    def _generate_id(self, text: str, index: int, metadata: Dict[str, Any]) -> str:
        """生成切片ID"""
        import hashlib

        doc_id = metadata.get("doc_id", "unknown")
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]

        return f"{doc_id}_{index}_{content_hash}"
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_knowledge/test_splitter.py -v
```

- [ ] **Step 4: 提交文档切分器**

```bash
git add src/knowledge/splitter.py tests/test_knowledge/test_splitter.py
git commit -m "feat: add document splitter"
```

---

## Task 9: 知识库管理 - 知识库管理器

**Files:**
- Create: `src/knowledge/manager.py`
- Create: `tests/test_knowledge/test_manager.py`

- [ ] **Step 1: 编写知识库管理器测试**

```python
# tests/test_knowledge/test_manager.py

import pytest
from unittest.mock import Mock, patch, AsyncMock
import tempfile


class TestKnowledgeManager:
    """知识库管理器测试"""

    @pytest.mark.asyncio
    async def test_upload_txt_file(self):
        """测试上传TXT文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("这是测试内容。" * 100)
            temp_path = f.name

        try:
            with patch("src.knowledge.manager.get_vector_store") as mock_vs, \
                 patch("src.knowledge.manager.get_keyword_index") as mock_ki, \
                 patch("src.knowledge.manager.get_metadata_store") as mock_ms, \
                 patch("src.knowledge.manager.get_embedding_client") as mock_emb:

                mock_vs.return_value = Mock()
                mock_vs.return_value.add = Mock(return_value=5)
                mock_ki.return_value = Mock()
                mock_ki.return_value.add = Mock(return_value=5)
                mock_ms.return_value = Mock()
                mock_emb.return_value = Mock()
                mock_emb.return_value.embed_documents = Mock(return_value=[[0.1]*1536]*5)

                from src.knowledge.manager import KnowledgeManager

                manager = KnowledgeManager()
                result = await manager.upload(
                    file_path=temp_path,
                    subject="数学",
                    title="测试文档"
                )

                assert result.doc_id is not None
        finally:
            import os
            os.unlink(temp_path)
```

- [ ] **Step 2: 创建知识库管理器**

```python
# src/knowledge/manager.py

import uuid
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger

from config.settings import settings
from .loader import get_loader
from .splitter import DocumentSplitter, DocumentChunk
from src.storage.vector_store import get_vector_store, VectorStore
from src.storage.keyword_index import get_keyword_index, KeywordIndex
from src.storage.metadata_store import get_metadata_store, MetadataStore
from src.llm.embeddings import get_embedding_client, EmbeddingClient


@dataclass
class UploadResult:
    """上传结果"""
    doc_id: str
    chunk_count: int
    filename: str


@dataclass
class DocumentInfo:
    """文档信息"""
    doc_id: str
    filename: str
    subject: str
    chunk_count: int
    create_time: str


class KnowledgeManager:
    """知识库管理器"""

    def __init__(self, batch_size: int = 20):
        self.batch_size = batch_size

        self._vector_store: Optional[VectorStore] = None
        self._keyword_index: Optional[KeywordIndex] = None
        self._metadata_store: Optional[MetadataStore] = None
        self._embedding_client: Optional[EmbeddingClient] = None
        self._splitter: Optional[DocumentSplitter] = None

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store

    @property
    def keyword_index(self) -> KeywordIndex:
        if self._keyword_index is None:
            self._keyword_index = get_keyword_index()
        return self._keyword_index

    @property
    def metadata_store(self) -> MetadataStore:
        if self._metadata_store is None:
            self._metadata_store = get_metadata_store()
        return self._metadata_store

    @property
    def embedding_client(self) -> EmbeddingClient:
        if self._embedding_client is None:
            self._embedding_client = get_embedding_client()
        return self._embedding_client

    @property
    def splitter(self) -> DocumentSplitter:
        if self._splitter is None:
            self._splitter = DocumentSplitter()
        return self._splitter

    async def upload(
        self,
        file_path: str,
        subject: str,
        grade_range: Optional[List[str]] = None,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> UploadResult:
        """上传文档到知识库"""
        logger.info(f"开始上传文档: {file_path}")

        # 生成文档ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        filename = Path(file_path).name

        # 1. 加载文档
        loader = get_loader(file_path)
        if loader is None:
            raise ValueError(f"不支持的文件类型: {filename}")

        text = loader.load()

        # 2. 切分文档
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "subject": subject,
            "grade_range": grade_range or [],
            "title": title or filename,
            "keywords": keywords or []
        }

        chunks = self.splitter.split(text, metadata)

        if not chunks:
            raise ValueError("文档内容为空")

        # 3. 向量化并存储
        await self._embed_and_store(chunks)

        # 4. 保存元数据
        self.metadata_store.save(doc_id, {
            **metadata,
            "chunk_count": len(chunks),
            "file_type": Path(file_path).suffix,
            "create_time": datetime.now().isoformat()
        })

        logger.info(f"文档上传完成: doc_id={doc_id}, chunks={len(chunks)}")

        return UploadResult(
            doc_id=doc_id,
            chunk_count=len(chunks),
            filename=filename
        )

    async def _embed_and_store(self, chunks: List[DocumentChunk]) -> None:
        """向量化并存储"""
        total = len(chunks)

        for i in range(0, total, self.batch_size):
            batch = chunks[i:i + self.batch_size]

            # 批量获取embedding
            texts = [chunk.content for chunk in batch]
            embeddings = self.embedding_client.embed_documents(texts)

            # 存储到向量库
            self.vector_store.add(
                ids=[chunk.id for chunk in batch],
                embeddings=embeddings,
                documents=texts,
                metadatas=[chunk.metadata for chunk in batch]
            )

            # 存储到关键词索引
            self.keyword_index.add([
                {"doc_id": chunk.id, "content": chunk.content, "metadata": chunk.metadata}
                for chunk in batch
            ])

            logger.debug(f"处理批次 {i//self.batch_size + 1}/{(total-1)//self.batch_size + 1}")

    def list(self, subject: Optional[str] = None) -> List[DocumentInfo]:
        """列出文档"""
        metadata_list = self.metadata_store.list(subject=subject)

        return [
            DocumentInfo(
                doc_id=m["doc_id"],
                filename=m["filename"],
                subject=m["subject"],
                chunk_count=m.get("chunk_count", 0),
                create_time=m.get("create_time", "")
            )
            for m in metadata_list
        ]

    def delete(self, doc_id: str) -> bool:
        """删除文档"""
        logger.info(f"删除文档: {doc_id}")

        # 1. 从元数据获取所有切片ID
        metadata = self.metadata_store.get(doc_id)
        if not metadata:
            return False

        # 2. 从向量库删除
        self.vector_store.delete_by_metadata({"doc_id": doc_id})

        # 3. 从关键词索引删除
        # 需要先查询所有切片ID
        results = self.vector_store.get(where={"doc_id": doc_id})
        if results.get("ids"):
            self.keyword_index.delete(results["ids"])

        # 4. 删除元数据
        self.metadata_store.delete(doc_id)

        logger.info(f"文档删除完成: {doc_id}")
        return True

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.metadata_store.stats()


# 全局实例
_manager: Optional[KnowledgeManager] = None


def get_knowledge_manager() -> KnowledgeManager:
    """获取知识库管理器实例"""
    global _manager
    if _manager is None:
        _manager = KnowledgeManager()
    return _manager
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_knowledge/test_manager.py -v
```

- [ ] **Step 4: 提交知识库管理器**

```bash
git add src/knowledge/manager.py tests/test_knowledge/test_manager.py
git commit -m "feat: add knowledge manager"
```

---

## Task 10: RAG检索模块

**Files:**
- Create: `src/rag/retriever.py`
- Create: `src/rag/reranker.py`
- Create: `src/rag/generator.py`
- Create: `src/rag/engine.py`
- Create: `tests/test_rag/__init__.py`
- Create: `tests/test_rag/test_retriever.py`

- [ ] **Step 1: 创建混合检索器 retriever.py**

```python
# src/rag/retriever.py

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from src.storage.vector_store import get_vector_store
from src.storage.keyword_index import get_keyword_index
from src.llm.embeddings import get_embedding_client


class HybridRetriever:
    """混合检索器 - 向量检索 + 关键词检索"""

    def __init__(self, rrf_k: int = 60):
        """
        Args:
            rrf_k: RRF融合参数
        """
        self.rrf_k = rrf_k

        self._vector_store = None
        self._keyword_index = None
        self._embedding_client = None

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store

    @property
    def keyword_index(self):
        if self._keyword_index is None:
            self._keyword_index = get_keyword_index()
        return self._keyword_index

    @property
    def embedding_client(self):
        if self._embedding_client is None:
            self._embedding_client = get_embedding_client()
        return self._embedding_client

    async def search(
        self,
        query: str,
        top_k: int = 10,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """混合检索"""
        # 并行执行向量检索和关键词检索
        vector_task = self._vector_search(query, top_k * 2, subject)
        keyword_task = self._keyword_search(query, top_k * 2, subject)

        vector_results, keyword_results = await asyncio.gather(
            vector_task, keyword_task
        )

        # RRF融合
        fused_results = self._rrf_fusion(vector_results, keyword_results, top_k)

        logger.debug(f"混合检索完成: 向量{len(vector_results)}条, 关键词{len(keyword_results)}条, 融合{len(fused_results)}条")
        return fused_results

    async def _vector_search(
        self,
        query: str,
        top_k: int,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            embedding = self.embedding_client.embed_query(query)
            where = {"subject": subject} if subject else None
            results = self.vector_store.search(embedding, top_k, where)
            return results
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """关键词检索"""
        try:
            results = self.keyword_index.search(query, top_k, subject)
            return results
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []

    def _rrf_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """RRF融合算法"""
        scores = {}
        docs = {}

        # 向量检索结果打分
        for rank, doc in enumerate(vector_results):
            doc_id = doc["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.rrf_k + rank + 1)
            docs[doc_id] = doc

        # 关键词检索结果打分
        for rank, doc in enumerate(keyword_results):
            doc_id = doc["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.rrf_k + rank + 1)
            if doc_id not in docs:
                docs[doc_id] = doc

        # 按分数排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # 构建结果
        results = []
        for doc_id in sorted_ids[:top_k]:
            doc = docs[doc_id].copy()
            doc["rrf_score"] = scores[doc_id]
            results.append(doc)

        return results


# 全局实例
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """获取检索器实例"""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
```

- [ ] **Step 2: 创建重排序器 reranker.py**

```python
# src/rag/reranker.py

from typing import List, Dict, Any
from loguru import logger

from src.llm.client import get_llm_client


class Reranker:
    """重排序器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def rerank(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """重排序检索结果"""
        if not docs:
            return []

        if len(docs) <= top_k:
            return docs

        # 使用LLM打分
        scores = await self._llm_score(query, docs)

        # 合并分数并排序
        for doc, score in zip(docs, scores):
            doc["rerank_score"] = score

        sorted_docs = sorted(docs, key=lambda x: x["rerank_score"], reverse=True)

        logger.debug(f"重排序完成: {len(sorted_docs[:top_k])} 条结果")
        return sorted_docs[:top_k]

    async def _llm_score(
        self,
        query: str,
        docs: List[Dict[str, Any]]
    ) -> List[float]:
        """使用LLM对文档相关性打分"""
        import json

        # 构建prompt
        doc_list = "\n".join([
            f"{i}. {doc['content'][:200]}..."
            for i, doc in enumerate(docs)
        ])

        prompt = f"""请对以下文档与查询的相关性打分(0-10分,只输出数字)。
每个文档一行,输出JSON数组格式。

查询: {query}

文档列表:
{doc_list}

输出格式示例: [8, 5, 7, 3, ...]"""

        try:
            response = await self.llm_client.generate(prompt)
            # 解析JSON
            scores = json.loads(response.strip())
            if isinstance(scores, list) and len(scores) == len(docs):
                return [float(s) for s in scores]
        except Exception as e:
            logger.warning(f"LLM打分失败: {e}")

        # 降级：返回原始顺序的默认分数
        return [0.5] * len(docs)
```

- [ ] **Step 3: 创建生成器 generator.py**

```python
# src/rag/generator.py

from typing import List, Dict, Any, Optional
from loguru import logger

from src.llm.client import get_llm_client
from config.prompts import RAG_PROMPT


class RAGGenerator:
    """RAG回答生成器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def generate(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        subject: str = "",
        grade: str = ""
    ) -> str:
        """生成回答"""
        # 构建上下文
        context = self._build_context(docs)

        # 构建prompt
        prompt = RAG_PROMPT.format(
            query=query,
            subject=subject or "通用",
            grade=grade or "中学",
            context=context
        )

        # 调用LLM生成
        response = await self.llm_client.generate(prompt)

        logger.debug(f"RAG生成完成: {len(response)} 字符")
        return response

    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """构建上下文"""
        context_parts = []

        for i, doc in enumerate(docs, 1):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("filename", "未知来源")
            context_parts.append(f"【参考资料{i}】(来源: {source})\n{content}\n")

        return "\n".join(context_parts)


# 全局实例
_generator: Optional[RAGGenerator] = None


def get_generator() -> RAGGenerator:
    """获取生成器实例"""
    global _generator
    if _generator is None:
        _generator = RAGGenerator()
    return _generator
```

- [ ] **Step 4: 创建RAG引擎 engine.py**

```python
# src/rag/engine.py

from typing import List, Dict, Any, Optional
from loguru import logger

from .retriever import get_retriever, HybridRetriever
from .reranker import Reranker
from .generator import get_generator, RAGGenerator


@dataclass
class SearchResult:
    """检索结果"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class RAGEngine:
    """RAG引擎"""

    def __init__(self):
        self._retriever: Optional[HybridRetriever] = None
        self._reranker: Optional[Reranker] = None
        self._generator: Optional[RAGGenerator] = None

    @property
    def retriever(self) -> HybridRetriever:
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever

    @property
    def reranker(self) -> Reranker:
        if self._reranker is None:
            self._reranker = Reranker()
        return self._reranker

    @property
    def generator(self) -> RAGGenerator:
        if self._generator is None:
            self._generator = get_generator()
        return self._generator

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        subject: Optional[str] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """检索相关文档"""
        logger.info(f"RAG检索: query={query[:50]}...")

        # 混合检索
        results = await self.retriever.search(query, top_k * 2, subject)

        # 重排序
        if rerank and results:
            results = await self.reranker.rerank(query, results, top_k)

        return results[:top_k]

    async def generate(
        self,
        query: str,
        subject: str = "",
        grade: str = "",
        top_k: int = 3
    ) -> str:
        """检索并生成回答"""
        # 检索
        docs = await self.retrieve(query, top_k=top_k, subject=subject)

        if not docs:
            return "抱歉，我没有找到相关的知识来回答这个问题。请尝试换一种方式提问。"

        # 生成回答
        response = await self.generator.generate(query, docs, subject, grade)

        return response


from dataclasses import dataclass

# 全局实例
_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """获取RAG引擎实例"""
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
```

- [ ] **Step 5: 提交RAG模块**

```bash
git add src/rag/ tests/test_rag/
git commit -m "feat: add RAG engine with hybrid retrieval"
```

---

## Task 11: 对话管理模块

**Files:**
- Create: `src/conversation/session.py`
- Create: `src/conversation/history.py`
- Create: `tests/test_agent/__init__.py`

- [ ] **Step 1: 创建会话管理 session.py**

```python
# src/conversation/session.py

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from config.settings import settings


@dataclass
class Session:
    """会话"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: list = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def touch(self):
        """更新时间戳"""
        self.updated_at = datetime.now()


class SessionManager:
    """会话管理器"""

    def __init__(self, max_sessions: int = 100):
        self.max_sessions = max_sessions
        self._sessions: Dict[str, Session] = {}

    def create(self) -> Session:
        """创建新会话"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session = Session(session_id=session_id)

        self._sessions[session_id] = session
        self._cleanup()

        logger.debug(f"创建会话: {session_id}")
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        """获取或创建会话"""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create()

    def delete(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"删除会话: {session_id}")
            return True
        return False

    def _cleanup(self):
        """清理过期会话"""
        if len(self._sessions) > self.max_sessions:
            # 按更新时间排序，删除最旧的
            sorted_sessions = sorted(
                self._sessions.items(),
                key=lambda x: x[1].updated_at
            )
            to_remove = len(self._sessions) - self.max_sessions
            for session_id, _ in sorted_sessions[:to_remove]:
                del self._sessions[session_id]

            logger.debug(f"清理了 {to_remove} 个过期会话")


# 全局实例
_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
```

- [ ] **Step 2: 创建对话历史 history.py**

```python
# src/conversation/history.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from config.settings import settings


@dataclass
class Message:
    """消息"""
    role: str  # user / assistant / system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[str] = None
    slots: Optional[Dict[str, Any]] = None


class ConversationHistory:
    """对话历史"""

    def __init__(self, max_turns: int = None):
        self.max_turns = max_turns or settings.MAX_HISTORY_TURNS
        self.messages: List[Message] = []

    def add_user_message(
        self,
        content: str,
        intent: Optional[str] = None,
        slots: Optional[Dict[str, Any]] = None
    ) -> Message:
        """添加用户消息"""
        msg = Message(
            role="user",
            content=content,
            intent=intent,
            slots=slots
        )
        self.messages.append(msg)
        self._trim()
        logger.debug(f"添加用户消息: {content[:50]}...")
        return msg

    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        msg = Message(role="assistant", content=content)
        self.messages.append(msg)
        self._trim()
        logger.debug(f"添加助手消息: {content[:50]}...")
        return msg

    def get_context(self, turns: Optional[int] = None) -> str:
        """获取对话上下文"""
        limit = turns or self.max_turns
        msgs = self.messages[-limit * 2:]

        lines = []
        for msg in msgs:
            role_name = "用户" if msg.role == "user" else "助手"
            lines.append(f"{role_name}: {msg.content}")

        return "\n".join(lines)

    def get_llm_messages(self) -> List[Dict[str, str]]:
        """获取LLM格式的消息列表"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def clear(self):
        """清空历史"""
        self.messages.clear()
        logger.debug("对话历史已清空")

    def _trim(self):
        """裁剪历史"""
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "intent": msg.intent,
                "slots": msg.slots
            }
            for msg in self.messages
        ]
```

- [ ] **Step 3: 提交对话管理模块**

```bash
git add src/conversation/ tests/test_agent/
git commit -m "feat: add conversation management"
```

---

## Task 12: Agent核心 - 状态定义和意图识别

**Files:**
- Create: `src/agent/state.py`
- Create: `src/agent/nodes/intent_classifier.py`
- Create: `src/agent/nodes/slot_filler.py`
- Create: `src/agent/nodes/slot_checker.py`
- Create: `src/agent/nodes/router.py`

- [ ] **Step 1: 创建Agent状态 state.py**

```python
# src/agent/state.py

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    """Agent状态"""
    # 输入
    query: str                           # 用户原始输入
    session_id: Optional[str]            # 会话ID

    # 意图识别
    intent: Optional[str]                # 识别的意图
    intent_confidence: Optional[float]   # 意图置信度

    # 槽位填充
    slots: Optional[Dict[str, Any]]      # 槽位信息
    slots_complete: Optional[bool]       # 槽位是否完整
    missing_slots: Optional[List[str]]   # 缺失的槽位

    # 追问
    ask_question: Optional[str]          # 追问内容

    # 响应
    response: Optional[str]              # 最终响应

    # 上下文
    history: Optional[List[Dict[str, str]]]  # 对话历史
    context: Optional[Dict[str, Any]]    # 上下文信息


# 槽位定义
SLOT_DEFINITIONS = {
    "study_qa": {
        "subject": {"type": "enum", "required": True, "values": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]},
        "grade": {"type": "enum", "required": False, "values": ["小学", "初一", "初二", "初三", "高一", "高二", "高三"]},
        "topic": {"type": "string", "required": True}
    },
    "homework_help": {
        "subject": {"type": "enum", "required": True, "values": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]},
        "question": {"type": "string", "required": True}
    },
    "emotion_support": {
        "emotion_type": {"type": "enum", "required": False, "values": ["焦虑", "沮丧", "愤怒", "迷茫", "压力"]},
        "context": {"type": "string", "required": False}
    },
    "chitchat": {}
}

# 必填槽位
REQUIRED_SLOTS = {
    "study_qa": ["subject", "topic"],
    "homework_help": ["subject", "question"],
    "emotion_support": [],
    "chitchat": []
}
```

- [ ] **Step 2: 创建意图识别节点 intent_classifier.py**

```python
# src/agent/nodes/intent_classifier.py

import json
from typing import Dict, Any
from loguru import logger

from src.agent.state import AgentState
from src.llm.client import get_llm_client
from config.prompts import INTENT_CLASSIFICATION_PROMPT


async def intent_classifier_node(state: AgentState) -> Dict[str, Any]:
    """意图识别节点"""
    query = state.get("query", "")

    if not query:
        return {"intent": "chitchat", "intent_confidence": 1.0}

    logger.info(f"意图识别: {query[:50]}...")

    # 调用LLM进行意图分类
    llm_client = get_llm_client()

    prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)

    try:
        response = await llm_client.generate(prompt)
        intent = response.strip()

        # 验证意图是否有效
        valid_intents = ["study_qa", "homework_help", "emotion_support", "chitchat"]
        if intent not in valid_intents:
            intent = "chitchat"

        logger.info(f"识别意图: {intent}")

        return {
            "intent": intent,
            "intent_confidence": 0.9
        }
    except Exception as e:
        logger.error(f"意图识别失败: {e}")
        return {"intent": "chitchat", "intent_confidence": 0.5}
```

- [ ] **Step 3: 创建槽位填充节点 slot_filler.py**

```python
# src/agent/nodes/slot_filler.py

import json
from typing import Dict, Any
from loguru import logger

from src.agent.state import AgentState, SLOT_DEFINITIONS
from src.llm.client import get_llm_client
from config.prompts import SLOT_FILLING_PROMPT, SLOT_DEFINITIONS as PROMPT_SLOT_DEFS


async def slot_filler_node(state: AgentState) -> Dict[str, Any]:
    """槽位填充节点"""
    query = state.get("query", "")
    intent = state.get("intent", "chitchat")

    logger.info(f"槽位填充: intent={intent}")

    # 闲聊不需要槽位
    if intent == "chitchat":
        return {"slots": {}, "slots_complete": True, "missing_slots": []}

    # 获取槽位定义
    slot_def = PROMPT_SLOT_DEFS.get(intent, "")
    if not slot_def:
        return {"slots": {}, "slots_complete": True, "missing_slots": []}

    # 构建历史对话
    history = state.get("history", [])
    history_text = "\n".join([
        f"{'用户' if h['role'] == 'user' else '助手'}: {h['content']}"
        for h in history[-4:]  # 最近2轮
    ])

    # 调用LLM提取槽位
    llm_client = get_llm_client()

    prompt = SLOT_FILLING_PROMPT.format(
        intent=intent,
        slot_definition=slot_def,
        query=query,
        history=history_text or "无"
    )

    try:
        response = await llm_client.generate(prompt)

        # 解析JSON
        slots = json.loads(response.strip())

        logger.info(f"提取槽位: {slots}")

        return {"slots": slots}
    except Exception as e:
        logger.error(f"槽位提取失败: {e}")
        return {"slots": {}}
```

- [ ] **Step 4: 创建槽位检查节点 slot_checker.py**

```python
# src/agent/nodes/slot_checker.py

from typing import Dict, Any, List
from loguru import logger

from src.agent.state import AgentState, REQUIRED_SLOTS


def slot_checker_node(state: AgentState) -> Dict[str, Any]:
    """槽位检查节点"""
    intent = state.get("intent", "chitchat")
    slots = state.get("slots", {})

    # 获取必填槽位
    required = REQUIRED_SLOTS.get(intent, [])

    # 检查缺失槽位
    missing = []
    for slot_name in required:
        value = slots.get(slot_name)
        if value is None or value == "" or value == "null":
            missing.append(slot_name)

    is_complete = len(missing) == 0

    logger.info(f"槽位检查: required={required}, missing={missing}, complete={is_complete}")

    return {
        "slots_complete": is_complete,
        "missing_slots": missing
    }
```

- [ ] **Step 5: 创建路由节点 router.py**

```python
# src/agent/nodes/router.py

from typing import Dict, Any
from loguru import logger

from src.agent.state import AgentState


def router_node(state: AgentState) -> str:
    """路由节点 - 返回下一个节点名称"""
    intent = state.get("intent", "chitchat")

    logger.info(f"路由到: {intent}")

    return intent
```

- [ ] **Step 6: 提交Agent核心节点**

```bash
git add src/agent/
git commit -m "feat: add agent state and core nodes"
```

---

## Task 13: Agent核心 - 意图处理器

**Files:**
- Create: `src/agent/nodes/handlers/base.py`
- Create: `src/agent/nodes/handlers/study_qa.py`
- Create: `src/agent/nodes/handlers/homework.py`
- Create: `src/agent/nodes/handlers/emotion.py`
- Create: `src/agent/nodes/handlers/chitchat.py`

- [ ] **Step 1: 创建处理器基类 base.py**

```python
# src/agent/nodes/handlers/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseHandler(ABC):
    """意图处理器基类"""

    @abstractmethod
    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理意图，返回响应"""
        pass
```

- [ ] **Step 2: 创建学科问答处理器 study_qa.py**

```python
# src/agent/nodes/handlers/study_qa.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.rag.engine import get_rag_engine


class StudyQAHandler(BaseHandler):
    """学科问答处理器"""

    def __init__(self):
        self._rag_engine = None

    @property
    def rag_engine(self):
        if self._rag_engine is None:
            self._rag_engine = get_rag_engine()
        return self._rag_engine

    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理学科问答"""
        subject = slots.get("subject", "")
        grade = slots.get("grade", "")
        topic = slots.get("topic", "")

        logger.info(f"学科问答: subject={subject}, topic={topic}")

        # 构建检索query
        query = f"{subject} {topic}" if subject else topic

        # 调用RAG生成回答
        response = await self.rag_engine.generate(
            query=query,
            subject=subject,
            grade=grade,
            top_k=3
        )

        return response
```

- [ ] **Step 3: 创建作业辅导处理器 homework.py**

```python
# src/agent/nodes/handlers/homework.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.llm.client import get_llm_client
from src.rag.engine import get_rag_engine
from config.prompts import HOMEWORK_GUIDANCE_PROMPT


class HomeworkHandler(BaseHandler):
    """作业辅导处理器"""

    def __init__(self):
        self._llm_client = None
        self._rag_engine = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    @property
    def rag_engine(self):
        if self._rag_engine is None:
            self._rag_engine = get_rag_engine()
        return self._rag_engine

    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理作业辅导"""
        subject = slots.get("subject", "")
        question = slots.get("question", "")

        logger.info(f"作业辅导: subject={subject}, question={question[:50]}...")

        # 检索相关知识点
        docs = await self.rag_engine.retrieve(question, top_k=2, subject=subject)

        # 构建知识点上下文
        knowledge_context = "\n".join([doc["content"] for doc in docs]) if docs else "暂无相关知识点"

        # 使用引导式教学prompt
        prompt = HOMEWORK_GUIDANCE_PROMPT.format(
            subject=subject,
            question=question,
            knowledge_context=knowledge_context
        )

        response = await self.llm_client.generate(prompt)

        return response
```

- [ ] **Step 4: 创建情绪疏导处理器 emotion.py**

```python
# src/agent/nodes/handlers/emotion.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.llm.client import get_llm_client
from config.prompts import EMOTION_SUPPORT_PROMPT


class EmotionHandler(BaseHandler):
    """情绪疏导处理器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理情绪疏导"""
        emotion_type = slots.get("emotion_type", "压力")

        # 从历史获取用户倾诉内容
        query = ""
        if history:
            for h in reversed(history):
                if h["role"] == "user":
                    query = h["content"]
                    break

        logger.info(f"情绪疏导: emotion_type={emotion_type}")

        prompt = EMOTION_SUPPORT_PROMPT.format(
            query=query,
            emotion_type=emotion_type
        )

        response = await self.llm_client.generate(prompt)

        return response
```

- [ ] **Step 5: 创建闲聊处理器 chitchat.py**

```python
# src/agent/nodes/handlers/chitchat.py

from typing import Dict, Any, List
from loguru import logger

from .base import BaseHandler
from src.llm.client import get_llm_client
from config.prompts import CHITCHAT_PROMPT


class ChitchatHandler(BaseHandler):
    """闲聊处理器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def handle(
        self,
        slots: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:
        """处理闲聊"""
        # 从历史获取用户输入
        query = ""
        if history:
            for h in reversed(history):
                if h["role"] == "user":
                    query = h["content"]
                    break

        logger.info(f"闲聊: query={query[:50]}...")

        prompt = CHITCHAT_PROMPT.format(query=query)

        response = await self.llm_client.generate(prompt)

        return response
```

- [ ] **Step 6: 创建handlers __init__.py**

```python
# src/agent/nodes/handlers/__init__.py

from .base import BaseHandler
from .study_qa import StudyQAHandler
from .homework import HomeworkHandler
from .emotion import EmotionHandler
from .chitchat import ChitchatHandler


# 处理器映射
HANDLERS = {
    "study_qa": StudyQAHandler,
    "homework_help": HomeworkHandler,
    "emotion_support": EmotionHandler,
    "chitchat": ChitchatHandler
}


def get_handler(intent: str) -> BaseHandler:
    """获取意图对应的处理器"""
    handler_cls = HANDLERS.get(intent, ChitchatHandler)
    return handler_cls()
```

- [ ] **Step 7: 提交意图处理器**

```bash
git add src/agent/nodes/handlers/
git commit -m "feat: add intent handlers"
```

---

## Task 14: Agent核心 - LangGraph状态图

**Files:**
- Create: `src/agent/graph.py`

- [ ] **Step 1: 创建Agent状态图 graph.py**

```python
# src/agent/graph.py

from typing import Dict, Any, Optional
from loguru import logger

from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes.intent_classifier import intent_classifier_node
from .nodes.slot_filler import slot_filler_node
from .nodes.slot_checker import slot_checker_node
from .nodes.router import router_node
from .nodes.handlers import get_handler
from src.conversation.session import get_session_manager
from src.conversation.history import ConversationHistory


def ask_missing_node(state: AgentState) -> Dict[str, Any]:
    """追问缺失槽位节点"""
    missing_slots = state.get("missing_slots", [])
    slots = state.get("slots", {})

    from config.prompts import ASK_MISSING_TEMPLATES

    if missing_slots:
        slot_name = missing_slots[0]
        question = ASK_MISSING_TEMPLATES.get(slot_name, f"请告诉我{slot_name}是什么？")

        return {"ask_question": question}

    return {"ask_question": "请提供更多信息"}


def create_handler_node(intent: str):
    """创建处理器节点工厂"""
    async def handler_node(state: AgentState) -> Dict[str, Any]:
        handler = get_handler(intent)

        slots = state.get("slots", {})
        history = state.get("history", [])

        response = await handler.handle(slots, history)

        return {"response": response}

    return handler_node


def build_graph() -> StateGraph:
    """构建Agent状态图"""
    # 创建状态图
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("slot_filler", slot_filler_node)
    graph.add_node("slot_checker", slot_checker_node)
    graph.add_node("ask_missing", ask_missing_node)
    graph.add_node("router", router_node)

    # 添加意图处理器节点
    graph.add_node("study_qa", create_handler_node("study_qa"))
    graph.add_node("homework_help", create_handler_node("homework_help"))
    graph.add_node("emotion_support", create_handler_node("emotion_support"))
    graph.add_node("chitchat", create_handler_node("chitchat"))

    # 设置入口
    graph.set_entry_point("intent_classifier")

    # 定义边
    graph.add_edge("intent_classifier", "slot_filler")
    graph.add_edge("slot_filler", "slot_checker")

    # 条件边：槽位检查
    graph.add_conditional_edges(
        "slot_checker",
        lambda state: "router" if state.get("slots_complete") else "ask_missing",
        {
            "router": "router",
            "ask_missing": "ask_missing"
        }
    )

    # ask_missing 结束
    graph.add_edge("ask_missing", END)

    # 条件边：路由到具体handler
    graph.add_conditional_edges(
        "router",
        lambda state: state.get("intent", "chitchat"),
        {
            "study_qa": "study_qa",
            "homework_help": "homework_help",
            "emotion_support": "emotion_support",
            "chitchat": "chitchat"
        }
    )

    # 所有handler结束
    for intent in ["study_qa", "homework_help", "emotion_support", "chitchat"]:
        graph.add_edge(intent, END)

    return graph


class AgentGraph:
    """Agent图执行器"""

    def __init__(self):
        self._graph = None
        self._session_manager = get_session_manager()

    @property
    def graph(self):
        if self._graph is None:
            self._graph = build_graph().compile()
        return self._graph

    async def run(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行Agent"""
        logger.info(f"Agent执行: query={query[:50]}...")

        # 获取或创建会话
        session = self._session_manager.get_or_create(session_id)

        # 构建初始状态
        initial_state: AgentState = {
            "query": query,
            "session_id": session.session_id,
            "history": [],
            "context": session.context
        }

        # 从会话获取历史
        if session.messages:
            initial_state["history"] = [
                {"role": msg.role, "content": msg.content}
                for msg in session.messages[-10:]  # 最近5轮
            ]

        # 执行图
        result = await self.graph.ainvoke(initial_state)

        # 更新会话
        session.touch()
        session.messages.append({
            "role": "user",
            "content": query,
            "intent": result.get("intent")
        })

        response = result.get("response") or result.get("ask_question", "抱歉，我无法理解您的问题。")

        session.messages.append({
            "role": "assistant",
            "content": response
        })

        return {
            "response": response,
            "intent": result.get("intent"),
            "slots": result.get("slots"),
            "session_id": session.session_id
        }


# 全局实例
_agent: Optional[AgentGraph] = None


def get_agent() -> AgentGraph:
    """获取Agent实例"""
    global _agent
    if _agent is None:
        _agent = AgentGraph()
    return _agent
```

- [ ] **Step 2: 提交Agent状态图**

```bash
git add src/agent/graph.py
git commit -m "feat: add LangGraph agent orchestration"
```

---

## Task 15: CLI命令行工具

**Files:**
- Create: `cli/main.py`

- [ ] **Step 1: 创建CLI主程序**

```python
# cli/main.py

import asyncio
import typer
from typer import Typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path
from typing import Optional, List

# 初始化
app = Typer(name="k12-assistant", help="K12智能学习助手")
console = Console()


@app.command()
def chat():
    """启动对话模式"""
    console.print(Panel.fit(
        "[bold green]K12智能学习助手[/bold green]\n"
        "输入问题开始对话，输入 'quit' 退出",
        title="欢迎"
    ))

    asyncio.run(_chat_loop())


async def _chat_loop():
    """对话循环"""
    from src.agent.graph import get_agent

    agent = get_agent()
    session_id = None

    while True:
        try:
            # 获取用户输入
            query = console.input("[bold blue]你:[/bold blue] ")

            if query.lower() in ["quit", "exit", "q"]:
                console.print("[yellow]再见！[/yellow]")
                break

            if not query.strip():
                continue

            # 调用Agent
            with console.status("[bold green]思考中...[/bold green]"):
                result = await agent.run(query, session_id)
                session_id = result["session_id"]

            # 显示响应
            console.print("\n[bold green]助手:[/bold green]")
            console.print(Markdown(result["response"]))
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]再见！[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


@app.command()
def upload(
    file_path: str = typer.Argument(..., help="文件路径"),
    subject: str = typer.Option(..., "--subject", "-s", help="学科"),
    grade: List[str] = typer.Option([], "--grade", "-g", help="年级"),
    title: str = typer.Option("", "--title", "-t", help="标题")
):
    """上传文档到知识库"""
    asyncio.run(_upload_document(file_path, subject, grade, title))


async def _upload_document(file_path: str, subject: str, grade: List[str], title: str):
    """上传文档"""
    from src.knowledge.manager import get_knowledge_manager

    if not Path(file_path).exists():
        console.print(f"[red]文件不存在: {file_path}[/red]")
        return

    manager = get_knowledge_manager()

    with console.status("[bold green]处理中...[/bold green]"):
        result = await manager.upload(
            file_path=file_path,
            subject=subject,
            grade_range=grade,
            title=title
        )

    console.print(f"[green]上传成功![/green]")
    console.print(f"  文档ID: {result.doc_id}")
    console.print(f"  切片数: {result.chunk_count}")


@app.command()
def list_docs(
    subject: str = typer.Option(None, "--subject", "-s", help="按学科筛选")
):
    """列出知识库文档"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()
    docs = manager.list(subject=subject)

    if not docs:
        console.print("[yellow]暂无文档[/yellow]")
        return

    from rich.table import Table
    table = Table(title="知识库文档")
    table.add_column("ID", style="cyan")
    table.add_column("文件名", style="green")
    table.add_column("学科", style="yellow")
    table.add_column("切片数", style="magenta")

    for doc in docs:
        table.add_row(
            doc.doc_id[:12] + "...",
            doc.filename,
            doc.subject,
            str(doc.chunk_count)
        )

    console.print(table)


@app.command()
def stats():
    """查看知识库统计"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()
    stats = manager.stats()

    console.print(Panel.fit(
        f"[bold]总文档数:[/bold] {stats['total_documents']}\n"
        f"[bold]总切片数:[/bold] {stats['total_chunks']}\n"
        f"[bold]存储大小:[/bold] {stats['storage_size_mb']} MB"
    ))

    if stats["by_subject"]:
        from rich.table import Table
        table = Table(title="学科分布")
        table.add_column("学科", style="cyan")
        table.add_column("文档数", style="green")
        table.add_column("切片数", style="yellow")

        for subject, data in stats["by_subject"].items():
            table.add_row(subject, str(data["docs"]), str(data["chunks"]))

        console.print(table)


@app.command()
def delete(doc_id: str = typer.Argument(..., help="文档ID")):
    """删除文档"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()

    if manager.delete(doc_id):
        console.print(f"[green]删除成功: {doc_id}[/green]")
    else:
        console.print(f"[red]文档不存在: {doc_id}[/red]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="主机地址"),
    port: int = typer.Option(8000, "--port", "-p", help="端口")
):
    """启动Web服务"""
    import uvicorn

    console.print(f"[green]启动Web服务: http://{host}:{port}[/green]")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: 提交CLI工具**

```bash
git add cli/
git commit -m "feat: add CLI tool"
```

---

## Task 16: FastAPI后端

**Files:**
- Create: `api/routes/chat.py`
- Create: `api/routes/knowledge.py`
- Create: `api/main.py`

- [ ] **Step 1: 创建聊天API chat.py**

```python
# api/routes/chat.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    slots: Optional[dict] = None
    session_id: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送消息"""
    from src.agent.graph import get_agent

    agent = get_agent()
    result = await agent.run(request.message, request.session_id)

    return ChatResponse(
        response=result["response"],
        intent=result.get("intent"),
        slots=result.get("slots"),
        session_id=result["session_id"]
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取对话历史"""
    from src.conversation.session import get_session_manager

    manager = get_session_manager()
    session = manager.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {"history": [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清空对话历史"""
    from src.conversation.session import get_session_manager

    manager = get_session_manager()
    manager.delete(session_id)

    return {"status": "success"}
```

- [ ] **Step 2: 创建知识库API knowledge.py**

```python
# api/routes/knowledge.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    subject: str = Form(...),
    grade: List[str] = Form(default=[]),
    title: str = Form(default="")
):
    """上传文档"""
    from src.knowledge.manager import get_knowledge_manager
    import tempfile
    import os

    # 检查文件类型
    allowed = [".pdf", ".docx", ".doc", ".txt", ".md"]
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
            subject=subject,
            grade_range=grade,
            title=title or file.filename
        )

        return {
            "status": "success",
            "doc_id": result.doc_id,
            "chunk_count": result.chunk_count
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
```

- [ ] **Step 3: 创建FastAPI主应用 main.py**

```python
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
```

- [ ] **Step 4: 提交FastAPI后端**

```bash
git add api/
git commit -m "feat: add FastAPI backend"
```

---

## Task 17: Web前端

**Files:**
- Create: `web/static/index.html`
- Create: `web/static/knowledge.html`
- Create: `web/static/css/style.css`
- Create: `web/static/css/chat.css`
- Create: `web/static/css/knowledge.css`
- Create: `web/static/js/api.js`
- Create: `web/static/js/app.js`
- Create: `web/static/js/knowledge.js`
- Create: `web/static/js/markdown.js`

- [ ] **Step 1: 创建主页面 index.html**

(内容见设计文档 13.3节)

- [ ] **Step 2: 创建知识库页面 knowledge.html**

(内容见设计文档 13.3节)

- [ ] **Step 3: 创建CSS样式文件**

(内容见设计文档 13.4节)

- [ ] **Step 4: 创建JavaScript文件**

(内容见设计文档 13.5节)

- [ ] **Step 5: 提交Web前端**

```bash
git add web/
git commit -m "feat: add web frontend"
```

---

## Task 18: 最终集成和测试

- [ ] **Step 1: 安装依赖**

```bash
pip install -e .
```

- [ ] **Step 2: 配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/ -v
```

- [ ] **Step 4: 启动服务测试**

```bash
# 启动Web服务
uvicorn api.main:app --reload

# 或使用CLI
python -m cli.main serve
```

- [ ] **Step 5: 提交最终代码**

```bash
git add .
git commit -m "feat: complete K12 study assistant system"
```

---

## 自检清单

完成所有任务后，请检查：

- [ ] 所有测试通过：`pytest tests/ -v`
- [ ] 服务可以启动：`uvicorn api.main:app`
- [ ] CLI可以运行：`python -m cli.main --help`
- [ ] 环境变量配置正确
- [ ] 文档已更新

---

**计划完成！**
