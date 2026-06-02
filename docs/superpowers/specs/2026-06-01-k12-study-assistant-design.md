# K12智能学习助手系统设计文档

> 版本: 1.0
> 日期: 2026-06-01
> 作者: Claude Design Assistant

---

## 一、项目概述

### 1.1 项目背景

本项目是一个K12学生学习助手系统，旨在帮助学生解决学习上的问题和情绪困扰。作为个人练习项目，目标是实现一个功能完整的Agent编排系统，掌握现代AI Agent开发范式。

### 1.2 核心功能

| 功能模块 | 描述 |
|----------|------|
| 意图识别 | 识别用户输入的意图类型（学科问答、作业辅导、情绪疏导、闲聊等） |
| 槽位填充 | 从用户输入中提取关键信息，支持多轮追问补全缺失槽位 |
| 向量混合检索 | 结合向量检索和关键词检索，提升知识库召回率 |
| RAG问答 | 基于检索增强生成的知识问答能力 |
| 知识库管理 | 支持文件上传、文档切分、向量化嵌入的知识库构建 |

### 1.3 技术选型

| 层级 | 技术选型 |
|------|----------|
| Agent框架 | LangGraph 0.2+ |
| LLM | 阿里云通义千问 (Qwen-Plus/Qwen-Max) |
| Embedding | DashScope text-embedding-v2 |
| 向量存储 | Chroma (向量) + Whoosh (关键词BM25) |
| 文档处理 | PyMuPDF, python-docx, LangChain TextSplitter |
| CLI框架 | Typer + Rich |
| Web后端 | FastAPI |
| Web前端 | HTML + CSS + JavaScript (原生) |
| 配置管理 | Pydantic Settings |
| 日志 | Loguru |

---

## 二、系统架构

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI Interface                            │
│                    (命令行交互入口)                               │
├───────────────────────────┬──────────────────────────────────────┤
│      对话模式              │           管理模式                   │
│   (学生提问交互)           │    (上传文档/管理知识库)             │
└───────────────────────────┴──────────────────────────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│  LangGraph Agent        │   │   Knowledge Manager      │
│  Orchestrator           │   │   (知识库管理模块)        │
│                         │   │  - 文件上传              │
│  ┌───────────────────┐  │   │  - 文档切分              │
│  │ 意图识别→槽位填充  │  │   │  - 向量化嵌入            │
│  │       ↓           │  │   │  - 知识库CRUD            │
│  │ 路由分发到各意图   │  │   └──────────────────────────┘
│  │  ├─ 学科问答      │  │
│  │  ├─ 作业辅导      │  │              │
│  │  ├─ 情绪疏导      │  │              ▼
│  │  └─ 闲聊          │  │   ┌──────────────────────────┐
│  └───────────────────┘  │   │   Chroma Vector Store    │
└─────────────────────────┘   │   + Whoosh Keyword Index │
              │               └──────────────────────────┘
              ▼                           ▲
┌─────────────────────────┐               │
│  RAG检索工具            │───────────────┘
│  (被学科问答调用)        │
└─────────────────────────┘
              │
              ▼
┌─────────────────────────┐
│  LLM (通义千问)          │
└─────────────────────────┘
```

### 2.2 核心设计原则

1. **Agent编排清晰**: 使用LangGraph状态图管理对话流程，状态流转可视化
2. **模块解耦**: 各功能模块独立，通过接口交互
3. **检索增强**: 向量检索+关键词检索混合，提升召回率
4. **可扩展性**: 易于添加新意图、新工具、新知识源

---

## 三、意图识别模块

### 3.1 支持的意图类型

| 意图 | 标识 | 描述 | 示例Query |
|------|------|------|-----------|
| 学科问答 | `study_qa` | 学科知识问答 | "勾股定理怎么用？" |
| 作业辅导 | `homework_help` | 作业辅导 | "这道题怎么做？" |
| 情绪疏导 | `emotion_support` | 情绪疏导 | "考试没考好很难过" |
| 闲聊 | `chitchat` | 日常闲聊 | "你好呀" |

### 3.2 意图识别流程

```
用户Query → 预处理(清洗、分词) → LLM意图分类 → 返回(intent + score)
```

### 3.3 Prompt模板

```python
INTENT_CLASSIFICATION_PROMPT = """
你是一个意图识别助手，需要判断学生输入的意图类别。

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

请输出意图类别（只输出类别名称，不要解释）:
"""
```

---

## 四、槽位填充模块

### 4.1 各意图槽位定义

#### 学科问答 (study_qa)

| 槽位名称 | 类型 | 必填 | 描述 |
|----------|------|------|------|
| subject | enum | 是 | 学科：语文/数学/英语/物理/化学/生物/历史/地理/政治 |
| grade | enum | 否 | 年级：小学/初一/初二/初三/高一/高二/高三 |
| topic | string | 是 | 具体知识点/问题 |

#### 作业辅导 (homework_help)

| 槽位名称 | 类型 | 必填 | 描述 |
|----------|------|------|------|
| subject | enum | 是 | 学科 |
| question | string | 是 | 具体题目内容 |
| image_url | string | 否 | 图片URL（如有） |

#### 情绪疏导 (emotion_support)

| 槽位名称 | 类型 | 必填 | 描述 |
|----------|------|------|------|
| emotion_type | enum | 否 | 情绪类型：焦虑/沮丧/愤怒/迷茫/压力 |
| context | string | 否 | 具体原因/背景 |

### 4.2 槽位填充流程

```
┌──────────────┐
│ 提取槽位(LLM) │
└──────┬───────┘
       │
       ▼
