# K12智能学习助手

一个基于LangGraph的智能学习助手系统，支持学科问答、作业辅导、情绪疏导等功能。

## 功能特性

- 意图识别：自动识别用户意图类型
- 槽位填充：提取关键信息，支持多轮追问
- 混合检索：向量检索 + 关键词检索
- RAG问答：基于知识库的智能问答
- Web界面：友好的对话交互界面

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
