# RAG-KB 🤖

**一个基于 LangGraph 的教育问答 Agent，支持意图识别、混合检索、RAG 生成**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain.github.io/langgraph/)
[![Qwen](https://img.shields.io/badge/Qwen-Plus-blue.svg)](https://dashscope.console.aliyun.com/)

> 用 LangGraph 构建的智能问答 Agent，融合意图识别 + 混合检索 + RAG 生成，专为教育场景设计

---

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| 🎯 **意图识别** | 自动识别学科问答、作业辅导、情绪疏导、闲聊等意图 |
| 📝 **槽位填充** | 提取关键信息，支持多轮追问补全缺失槽位 |
| 🔍 **混合检索** | 向量检索 + 关键词检索混合，召回率提升 |
| 🤖 **RAG 生成** | 基于知识库的检索增强生成，确保答案准确 |
| 💬 **多轮对话** | 支持上下文记忆，维持对话连贯性 |
| 📚 **知识库管理** | PDF/DOCX/TXT 文档上传、自动切分、向量化 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                            │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 LangGraph Agent Orchestrator                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Intent      │  │  Slot        │  │  Router      │     │
│  │  Recognition │─▶│  Filling     │─▶│              │     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
└──────────────────────────────────────────────┼─────────────┘
                              │                 │
            ┌─────────────────┼─────────────────┼─────────────┐
            ▼                 ▼                 ▼             ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ Study QA    │  │ Homework    │  │ Emotion     │  │ Holiday     │
    │ (RAG检索)   │  │ Helper      │  │ Support     │  │ Tool        │
    └──────┬──────┘  └─────────────┘  └─────────────┘  └─────────────┘
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │              Hybrid Retrieval (RAG)                      │
    │      Vector Search (Chroma) + Keyword Search (BM25)    │
    └─────────────────────────────────────────────────────────┘
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │              LLM: Qwen-Plus (通义千问)                   │
    └─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 安装

```bash
pip install -e .
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY
```

### 3. 启动

```bash
python run.py web
# 打开 http://localhost:8000
```

> ⚡ **完成！** 立即体验智能问答

---

## 💬 对话示例

```yaml
用户: 勾股定理是什么？
Agent: 勾股定理是直角三角形的性质定理... [来自知识库RAG检索]

用户: 那这道题怎么做？已知a=3, b=4, 求c
Agent: 根据勾股定理 a² + b² = c²，代入得 c = √(9+16) = 5

用户: 考试没考好，心情不好
Agent: [情绪疏导模式] 我理解你的感受... [启动情绪支持流程]
```

---

## 🛠️ 技术栈

| 层级 | 技术选型 |
|------|----------|
| Agent 框架 | LangGraph 0.2+ |
| LLM | 通义千问 (Qwen-Plus) |
| Embedding | DashScope text-embedding-v2 |
| 向量数据库 | ChromaDB |
| 关键词索引 | BM25 (Whoosh) |
| Web 框架 | FastAPI + Uvicorn |
| CLI 框架 | Typer + Rich |
| 配置管理 | Pydantic Settings |

---

## 📁 项目结构

```
rag-kb/
├── config/
│   ├── prompts.py      # Agent Prompts 模板
│   └── settings.py     # 配置管理
├── src/
│   ├── agent/          # Agent 核心
│   │   ├── state.py    # 状态机定义
│   │   └── tools/      # 工具集
│   ├── rag/           # RAG 引擎
│   │   ├── engine.py   # RAG 编排
│   │   ├── retriever.py # 检索器
│   │   ├── reranker.py  # 重排
│   │   └── generator.py # 生成器
│   ├── knowledge/     # 知识库管理
│   │   ├── manager.py  # 知识库管理
│   │   └── splitter.py # 文档切分
│   ├── storage/       # 存储层
│   │   ├── vector_store.py  # 向量存储
│   │   ├── keyword_index.py # 关键词索引
│   │   └── session_db.py    # 会话存储
│   └── llm/           # LLM 封装
│       ├── client.py   # LLM 客户端
│       └── embeddings.py # Embedding
├── api/               # FastAPI 接口
│   ├── main.py        # 应用入口
│   └── routes/        # 路由
│       ├── chat.py     # 对话接口
│       └── knowledge.py # 知识库接口
├── cli/               # 命令行工具
├── web/               # 前端页面
│   ├── index.html     # 对话页面
│   └── knowledge.html # 知识库页面
└── tests/             # 单元测试
```

---

## 🔧 使用方式

### Web 服务

```bash
python run.py web
# 访问 http://localhost:8000
```

### CLI 对话模式

```bash
python run.py cli
```

### CLI 知识库管理

```bash
# 上传文档
python -m cli.main knowledge upload ./docs/math.pdf --subject 数学

# 查看知识库
python -m cli.main knowledge list
```

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 License

MIT License