┌──────────────┐     槽位完整     ┌──────────────┐
│ 检查缺失槽位  │─────────────────▶│ 返回填充结果  │
└──────┬───────┘                  └──────────────┘
       │ 缺失
       ▼
┌──────────────┐
│ 生成追问反问  │
└──────────────┘
```

### 4.3 槽位提取Prompt模板

```python
SLOT_FILLING_PROMPT = """
你是一个槽位提取助手。根据用户输入，提取以下槽位信息。

【意图类型】{intent}
【槽位定义】
{slot_definition}

【用户输入】
{query}

【历史对话】
{history}

请以JSON格式输出提取的槽位，缺失的槽位填null:
"""
```

---

## 五、LangGraph状态图设计

### 5.1 状态定义

```python
class AgentState(TypedDict):
    query: str                    # 用户原始输入
    intent: str                   # 识别的意图
    slots: dict                   # 槽位信息
    slots_complete: bool          # 槽位是否完整
    missing_slots: list           # 缺失的槽位
    ask_question: str             # 追问内容
    response: str                 # 最终响应
    history: list                 # 对话历史
```

### 5.2 状态图定义

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)

# 添加节点
graph.add_node("intent_classifier", intent_classifier_node)
graph.add_node("slot_filler", slot_filler_node)
graph.add_node("slot_checker", slot_checker_node)
graph.add_node("ask_missing", ask_missing_node)
graph.add_node("router", router_node)
graph.add_node("study_qa", study_qa_node)
graph.add_node("homework_help", homework_help_node)
graph.add_node("emotion_support", emotion_support_node)
graph.add_node("chitchat", chitchat_node)

# 定义入口
graph.set_entry_point("intent_classifier")

# 定义边
graph.add_edge("intent_classifier", "slot_filler")
graph.add_edge("slot_filler", "slot_checker")

# 条件边：检查槽位是否完整
graph.add_conditional_edges(
    "slot_checker",
    lambda state: "router" if state["slots_complete"] else "ask_missing",
    {
        "router": "router",
        "ask_missing": "ask_missing"
    }
)

# 条件边：路由到具体handler
graph.add_conditional_edges(
    "router",
    lambda state: state["intent"],
    {
        "study_qa": "study_qa",
        "homework_help": "homework_help",
        "emotion_support": "emotion_support",
        "chitchat": "chitchat"
    }
)

# 所有handler结束
graph.add_edge("study_qa", END)
graph.add_edge("homework_help", END)
graph.add_edge("emotion_support", END)
graph.add_edge("chitchat", END)
```

### 5.3 状态流转图

```
START → intent_classifier → slot_filler → slot_checker
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      │ 槽位完整？                                │
                      ├─Yes───────────────────No─────────────────┤
                      ▼                                           ▼
                   router                                   ask_missing
                      │                                           │
         ┌────────────┼────────────┬────────────┐                │
         ▼            ▼            ▼            ▼                │
     study_qa   homework_help emotion    chitchat                │
         │            │     support        │                      │
         └────────────┴────────────┴────────┴────────────────────┘
                      │
                      ▼
                     END
```

---

## 六、意图处理器设计

### 6.1 学科问答处理器 (StudyQAHandler)

**输入**: `{subject, grade, topic}`

**处理流程**:
1. 构建检索Query (topic + subject + grade)
2. 调用RAG检索工具
   - 向量相似度检索
   - 关键词检索 (BM25)
   - 混合排序
3. 构建Prompt (检索结果 + 用户问题)
4. LLM生成回答
   - 结构化输出 (知识点+例题+总结)
   - 适配年级理解能力

**输出结构**:
```json
{
    "knowledge_point": "函数单调性的定义和判断方法",
    "explanation": "通俗解释，适配年级...",
    "examples": [
        {
            "title": "例题1",
            "content": "判断函数f(x)=x²在(0,+∞)上的单调性",
            "solution": "详细解答步骤..."
        }
    ],
    "tips": "记忆技巧或易错点提醒",
    "related_topics": ["函数奇偶性", "二次函数"]
}
```

### 6.2 作业辅导处理器 (HomeworkHandler)

**输入**: `{subject, question, image_url?}`

**处理流程**:
1. 题目理解
   - 如有图片: 调用多模态模型识别题目
   - 提取题目关键信息
2. 知识点定位
   - 调用RAG检索相关知识点
3. 解题思路引导 (启发式，不直接给答案)
   - Step1: 分析题目考查点
   - Step2: 引导思考方向
   - Step3: 逐步提示
4. 完整解答 (用户请求时提供)

**引导式教学Prompt**:
```python
HOMEWORK_GUIDANCE_PROMPT = """
你是一位耐心的K12辅导老师。请用启发式方法引导学生解题，不要直接给出答案。

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

注意: 保持鼓励和耐心的语气。
"""
```

### 6.3 情绪疏导处理器 (EmotionHandler)

**输入**: `{emotion_type?, context?}`

**处理流程**:
1. 情绪识别与分析 → 判断情绪类型和严重程度
2. 共情回应 → 表达理解和接纳
3. 引导倾诉 → 开放式提问，鼓励表达
4. 建议/疏导
   - 学习方法调整建议
   - 压力缓解技巧
   - 严重情况提醒寻求专业帮助

**情绪类型与应对策略**:

| 情绪类型 | 应对策略 |
|----------|----------|
| 焦虑 | 认可感受 + 拆解问题 + 关注当下 |
| 沮丧 | 共情倾听 + 重新框架 + 小步目标 |
| 压力 | 理解支持 + 时间管理 + 休息建议 |
| 迷茫 | 探索原因 + 帮助梳理 + 明确方向 |
| 愤怒 | 接纳情绪 + 引导表达 + 寻找原因 |

### 6.4 闲聊处理器 (ChitchatHandler)

**输入**: `{query}`

**处理**: 直接调用LLM进行友好对话

**特点**:
- 轻松友好的语气
- 可以聊学习之外的话题
- 适当引导回到学习话题

---

## 七、RAG检索模块

### 7.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                       RAG Engine                            │
├─────────────────────────────────────────────────────────────┤
│  Query Layer: Query改写 | Query扩展 | 假设问答生成          │
├─────────────────────────────────────────────────────────────┤
│  Retrieval Layer:                                           │
│    ┌─────────────┐              ┌─────────────┐             │
│    │ 向量检索    │              │ 关键词检索  │             │
│    │ (Chroma)    │              │ (BM25)      │             │
│    └──────┬──────┘              └──────┬──────┘             │
│           └────────────┬───────────────┘                    │
│                        ↓                                    │
│                ┌─────────────┐                              │
│                │ RRF混合融合  │                              │
│                └──────┬──────┘                              │
├───────────────────────┴─────────────────────────────────────┤
│  Rerank Layer: 相关性打分 | 多样性过滤 | Top-K截断          │
├─────────────────────────────────────────────────────────────┤
│  Generation Layer: Context组装 → Prompt构建 → LLM生成       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Query处理层

| 组件 | 功能 | 示例 |
|------|------|------|
| Query改写 | 将模糊query改写为清晰query | "这个怎么做" → "如何求解一元二次方程" |
| Query扩展 | 生成同义query提升召回 | "函数单调性" → ["函数单调性", "函数增减性"] |
| 假设问答生成 | 生成潜在问答对辅助检索 | 根据query生成可能的Q&A |

### 7.3 混合检索实现

#### 向量检索

```python
class VectorRetriever:
    def __init__(self, collection_name: str = "knowledge_base"):
        self.client = chromadb.PersistentClient(path="./data/chroma")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = DashScopeEmbeddings()

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_embedding = await self.embedder.embed(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        return self._format_results(results)
```

#### 关键词检索 (BM25)

```python
class KeywordRetriever:
    def __init__(self, index_path: str = "./data/bm25_index"):
        self.index_path = index_path
        self.ix = None
        self._init_index()

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        from whoosh.qparser import QueryParser
        with self.ix.searcher() as searcher:
            parser = QueryParser("content", self.ix.schema)
            q = parser.parse(query)
            results = searcher.search(q, limit=top_k)
            return [{"doc_id": r["doc_id"], "score": r.score,
                     "content": r["content"]} for r in results]
```

#### RRF混合融合

```python
class HybridRetriever:
    def __init__(self, vector_retriever, keyword_retriever, k: int = 60):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.k = k  # RRF参数

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        # 并行执行两种检索
        vector_results, keyword_results = await asyncio.gather(
            self.vector_retriever.search(query, top_k * 2),
            self.keyword_retriever.search(query, top_k * 2)
        )

        # RRF融合
        scores = {}
        for rank, doc in enumerate(vector_results):
            doc_id = doc["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.k + rank + 1)

        for rank, doc in enumerate(keyword_results):
            doc_id = doc["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.k + rank + 1)

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
```

### 7.4 生成层Prompt

```python
RAG_PROMPT = """
你是一位专业的K12学习辅导老师。请根据参考知识回答学生的问题。

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

请开始回答:
"""
```

---

## 八、知识库管理模块

### 8.1 支持的文件格式

| 格式 | 解析方式 | 说明 |
|------|----------|------|
| PDF | PyMuPDF | 支持扫描件OCR |
| Word | python-docx | .docx格式 |
| TXT | 原生读取 | 纯文本文件 |
| Markdown | markdown解析 | 保留结构信息 |
| JSON | json解析 | 结构化知识 |

### 8.2 文档切分策略

```python
class DocumentSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " "]
```

**切分参数**:
- chunk_size: 500字符
- chunk_overlap: 50字符
- separators: 按优先级递归切分

### 8.3 元数据设计

```python
@dataclass
class DocumentMetadata:
    doc_id: str                    # 文档唯一ID
    filename: str                  # 原始文件名
    file_type: str                 # 文件类型
    subject: str                   # 学科
    grade_range: list[str]         # 适用年级
    title: str                     # 文档标题
    keywords: list[str]            # 关键词标签
    chunk_count: int               # 切分块数
    create_time: datetime          # 创建时间
    update_time: datetime          # 更新时间
```

### 8.4 向量化嵌入流程

```
DocumentChunk List
       │
       ▼
┌──────────────┐
│ 批量处理     │  batch_size = 20
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Embedding    │  DashScope text-embedding-v2
│ API调用      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 向量存储     │  Chroma + Whoosh
└──────────────┘
```

### 8.5 知识库管理接口

```python
class KnowledgeManager:
    async def upload(self, file_path: str, subject: str,
                     grade_range: list[str] = None) -> UploadResult:
        """上传文档到知识库"""
        pass

    async def list(self, subject: str = None) -> list[DocumentInfo]:
        """查询知识库文档列表"""
        pass

    async def delete(self, doc_id: str) -> bool:
        """删除文档及其所有切片"""
        pass

    async def search(self, query: str, subject: str = None,
                     top_k: int = 5) -> list[SearchResult]:
        """搜索知识库"""
        pass

    async def stats(self) -> KnowledgeStats:
        """获取知识库统计信息"""
        pass
```

### 8.6 CLI命令设计

```bash
# 上传文档
$ python main.py knowledge upload ./docs/math.pdf --subject 数学 --grade 高一

# 列出所有文档
$ python main.py knowledge list

# 搜索知识
$ python main.py knowledge search "勾股定理" --subject 数学

# 删除文档
$ python main.py knowledge delete doc_001

# 查看统计
$ python main.py knowledge stats
```

---

## 九、对话管理模块

### 9.1 会话状态

```python
@dataclass
class Session:
    session_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message]
    current_intent: str
    current_slots: dict
```

### 9.2 对话历史管理

```python
class ConversationHistory:
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: list[Message] = []

    def add_user_message(self, content: str, intent: str = None,
                         slots: dict = None):
        """添加用户消息"""
        pass

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        pass

    def get_context(self, turns: int = None) -> str:
        """获取对话上下文"""
        pass
```

### 9.3 多轮对话上下文传递

- 同类意图（学科问答、作业辅导）可继承槽位
- 槽位有TTL机制（3轮有效）
- 支持意图切换时的上下文保留

---

## 十、项目目录结构

```
k12-study-assistant/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py                    # 配置管理
│   └── prompts.py                     # Prompt模板
│
├── src/
│   ├── __init__.py
│   │
│   ├── agent/                         # Agent模块
│   │   ├── __init__.py
│   │   ├── graph.py                   # LangGraph状态图
│   │   ├── state.py                   # 状态定义
│   │   └── nodes/                     # 节点实现
│   │       ├── __init__.py
│   │       ├── intent_classifier.py
│   │       ├── slot_filler.py
│   │       ├── router.py
│   │       └── handlers/
│   │           ├── study_qa.py
│   │           ├── homework.py
│   │           ├── emotion.py
│   │           └── chitchat.py
│   │
│   ├── rag/                           # RAG模块
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   ├── generator.py
│   │   └── query_processor.py
│   │
│   ├── knowledge/                     # 知识库管理
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── loader/
│   │   ├── splitter.py
│   │   └── embedder.py
│   │
│   ├── storage/                       # 存储层
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   ├── keyword_index.py
│   │   └── metadata_store.py
│   │
│   ├── llm/                           # LLM模块
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── embeddings.py
│   │
│   ├── conversation/                  # 对话管理
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── history.py
│   │   └── context.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
│
├── cli/                               # CLI入口
│   ├── __init__.py
│   ├── main.py
│   ├── chat.py
│   └── knowledge.py
│
├── data/                              # 数据目录
│   ├── chroma/
│   ├── bm25_index/
│   ├── knowledge/
│   └── metadata/
│
├── logs/
│
├── tests/
│   ├── test_agent/
│   ├── test_rag/
│   └── test_knowledge/
│
└── docs/
    ├── architecture.md
    └── api.md
```

---

## 十一、依赖清单

```toml
[project]
name = "k12-study-assistant"
version = "1.0.0"
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
    "markdown>=3.5.0",

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
```

---

## 十二、核心接口定义

### 12.1 Agent接口

```python
class BaseNode(ABC):
    @abstractmethod
    async def __call__(self, state: AgentState) -> AgentState:
        pass

class BaseHandler(ABC):
    @abstractmethod
    async def handle(self, slots: dict, history: list) -> str:
        pass
```

### 12.2 RAG接口

```python
class BaseRetriever(ABC):
    @abstractmethod
    async def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        pass

class RAGEngine:
    async def retrieve(self, query: str, top_k: int = 5,
                       filters: dict = None) -> list[SearchResult]:
        pass

    async def generate(self, query: str, docs: list[SearchResult],
                       **kwargs) -> str:
        pass
```

### 12.3 存储接口

```python
class VectorStore(ABC):
    async def add(self, ids: list[str], embeddings: list[list[float]],
                  documents: list[str], metadatas: list[dict]):
        pass

    async def search(self, embedding: list[float], top_k: int,
                     filters: dict = None) -> list[SearchResult]:
        pass

    async def delete(self, ids: list[str]):
        pass

class KeywordIndex(ABC):
    async def add(self, docs: list[DocumentChunk]):
        pass

    async def search(self, query: str, top_k: int) -> list[SearchResult]:
        pass

    async def delete(self, doc_ids: list[str]):
        pass
```

---

## 十三、Web前端设计 (自定义搭建)

### 13.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          前端 (浏览器)                              │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    HTML + CSS + JavaScript                   │  │
│   │                                                             │  │
│   │   页面:                                                      │  │
│   │   - index.html        (对话页面)                            │  │
│   │   - knowledge.html    (知识库管理页面)                       │  │
│   │                                                             │  │
│   │   样式:                                                      │  │
│   │   - css/style.css     (主样式)                              │  │
│   │                                                             │  │
│   │   交互:                                                      │  │
│   │   - js/app.js         (主逻辑)                              │  │
│   │   - js/api.js         (API调用)                             │  │
│   │   - js/markdown.js    (Markdown渲染)                        │  │
│   │                                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                 │                                   │
│                                 │ HTTP/WebSocket                    │
│                                 ▼                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       后端 (FastAPI)                                │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                      API Routes                              │  │
│   │                                                             │  │
│   │   POST /api/chat           发送消息                         │  │
│   │   POST /api/chat/stream    流式响应                         │  │
│   │   GET  /api/history        获取对话历史                      │  │
│   │   DELETE /api/history      清空对话历史                      │  │
│   │                                                             │  │
│   │   POST /api/knowledge/upload    上传文档                    │  │
│   │   GET  /api/knowledge/list      文档列表                    │  │
│   │   DELETE /api/knowledge/{id}    删除文档                    │  │
│   │   GET  /api/knowledge/stats     统计信息                    │  │
│   │                                                             │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                 │                                   │
│                                 ▼                                   │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                   Agent Core                                 │  │
│   │           (LangGraph + RAG + Knowledge)                     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.2 FastAPI后端设计

#### API路由定义

```python
# api/routes/chat.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str
    intent: Optional[str] = None
    slots: Optional[dict] = None
    session_id: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送消息并获取响应"""
    from src.agent.graph import AgentGraph

    agent = AgentGraph()
    result = await agent.run(
        query=request.message,
        session_id=request.session_id
    )

    return ChatResponse(
        response=result["response"],
        intent=result.get("intent"),
        slots=result.get("slots"),
        session_id=result["session_id"]
    )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式响应"""
    from src.agent.graph import AgentGraph

    agent = AgentGraph()

    async def generate():
        async for chunk in agent.run_stream(
            query=request.message,
            session_id=request.session_id
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/history")
async def get_history(session_id: str):
    """获取对话历史"""
    from src.conversation.session import SessionManager

    manager = SessionManager()
    history = await manager.get_history(session_id)
    return {"history": history}


@router.delete("/history")
async def clear_history(session_id: str):
    """清空对话历史"""
    from src.conversation.session import SessionManager

    manager = SessionManager()
    await manager.clear(session_id)
    return {"status": "success"}
```

```python
# api/routes/knowledge.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    subject: str = Form(...),
    grade: List[str] = Form(default=[]),
    title: str = Form(default="")
):
    """上传文档到知识库"""
    from src.knowledge.manager import KnowledgeManager

    # 检查文件类型
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    manager = KnowledgeManager()

    # 保存临时文件
    content = await file.read()
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)

    # 上传处理
    result = await manager.upload(
        file_path=temp_path,
        subject=subject,
        grade_range=grade,
        title=title or file.filename
    )

    return {
        "status": "success",
        "doc_id": result.doc_id,
        "chunk_count": result.chunk_count
    }


@router.get("/list")
async def list_documents(subject: Optional[str] = None):
    """获取文档列表"""
    from src.knowledge.manager import KnowledgeManager

    manager = KnowledgeManager()
    documents = await manager.list(subject=subject)

    return {"documents": documents}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    from src.knowledge.manager import KnowledgeManager

    manager = KnowledgeManager()
    success = await manager.delete(doc_id)

    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=404, detail="文档不存在")


@router.get("/stats")
async def get_stats():
    """获取知识库统计"""
    from src.knowledge.manager import KnowledgeManager

    manager = KnowledgeManager()
    stats = await manager.stats()

    return stats
```

#### 主应用入口

```python
# api/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, knowledge

app = FastAPI(
    title="K12智能学习助手",
    description="K12学生学习助手API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(knowledge.router)

# 静态文件服务
app.mount("/static", StaticFiles(directory="web/static"), name="static")


@app.get("/")
async def index():
    """主页"""
    return FileResponse("web/static/index.html")


@app.get("/knowledge")
async def knowledge_page():
    """知识库管理页面"""
    return FileResponse("web/static/knowledge.html")
```

### 13.3 前端页面设计

#### 对话页面 (index.html)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K12智能学习助手</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="/static/css/chat.css">
</head>
<body>
    <div class="container">
        <!-- 侧边栏 -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <h1 class="logo">🎓 K12学习助手</h1>
            </div>

            <button class="new-chat-btn" id="newChatBtn">
                <span>➕</span> 新建对话
            </button>

            <nav class="nav-menu">
                <a href="/" class="nav-item active">
                    <span>💬</span> 对话
                </a>
                <a href="/knowledge" class="nav-item">
                    <span>📚</span> 知识库
                </a>
            </nav>

            <div class="history-section">
                <h3>历史对话</h3>
                <ul class="history-list" id="historyList">
                    <!-- 动态加载 -->
                </ul>
            </div>
        </aside>

        <!-- 主聊天区域 -->
        <main class="chat-main">
            <header class="chat-header">
                <h2>学习助手</h2>
                <div class="header-actions">
                    <button id="clearBtn" class="icon-btn" title="清空对话">🗑️</button>
                </div>
            </header>

            <!-- 消息区域 -->
            <div class="messages-container" id="messagesContainer">
                <!-- 欢迎消息 -->
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
            </div>

            <!-- 输入区域 -->
            <div class="input-container">
                <div class="input-wrapper">
                    <textarea
                        id="messageInput"
                        placeholder="请输入你的问题..."
                        rows="1"
                    ></textarea>
                    <button id="sendBtn" class="send-btn">
                        <span>发送</span>
                    </button>
                </div>
                <p class="input-hint">按 Enter 发送，Shift + Enter 换行</p>
            </div>
        </main>
    </div>

    <script src="/static/js/api.js"></script>
    <script src="/static/js/markdown.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

#### 知识库管理页面 (knowledge.html)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知识库管理 - K12智能学习助手</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="/static/css/knowledge.css">
</head>
<body>
    <div class="container">
        <!-- 侧边栏 (同对话页面) -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <h1 class="logo">🎓 K12学习助手</h1>
            </div>

            <nav class="nav-menu">
                <a href="/" class="nav-item">
                    <span>💬</span> 对话
                </a>
                <a href="/knowledge" class="nav-item active">
                    <span>📚</span> 知识库
                </a>
            </nav>
        </aside>

        <!-- 主内容区域 -->
        <main class="knowledge-main">
            <header class="page-header">
                <h2>📚 知识库管理</h2>
            </header>

            <!-- 上传区域 -->
            <section class="upload-section card">
                <h3>📤 上传文档</h3>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <p>拖拽文件到此处，或点击选择文件</p>
                    <input type="file" id="fileInput" accept=".pdf,.docx,.txt,.md" hidden>
                    <p class="file-types">支持: PDF, Word, TXT, Markdown</p>
                </div>

                <div class="upload-form" id="uploadForm" style="display: none;">
                    <div class="form-row">
                        <div class="form-group">
                            <label>学科</label>
                            <select id="subjectSelect">
                                <option value="数学">数学</option>
                                <option value="语文">语文</option>
                                <option value="英语">英语</option>
                                <option value="物理">物理</option>
                                <option value="化学">化学</option>
                                <option value="生物">生物</option>
                                <option value="历史">历史</option>
                                <option value="地理">地理</option>
                                <option value="政治">政治</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>适用年级</label>
                            <select id="gradeSelect" multiple>
                                <option value="小学">小学</option>
                                <option value="初一">初一</option>
                                <option value="初二">初二</option>
                                <option value="初三">初三</option>
                                <option value="高一">高一</option>
                                <option value="高二">高二</option>
                                <option value="高三">高三</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>文档标题</label>
                            <input type="text" id="titleInput" placeholder="如：函数知识点总结">
                        </div>
                    </div>
                    <button class="primary-btn" id="uploadBtn">上传并处理</button>
                </div>
            </section>

            <!-- 文档列表 -->
            <section class="documents-section card">
                <div class="section-header">
                    <h3>📋 文档列表</h3>
                    <select id="filterSubject" class="filter-select">
                        <option value="">全部学科</option>
                        <option value="数学">数学</option>
                        <option value="物理">物理</option>
                        <option value="化学">化学</option>
                    </select>
                </div>

                <table class="documents-table">
                    <thead>
                        <tr>
                            <th>文档名称</th>
                            <th>学科</th>
                            <th>切片数</th>
                            <th>上传时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="documentsList">
                        <!-- 动态加载 -->
                    </tbody>
                </table>
            </section>

            <!-- 统计信息 -->
            <section class="stats-section card">
                <h3>📊 统计信息</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="totalDocs">0</div>
                        <div class="stat-label">总文档数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="totalChunks">0</div>
                        <div class="stat-label">总切片数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="storageSize">0 MB</div>
                        <div class="stat-label">存储大小</div>
                    </div>
                </div>

                <div class="subject-stats" id="subjectStats">
                    <!-- 动态加载学科分布 -->
                </div>
            </section>
        </main>
    </div>

    <script src="/static/js/api.js"></script>
    <script src="/static/js/knowledge.js"></script>
</body>
</html>
```

### 13.4 CSS样式设计

```css
/* web/static/css/style.css */

/* ===== 基础变量 ===== */
:root {
    --primary-color: #4A90D9;
    --primary-hover: #357ABD;
    --bg-color: #f5f7fa;
    --sidebar-bg: #1a1f2e;
    --card-bg: #ffffff;
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
    --border-color: #e0e0e0;
    --user-bubble: #4A90D9;
    --assistant-bubble: #f0f0f0;
    --success-color: #4CAF50;
    --error-color: #f44336;
    --shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* ===== 重置样式 ===== */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-primary);
    line-height: 1.6;
}

/* ===== 布局 ===== */
.container {
    display: flex;
    height: 100vh;
}

/* ===== 侧边栏 ===== */
.sidebar {
    width: 260px;
    background-color: var(--sidebar-bg);
    color: white;
    display: flex;
    flex-direction: column;
    padding: 20px;
}

.logo {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 20px;
}

.new-chat-btn {
    width: 100%;
    padding: 12px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.2s;
}

.new-chat-btn:hover {
    background-color: var(--primary-hover);
}

.nav-menu {
    margin-top: 20px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    border-radius: 8px;
    transition: all 0.2s;
}

.nav-item:hover,
.nav-item.active {
    background-color: rgba(255, 255, 255, 0.1);
    color: white;
}

.history-section {
    margin-top: 30px;
    flex: 1;
    overflow-y: auto;
}

.history-section h3 {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 10px;
}

.history-list {
    list-style: none;
}

.history-item {
    padding: 10px 12px;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
    border-radius: 6px;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-item:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

/* ===== 卡片 ===== */
.card {
    background-color: var(--card-bg);
    border-radius: 12px;
    padding: 24px;
    box-shadow: var(--shadow);
    margin-bottom: 20px;
}

/* ===== 按钮样式 ===== */
.primary-btn {
    padding: 10px 24px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.2s;
}

.primary-btn:hover {
    background-color: var(--primary-hover);
}

.primary-btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.icon-btn {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    padding: 8px;
    border-radius: 6px;
    transition: background-color 0.2s;
}

.icon-btn:hover {
    background-color: var(--assistant-bubble);
}

/* ===== 表单 ===== */
.form-group {
    flex: 1;
}

.form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    font-size: 1rem;
}

.form-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
    .sidebar {
        width: 60px;
        padding: 10px;
    }

    .logo span,
    .nav-item span:last-child {
        display: none;
    }
}
```

```css
/* web/static/css/chat.css */

/* ===== 聊天主区域 ===== */
.chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: var(--bg-color);
}

.chat-header {
    padding: 16px 24px;
    background-color: var(--card-bg);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-header h2 {
    font-size: 1.2rem;
}

/* ===== 消息容器 ===== */
.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
}

/* ===== 欢迎消息 ===== */
.welcome-message {
    text-align: center;
    padding: 60px 20px;
}

.welcome-icon {
    font-size: 4rem;
    margin-bottom: 20px;
}

.welcome-message h2 {
    font-size: 1.8rem;
    margin-bottom: 12px;
}

.welcome-message p {
    color: var(--text-secondary);
    margin-bottom: 30px;
}

.quick-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
}

.quick-btn {
    padding: 12px 20px;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.95rem;
    transition: all 0.2s;
}

.quick-btn:hover {
    border-color: var(--primary-color);
    color: var(--primary-color);
}

/* ===== 消息气泡 ===== */
.message {
    display: flex;
    margin-bottom: 16px;
    gap: 12px;
}

.message.user {
    flex-direction: row-reverse;
}

.message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}

.message.user .message-avatar {
    background-color: var(--primary-color);
}

.message.assistant .message-avatar {
    background-color: var(--assistant-bubble);
}

.message-content {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 16px;
    line-height: 1.6;
}

.message.user .message-content {
    background-color: var(--user-bubble);
    color: white;
    border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
    background-color: var(--assistant-bubble);
    border-bottom-left-radius: 4px;
}

/* Markdown 内容样式 */
.message-content h3 {
    margin: 12px 0 8px;
}

.message-content code {
    background-color: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
}

.message-content pre {
    background-color: #1a1a1a;
    color: #fff;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
}

.message-content pre code {
    background: none;
    padding: 0;
}

/* ===== 输入区域 ===== */
.input-container {
    padding: 16px 24px;
    background-color: var(--card-bg);
    border-top: 1px solid var(--border-color);
}

.input-wrapper {
    display: flex;
    gap: 12px;
    background-color: var(--bg-color);
    border-radius: 12px;
    padding: 8px;
}

.input-wrapper textarea {
    flex: 1;
    border: none;
    background: none;
    resize: none;
    font-size: 1rem;
    padding: 8px;
    font-family: inherit;
    max-height: 150px;
}

.input-wrapper textarea:focus {
    outline: none;
}

.send-btn {
    padding: 10px 24px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
}

.send-btn:hover {
    background-color: var(--primary-hover);
}

.send-btn:disabled {
    background-color: #ccc;
}

.input-hint {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 8px;
    text-align: center;
}

/* ===== 加载动画 ===== */
.typing-indicator {
    display: flex;
    gap: 4px;
    padding: 16px;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    background-color: #999;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-10px); }
}
```

### 13.5 JavaScript交互逻辑

```javascript
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

    // 流式聊天
    async chatStream(message, sessionId, onChunk) {
        const response = await fetch(`${API_BASE}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                session_id: sessionId
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    onChunk(data);
                }
            }
        }
    },

    // 获取对话历史
    async getHistory(sessionId) {
        const response = await fetch(`${API_BASE}/chat/history?session_id=${sessionId}`);
        return response.json();
    },

    // 清空历史
    async clearHistory(sessionId) {
        const response = await fetch(`${API_BASE}/chat/history?session_id=${sessionId}`, {
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
    }
};
```

```javascript
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
```

```javascript
// web/static/js/markdown.js

// 简单的Markdown渲染器
function renderMarkdown(text) {
    if (!text) return '';

    // 转义HTML
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // 标题
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // 粗体
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // 斜体
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // 代码块
    html = html.replace(/```(\w*)\n([\s\S]+?)```/g, '<pre><code class="language-$1">$2</code></pre>');

    // 行内代码
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    // 列表
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // 有序列表
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // 段落
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // 清理空段落
    html = html.replace(/<p>\s*<\/p>/g, '');

    return html;
}
```

### 13.6 启动方式

```bash
# 安装依赖
pip install fastapi uvicorn python-multipart

# 启动后端服务
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 访问
# http://localhost:8000
```

### 13.7 目录结构更新

```
k12-study-assistant/
├── ...
├── api/                                # API模块
│   ├── __init__.py
│   ├── main.py                         # FastAPI主应用
│   └── routes/
│       ├── __init__.py
│       ├── chat.py                     # 对话API
│       └── knowledge.py                # 知识库API
│
├── web/                                # 前端静态文件
│   └── static/
│       ├── index.html                  # 对话页面
│       ├── knowledge.html              # 知识库管理页面
│       ├── css/
│       │   ├── style.css               # 全局样式
│       │   ├── chat.css                # 对话页样式
│       │   └── knowledge.css           # 知识库页样式
│       └── js/
│           ├── api.js                  # API调用
│           ├── app.js                  # 主逻辑
│           ├── knowledge.js            # 知识库逻辑
│           └── markdown.js             # Markdown渲染
├── ...
```

### 13.8 依赖更新

```toml
dependencies = [
    # ... 原有依赖

    # Web后端
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "python-multipart>=0.0.6",
]
```

---

## 十四、后续扩展方向

1. **多模态支持**: 支持图片题目识别、语音交互
2. **用户系统**: 多用户支持，学习进度追踪
3. **评估系统**: 检索效果评估、回答质量评估
4. **知识图谱**: 构建学科知识图谱，增强推理能力
5. **WebSocket实时通信**: 支持真正的流式响应

---

## 附录：示例数据

为方便测试，系统预置以下示例知识数据：

### 数学
- 函数知识点总结（含定义、性质、图像）
- 勾股定理讲解与例题
- 一元二次方程求解方法

### 物理
- 牛顿运动定律详解
- 电学基础知识

### 化学
- 元素周期表知识点
- 化学方程式配平方法

---

*文档结束*
