# Claude/Anthropic Agent 架构设计深度调研报告

## 目录
1. [Agent 核心架构](#1-agent-核心架构)
2. [工具系统设计](#2-工具系统设计)
3. [Skill 系统设计](#3-skill-系统设计)
4. [MCP (Model Context Protocol) 架构](#4-mcp-model-context-protocol-架构)
5. [最佳实践](#5-最佳实践)
6. [架构图](#6-架构图)
7. [代码示例](#7-代码示例)
8. [参考资料](#8-参考资料)

---

## 1. Agent 核心架构

### 1.1 核心设计理念

Anthropic 对 Agent 的定义非常简洁而深刻：

> **Agent = LLM + Tools + Prompt (in a loop)**

这是 Anthropic 官方推荐的核心架构模式。相比于复杂的框架，他们强调从简单开始，只在必要时增加复杂性。

### 1.2 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent 架构层次                          │
├─────────────────────────────────────────────────────────────┤
│  Level 0: Augmented LLM (增强型 LLM)                        │
│  ├── 检索/搜索能力                                          │
│  ├── 工具调用                                               │
│  ├── 记忆                                                   │
│  └── 状态管理                                               │
├─────────────────────────────────────────────────────────────┤
│  Level 1: Workflows (工作流)                                │
│  ├── Prompt Chaining (提示链)                               │
│  ├── Routing (路由)                                         │
│  ├── Parallelization (并行化)                               │
│  ├── Orchestrator-Workers (编排者-工作者)                   │
│  └── Evaluator-Optimizer (评估者-优化者)                    │
├─────────────────────────────────────────────────────────────┤
│  Level 2: Autonomous Agents (自主智能体)                    │
│  └── 完全自主的目标驱动系统                                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 状态管理

#### 状态类型

| 状态类型 | 描述 | 持久性 |
|---------|------|--------|
| **Conversation History** | 对话历史，包含所有消息 | 会话级 |
| **Tool Execution State** | 工具执行状态和结果 | 任务级 |
| **Working Memory** | 当前任务的临时存储 | 任务级 |
| **Persistent Memory** | 跨会话的长期记忆 | 持久化 |

#### 状态管理策略

```python
class AgentState:
    """Agent 状态管理"""

    def __init__(self):
        self.messages = []           # 对话历史
        self.tool_results = {}       # 工具执行结果缓存
        self.context = {}            # 上下文变量
        self.checkpoints = []        # 检查点（用于长任务）

    def add_message(self, role: str, content: any):
        """添加消息到历史"""
        self.messages.append({"role": role, "content": content})

    def save_checkpoint(self, state: dict):
        """保存检查点"""
        self.checkpoints.append({
            "timestamp": datetime.now(),
            "state": state,
            "message_count": len(self.messages)
        })

    def handle_token_limit(self, max_tokens: int):
        """处理 Token 限制"""
        # 策略1: 滑动窗口
        # 策略2: 摘要压缩
        # 策略3: 重要性过滤
        pass
```

### 1.4 工具调用流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │───►│   LLM    │───►│  Tool    │───►│  Result  │
│  Input   │    │ Process  │    │ Execute  │    │ Process  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                               │
                     │         ┌─────────────────────┘
                     ▼         ▼
               ┌──────────────────┐
               │  Continue Loop?  │
               │  (stop_reason)   │
               └──────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   "tool_use"    "end_turn"   "max_tokens"
   (继续循环)    (结束)       (达到限制)
```

### 1.5 循环执行机制

核心循环逻辑：

```python
def agent_loop(user_message: str, tools: list, max_iterations: int = 10):
    """
    Agent 核心循环执行机制

    Args:
        user_message: 用户输入
        tools: 可用工具列表
        max_iterations: 最大迭代次数（防止无限循环）
    """
    messages = [{"role": "user", "content": user_message}]
    iteration = 0

    while iteration < max_iterations:
        # 调用 Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        # 添加助手响应到历史
        messages.append({"role": "assistant", "content": response.content})

        # 检查停止原因
        if response.stop_reason == "tool_use":
            # 提取工具调用
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # 执行工具
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            # 添加工具结果作为用户消息
            messages.append({"role": "user", "content": tool_results})
            iteration += 1

        elif response.stop_reason == "end_turn":
            # Claude 完成任务
            return extract_text_response(response)

        elif response.stop_reason == "max_tokens":
            # 达到 Token 限制，需要处理
            return handle_token_limit(response)

    # 达到最大迭代次数
    return {"error": "Max iterations reached"}
```

---

## 2. 工具系统设计

### 2.1 Tool 定义方式

Anthropic 使用 JSON Schema 定义工具：

```python
tools = [
    {
        "name": "get_weather",                    # 工具名称
        "description": "Get the current weather in a given location. Returns temperature and conditions.",
        "input_schema": {                         # JSON Schema 格式
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "search_database",
        "description": "Search the knowledge base for relevant documents",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters for the search",
                    "properties": {
                        "date_range": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "string"},
                                "end": {"type": "string"}
                            }
                        },
                        "category": {
                            "type": "string"
                        }
                    }
                }
            },
            "required": ["query"]
        }
    }
]
```

### 2.2 Tool Calling 实现

#### 2.2.1 工具执行器

```python
class ToolExecutor:
    """工具执行器"""

    def __init__(self):
        self.tools = {}  # 工具注册表

    def register(self, name: str, func: callable, schema: dict):
        """注册工具"""
        self.tools[name] = {
            "function": func,
            "schema": schema
        }

    def execute(self, tool_name: str, tool_input: dict) -> any:
        """执行工具"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            # 验证输入
            self.validate_input(tool_name, tool_input)

            # 执行工具
            result = self.tools[tool_name]["function"](**tool_input)
            return result

        except Exception as e:
            return {"error": str(e)}

    def validate_input(self, tool_name: str, input_data: dict):
        """验证工具输入"""
        schema = self.tools[tool_name]["schema"]["input_schema"]
        required = schema.get("required", [])

        for field in required:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
```

#### 2.2.2 工具结果处理

```python
def process_tool_result(tool_use_block, result: any) -> dict:
    """
    处理工具结果，生成标准格式

    Args:
        tool_use_block: Claude 返回的 tool_use 块
        result: 工具执行结果

    Returns:
        标准格式的工具结果
    """
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_block.id,  # 必须匹配 tool_use 的 id
        "content": json.dumps(result) if isinstance(result, (dict, list)) else str(result),
        "is_error": False  # 如果工具执行失败，设为 True
    }
```

### 2.3 工具注册和发现机制

```python
class ToolRegistry:
    """工具注册中心"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register_tool(self, name: str, description: str,
                      input_schema: dict, handler: callable):
        """注册工具"""
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "handler": handler
        }

    def get_tools_schema(self) -> list:
        """获取所有工具的 Schema（用于 API 调用）"""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"]
            }
            for t in self._tools.values()
        ]

    def get_tool_handler(self, name: str) -> callable:
        """获取工具处理函数"""
        return self._tools.get(name, {}).get("handler")


# 使用装饰器注册工具
def tool(name: str, description: str, input_schema: dict):
    """工具注册装饰器"""
    def decorator(func):
        registry = ToolRegistry()
        registry.register_tool(name, description, input_schema, func)
        return func
    return decorator


# 使用示例
@tool(
    name="calculate",
    description="Perform mathematical calculations",
    input_schema={
        "type": "object",
        "properties": {
            "expression": {"type": "string"}
        },
        "required": ["expression"]
    }
)
def calculate(expression: str) -> float:
    return eval(expression)
```

### 2.4 Tool Choice 参数

```python
# tool_choice 参数控制工具使用行为

# 1. auto - 让 Claude 自动决定（默认）
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=tools,
    tool_choice={"type": "auto"},  # Claude 自动选择
    messages=messages
)

# 2. any - 强制使用工具
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=tools,
    tool_choice={"type": "any"},  # 必须调用至少一个工具
    messages=messages
)

# 3. tool - 强制调用特定工具
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=tools,
    tool_choice={"type": "tool", "name": "get_weather"},  # 强制调用指定工具
    messages=messages
)

# 4. none - 禁止使用工具
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    tools=tools,
    tool_choice={"type": "none"},  # 不使用工具
    messages=messages
)
```

---

## 3. Skill 系统设计

### 3.1 Skill 与 Tool 的区别

| 特性 | Tool | Skill |
|-----|------|-------|
| **定义** | 单一功能的原子操作 | 复杂任务的编排能力 |
| **粒度** | 细粒度、单一职责 | 粗粒度、多步骤 |
| **触发** | 由 LLM 决定调用 | 可通过关键词、意图、配置触发 |
| **组合** | 独立使用 | 可组合多个 Tool |
| **示例** | `get_weather()`, `search()` | `research_topic()`, `analyze_code()` |

### 3.2 Skill 的组织方式

```
┌─────────────────────────────────────────────────────────────┐
│                      Skill 架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Skill Layer                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Skill 1  │  │ Skill 2  │  │ Skill 3  │          │   │
│  │  │(Research)│  │(Code Gen)│  │(Analysis)│          │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  └───────┼─────────────┼─────────────┼─────────────────┘   │
│          │             │             │                     │
│          ▼             ▼             ▼                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Tool Layer                        │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │   │
│  │  │Tool 1│ │Tool 2│ │Tool 3│ │Tool 4│ │Tool 5│      │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Skill 定义结构

```python
from dataclasses import dataclass
from typing import List, Optional, Callable
from enum import Enum

class TriggerType(Enum):
    """Skill 触发类型"""
    KEYWORD = "keyword"      # 关键词触发
    INTENT = "intent"        # 意图识别触发
    MANUAL = "manual"        # 手动调用
    SCHEDULED = "scheduled"  # 定时触发
    HOOK = "hook"           # 钩子触发

@dataclass
class SkillTrigger:
    """Skill 触发条件"""
    type: TriggerType
    patterns: List[str]      # 关键词或意图模式
    priority: int = 0        # 优先级

@dataclass
class Skill:
    """Skill 定义"""
    name: str                           # Skill 名称
    description: str                    # 描述
    trigger: SkillTrigger               # 触发条件
    tools: List[str]                    # 依赖的工具
    system_prompt: str                  # 专属系统提示
    pre_processing: Optional[Callable]  # 前置处理
    post_processing: Optional[Callable] # 后置处理
    max_turns: int = 5                  # 最大轮次
    examples: List[dict] = None         # Few-shot 示例


# Skill 示例
research_skill = Skill(
    name="literature_search",
    description="Conduct comprehensive literature reviews using multi-perspective analysis",
    trigger=SkillTrigger(
        type=TriggerType.INTENT,
        patterns=["research", "literature review", "find papers", "survey"]
    ),
    tools=["search_database", "get_paper", "summarize", "export_citations"],
    system_prompt="""You are a research assistant specialized in academic literature.
    When conducting research:
    1. First clarify the research question
    2. Search for relevant papers
    3. Analyze and synthesize findings
    4. Provide structured output with citations""",
    max_turns=10,
    examples=[
        {
            "input": "Research recent advances in transformer architectures",
            "output": "I'll help you research recent advances in transformer architectures..."
        }
    ]
)
```

### 3.4 Skill 触发机制

```python
class SkillDispatcher:
    """Skill 调度器"""

    def __init__(self):
        self.skills = {}  # 注册的 Skills
        self.intent_classifier = None  # 意图分类器

    def register(self, skill: Skill):
        """注册 Skill"""
        self.skills[skill.name] = skill

    def detect_skill(self, user_message: str) -> Optional[Skill]:
        """检测应该触发哪个 Skill"""

        # 1. 关键词匹配
        for skill in self.skills.values():
            if skill.trigger.type == TriggerType.KEYWORD:
                for pattern in skill.trigger.patterns:
                    if pattern.lower() in user_message.lower():
                        return skill

        # 2. 意图识别（使用 LLM）
        if self.intent_classifier:
            intent = self.intent_classifier.classify(user_message)
            for skill in self.skills.values():
                if skill.trigger.type == TriggerType.INTENT:
                    if intent in skill.trigger.patterns:
                        return skill

        # 3. 手动触发检查（如 /skill_name）
        if user_message.startswith("/"):
            skill_name = user_message[1:].split()[0]
            return self.skills.get(skill_name)

        return None

    def execute_skill(self, skill: Skill, user_message: str, context: dict):
        """执行 Skill"""
        # 前置处理
        if skill.pre_processing:
            user_message = skill.pre_processing(user_message, context)

        # 构建专属提示
        messages = [
            {"role": "system", "content": skill.system_prompt},
            {"role": "user", "content": user_message}
        ]

        # 获取相关工具
        tools = [
            tool_registry.get_tool_schema(t)
            for t in skill.tools
        ]

        # 执行 Agent 循环
        return self.run_skill_loop(skill, messages, tools)
```

---

## 4. MCP (Model Context Protocol) 架构

### 4.1 设计理念

MCP 是 Anthropic 推动的开放协议，旨在标准化 AI 应用与数据源/工具之间的连接。

核心理念：
- **USB-C for AI**: 像 USB-C 统一设备连接一样，MCP 统一 AI 与数据/工具的连接
- **解耦**: AI 应用与数据源/工具解耦，可独立发展
- **标准化**: 统一接口，降低集成成本

### 4.2 架构模式

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP 架构模式                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐         ┌─────────────┐         ┌──────────┐ │
│  │ MCP Client  │◄───────►│ MCP Server  │◄───────►│  Local   │ │
│  │ (AI App)    │  JSON   │             │         │ Resource │ │
│  │             │  RPC    │             │         │          │ │
│  └─────────────┘         └─────────────┘         └──────────┘ │
│        │                       │                               │
│        │                       │                               │
│        ▼                       ▼                               │
│  ┌─────────────┐         ┌─────────────┐                      │
│  │   Claude    │         │  External   │                      │
│  │   Model     │         │    API      │                      │
│  └─────────────┘         └─────────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 核心能力

#### 4.3.1 Resources (资源)

只读数据暴露能力：

```python
from mcp.server import Server
import mcp.types as types

server = Server("resource-server")

@server.list_resources()
async def list_resources() -> list[types.Resource]:
    """列出可用资源"""
    return [
        types.Resource(
            uri="file:///data/report.pdf",
            name="Monthly Report",
            description="Monthly business report",
            mimeType="application/pdf"
        ),
        types.Resource(
            uri="database://users",
            name="User Database",
            description="User records"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri.startswith("file://"):
        path = uri[7:]
        with open(path, 'r') as f:
            return f.read()
    elif uri.startswith("database://"):
        # 查询数据库
        return query_database(uri[11:])
```

#### 4.3.2 Tools (工具)

可执行功能：

```python
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """列出可用工具"""
    return [
        types.Tool(
            name="query_database",
            description="Execute SQL query on the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query"}
                },
                "required": ["sql"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.Content]:
    """执行工具"""
    if name == "query_database":
        result = execute_sql(arguments["sql"])
        return [types.TextContent(type="text", text=str(result))]
```

#### 4.3.3 Prompts (提示模板)

预定义的提示模板：

```python
@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    """列出可用提示模板"""
    return [
        types.Prompt(
            name="analyze_code",
            description="Analyze code for issues",
            arguments=[
                types.PromptArgument(
                    name="language",
                    description="Programming language",
                    required=True
                )
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    """获取渲染后的提示"""
    if name == "analyze_code":
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Analyze this {arguments['language']} code for issues..."
                    )
                )
            ]
        )
```

#### 4.3.4 Sampling (采样)

服务器请求 LLM 生成：

```python
# MCP Server 可以请求 Client 进行 LLM 调用
# 这允许服务器实现自主行为

async def autonomous_analysis(server, context):
    """使用 Sampling 进行自主分析"""

    result = await server.request_handler.send_request(
        "sampling/createMessage",
        {
            "messages": [
                {"role": "user", "content": "Analyze this data..."}
            ],
            "modelPreferences": {
                "hints": [{"name": "claude-sonnet"}]
            },
            "maxTokens": 1000
        }
    )

    return result
```

### 4.4 MCP 与 Agent 集成

```python
class MCPAgent:
    """基于 MCP 的 Agent"""

    def __init__(self, mcp_clients: list):
        self.mcp_clients = mcp_clients  # 多个 MCP Server 连接
        self.consolidated_tools = []
        self.consolidated_resources = []

    async def initialize(self):
        """初始化，聚合所有 MCP Server 的能力"""
        for client in self.mcp_clients:
            # 获取工具列表
            tools = await client.list_tools()
            self.consolidated_tools.extend(tools)

            # 获取资源列表
            resources = await client.list_resources()
            self.consolidated_resources.extend(resources)

    async def run(self, user_message: str):
        """运行 Agent"""
        messages = [{"role": "user", "content": user_message}]

        while True:
            # 调用 Claude
            response = await self.call_claude(
                messages=messages,
                tools=self.consolidated_tools
            )

            if response.stop_reason == "tool_use":
                # 找到对应的 MCP Server 并执行
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self.execute_on_mcp(
                            block.name,
                            block.input
                        )
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            }]
                        })
            else:
                return response

    async def execute_on_mcp(self, tool_name: str, tool_input: dict):
        """在对应的 MCP Server 上执行工具"""
        for client in self.mcp_clients:
            tools = await client.list_tools()
            if any(t.name == tool_name for t in tools):
                return await client.call_tool(tool_name, tool_input)
```

---

## 5. 最佳实践

### 5.1 意图识别和路由

```python
class IntentRouter:
    """意图识别与路由"""

    def __init__(self):
        self.intents = {
            "search": ["find", "search", "look for", "查询", "搜索"],
            "create": ["create", "generate", "make", "创建", "生成"],
            "analyze": ["analyze", "examine", "review", "分析", "检查"],
            "execute": ["run", "execute", "perform", "执行", "运行"]
        }

    async def classify(self, user_message: str) -> str:
        """使用 LLM 进行意图分类"""

        prompt = f"""Classify the user's intent into one of these categories:
        - search: Finding information
        - create: Creating new content
        - analyze: Analyzing existing content
        - execute: Running a command or task

        User message: {user_message}

        Respond with only the category name."""

        response = await self.llm.generate(prompt)
        return response.strip().lower()

    async def route(self, user_message: str):
        """根据意图路由到不同处理流程"""
        intent = await self.classify(user_message)

        routers = {
            "search": self.handle_search,
            "create": self.handle_create,
            "analyze": self.handle_analyze,
            "execute": self.handle_execute
        }

        handler = routers.get(intent, self.handle_default)
        return await handler(user_message)
```

### 5.2 多工具编排

#### 5.2.1 顺序编排

```python
async def sequential_orchestration(query: str):
    """顺序执行多个工具"""
    results = []

    # 步骤 1: 搜索
    search_result = await execute_tool("search", {"query": query})
    results.append(search_result)

    # 步骤 2: 分析
    analysis_result = await execute_tool("analyze", {"data": search_result})
    results.append(analysis_result)

    # 步骤 3: 总结
    summary_result = await execute_tool("summarize", {"content": analysis_result})
    results.append(summary_result)

    return summary_result
```

#### 5.2.2 并行编排

```python
import asyncio

async def parallel_orchestration(query: str):
    """并行执行多个工具"""
    tasks = [
        execute_tool("search_web", {"query": query}),
        execute_tool("search_database", {"query": query}),
        execute_tool("search_local", {"query": query})
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 合并结果
    merged = merge_results(results)

    # 最终综合
    return await execute_tool("synthesize", {"sources": merged})
```

#### 5.2.3 动态编排 (Orchestrator-Workers)

```python
class OrchestratorWorker:
    """Orchestrator-Workers 模式"""

    async def run(self, task: str):
        # 1. Orchestrator 分析任务，分配子任务
        subtasks = await self.orchestrate(task)

        # 2. Workers 并行执行子任务
        results = await asyncio.gather(*[
            self.worker(subtask) for subtask in subtasks
        ])

        # 3. Orchestrator 综合结果
        final = await self.synthesize(results)

        return final

    async def orchestrate(self, task: str) -> list:
        """Orchestrator 分解任务"""
        prompt = f"""Break down this task into subtasks:
        Task: {task}

        Return a JSON array of subtasks."""

        response = await self.llm.generate(prompt)
        return json.loads(response)

    async def worker(self, subtask: dict):
        """Worker 执行子任务"""
        return await self.agent.run(subtask["description"])
```

### 5.3 错误处理和重试

```python
import asyncio
from typing import Optional

class RobustToolExecutor:
    """健壮的工具执行器"""

    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout

    async def execute_with_retry(
        self,
        tool_name: str,
        tool_input: dict,
        fallback: Optional[callable] = None
    ):
        """带重试的工具执行"""

        for attempt in range(self.max_retries):
            try:
                # 带超时执行
                result = await asyncio.wait_for(
                    self._execute_tool(tool_name, tool_input),
                    timeout=self.timeout
                )

                # 检查是否是错误结果
                if isinstance(result, dict) and "error" in result:
                    raise ToolExecutionError(result["error"])

                return result

            except asyncio.TimeoutError:
                print(f"Tool {tool_name} timed out, attempt {attempt + 1}")

                if attempt == self.max_retries - 1:
                    if fallback:
                        return await fallback(tool_input)
                    return {"error": "Timeout after max retries"}

            except ToolExecutionError as e:
                print(f"Tool {tool_name} failed: {e}, attempt {attempt + 1}")

                if attempt == self.max_retries - 1:
                    if fallback:
                        return await fallback(tool_input)
                    return {"error": str(e)}

            except Exception as e:
                print(f"Unexpected error: {e}")
                return {"error": f"Unexpected error: {str(e)}"}

            # 指数退避
            await asyncio.sleep(2 ** attempt)

    async def _execute_tool(self, name: str, input: dict):
        """实际执行工具"""
        # 实现实际的工具执行逻辑
        pass


# Agent 级别的错误恢复
class ResilientAgent:
    """容错 Agent"""

    async def run_with_recovery(self, user_message: str):
        """带恢复机制的 Agent 运行"""
        messages = [{"role": "user", "content": user_message}]
        failed_tools = []

        while True:
            try:
                response = await self.call_llm(messages)

                if response.stop_reason == "tool_use":
                    for block in response.content:
                        if block.type == "tool_use":
                            result = await self.safe_execute_tool(
                                block.name,
                                block.input,
                                failed_tools
                            )

                            if "error" in result:
                                failed_tools.append(block.name)
                                # 让 LLM 知道工具失败了，尝试其他方案
                                result["_recovery_hint"] = "This tool failed. Try alternative approach."

                            messages.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(result)
                                }]
                            })
                else:
                    return response

            except Exception as e:
                # 全局错误恢复
                recovery_prompt = f"""
                An error occurred: {str(e)}
                Previous context: {messages[-1] if messages else 'None'}

                Please suggest a recovery approach or provide the best possible answer.
                """

                messages.append({
                    "role": "user",
                    "content": recovery_prompt
                })
```

### 5.4 Agent 设计模式总结

| 模式 | 适用场景 | 复杂度 |
|-----|---------|--------|
| **Single Agent + Tools** | 简单任务，单一目标 | 低 |
| **Prompt Chaining** | 固定流程，步骤明确 | 低 |
| **Routing** | 多类型任务，需要分类处理 | 中 |
| **Parallelization** | 独立子任务，需要加速 | 中 |
| **Orchestrator-Workers** | 复杂任务，需要动态分解 | 高 |
| **Evaluator-Optimizer** | 需要迭代优化的任务 | 高 |
| **Multi-Agent** | 多角色协作，复杂系统 | 高 |

---

## 6. 架构图

### 6.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Claude Agent 整体架构                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Application Layer                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Skills    │  │  Workflows  │  │   Agents    │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Orchestration Layer                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Router    │  │  Scheduler  │  │  Dispatcher │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Tool Layer                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Tool Registry                             │   │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │   │   │
│  │  │  │ Tool 1 │ │ Tool 2 │ │ Tool 3 │ │ Tool 4 │ │ Tool N │    │   │   │
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Integration Layer (MCP)                        │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │   │
│  │  │   MCP Client    │  │   MCP Server    │  │  External APIs  │    │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Model Layer                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              Claude API (Sonnet/Opus/Haiku)                  │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Agent 执行流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Agent 执行流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────┐                                                             │
│    │  Start  │                                                             │
│    └────┬────┘                                                             │
│         │                                                                   │
│         ▼                                                                   │
│    ┌─────────────┐                                                         │
│    │ User Input  │                                                         │
│    └──────┬──────┘                                                         │
│           │                                                                 │
│           ▼                                                                 │
│    ┌─────────────┐      ┌──────────────────────────────┐                   │
│    │   Intent    │─────►│  Intent Classification        │                   │
│    │  Detection  │      │  - Keyword Matching           │                   │
│    └──────┬──────┘      │  - LLM Classification         │                   │
│           │             │  - Pattern Recognition        │                   │
│           │             └──────────────────────────────┘                   │
│           ▼                                                                 │
│    ┌─────────────┐      ┌──────────────────────────────┐                   │
│    │   Skill     │─────►│  Skill Selection              │                   │
│    │  Selection  │      │  - Match Intent to Skill      │                   │
│    └──────┬──────┘      │  - Load Tools & Prompts       │                   │
│           │             └──────────────────────────────┘                   │
│           ▼                                                                 │
│    ┌─────────────┐                                                         │
│    │   Agent     │◄──────────────────────────────────────┐                 │
│    │    Loop     │                                       │                 │
│    └──────┬──────┘                                       │                 │
│           │                                              │                 │
│           ▼                                              │                 │
│    ┌─────────────┐                                       │                 │
│    │  Call LLM   │                                       │                 │
│    │ (Claude API)│                                       │                 │
│    └──────┬──────┘                                       │                 │
│           │                                              │                 │
│           ▼                                              │                 │
│    ┌─────────────┐                                       │                 │
│    │ Check Stop  │                                       │                 │
│    │   Reason    │                                       │                 │
│    └──────┬──────┘                                       │                 │
│           │                                              │                 │
│     ┌─────┼─────┬─────────┐                              │                 │
│     │     │     │         │                              │                 │
│     ▼     ▼     ▼         ▼                              │                 │
│  tool_use  │  end_turn  max_tokens                       │                 │
│     │     │     │         │                              │                 │
│     ▼     │     │         ▼                              │                 │
│ ┌─────────┐│     │    ┌─────────┐                        │                 │
│ │Execute  ││     │    │ Handle  │                        │                 │
│ │ Tools   ││     │    │ Token   │                        │                 │
│ └────┬────┘│     │    │ Limit   │                        │                 │
│      │     │     └────┬────┘                             │                 │
│      │     │          │                                  │                 │
│      │     │          ▼                                  │                 │
│      │     │    ┌──────────┐                             │                 │
│      │     │    │  Return  │                             │                 │
│      │     │    │  Result  │                             │                 │
│      │     │    └──────────┘                             │                 │
│      │     │                                              │                 │
│      └─────┴──────────────────────────────────────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 代码示例

### 7.1 完整的 Agent 实现

```python
import anthropic
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# ============ 类型定义 ============

class StopReason(Enum):
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"

@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: callable

# ============ Agent 核心类 ============

class ClaudeAgent:
    """Claude Agent 完整实现"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        max_iterations: int = 10
    ):
        self.client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations
        self.tools: Dict[str, ToolDefinition] = {}
        self.messages: List[Dict] = []
        self.system_prompt: str = "You are a helpful assistant."

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: callable
    ):
        """注册工具"""
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )

    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self.system_prompt = prompt

    def get_tools_schema(self) -> List[Dict]:
        """获取工具 Schema"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema
            }
            for t in self.tools.values()
        ]

    def execute_tool(self, name: str, input_data: Dict) -> Any:
        """执行工具"""
        if name not in self.tools:
            return {"error": f"Unknown tool: {name}"}

        try:
            return self.tools[name].handler(**input_data)
        except Exception as e:
            return {"error": str(e)}

    def run(self, user_message: str) -> str:
        """运行 Agent"""
        self.messages = [{"role": "user", "content": user_message}]
        iteration = 0

        while iteration < self.max_iterations:
            # 调用 Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=self.get_tools_schema(),
                messages=self.messages
            )

            # 添加助手响应
            self.messages.append({"role": "assistant", "content": response.content})

            # 检查停止原因
            if response.stop_reason == StopReason.TOOL_USE.value:
                # 处理工具调用
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        result = self.execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                        })

                self.messages.append({"role": "user", "content": tool_results})
                iteration += 1

            elif response.stop_reason == StopReason.END_TURN.value:
                return self._extract_text(response)

            elif response.stop_reason == StopReason.MAX_TOKENS.value:
                return self._handle_token_limit(response)

        return "Error: Maximum iterations reached"

    def _extract_text(self, response) -> str:
        """提取文本响应"""
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    def _handle_token_limit(self, response) -> str:
        """处理 Token 限制"""
        return "Response truncated due to token limit. Please simplify your request."


# ============ 使用示例 ============

# 创建 Agent
agent = ClaudeAgent()

# 注册工具
agent.register_tool(
    name="get_weather",
    description="Get current weather for a location",
    input_schema={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    },
    handler=lambda location: {"temperature": "22°C", "condition": "Sunny"}
)

agent.register_tool(
    name="search",
    description="Search for information",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    },
    handler=lambda query: [f"Result for: {query}"]
)

# 设置系统提示
agent.set_system_prompt("""You are a helpful assistant with access to tools.
Use tools when appropriate to answer user questions accurately.""")

# 运行
result = agent.run("What's the weather in San Francisco?")
print(result)
```

### 7.2 MCP Server 实现示例

```python
from mcp.server import Server
import mcp.types as types
from mcp.server.stdio import stdio_server

# 创建 MCP Server
server = Server("example-server")

# ============ Resources ============

@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="file:///data/config.json",
            name="Configuration",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "file:///data/config.json":
        return '{"setting": "value"}'
    raise ValueError(f"Unknown resource: {uri}")

# ============ Tools ============

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="echo",
            description="Echo the input message",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.Content]:
    if name == "echo":
        return [types.TextContent(
            type="text",
            text=f"Echo: {arguments['message']}"
        )]
    raise ValueError(f"Unknown tool: {name}")

# ============ Prompts ============

@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="greet",
            description="Generate a greeting message",
            arguments=[
                types.PromptArgument(
                    name="name",
                    description="Name to greet",
                    required=True
                )
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    if name == "greet":
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Please greet {arguments['name']} warmly."
                    )
                )
            ]
        )
    raise ValueError(f"Unknown prompt: {name}")

# ============ 运行 Server ============

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 8. 参考资料

### 官方文档

| 资源 | URL |
|-----|-----|
| **Building Effective Agents** | https://www.anthropic.com/engineering/building-effective-agents |
| **Claude API Documentation** | https://docs.anthropic.com/en/docs/build-with-claude/agents |
| **Tool Use Guide** | https://docs.anthropic.com/en/docs/build-with-claude/tool-use |
| **MCP Specification** | https://modelcontextprotocol.io |
| **Anthropic Cookbook** | https://github.com/anthropics/anthropic-cookbook |
| **MCP Python SDK** | https://github.com/modelcontextprotocol/python-sdk |
| **MCP TypeScript SDK** | https://github.com/modelcontextprotocol/typescript-sdk |

### 关键文章

1. **Building Effective Agents** - Anthropic 官方 Agent 构建指南
2. **Orchestrating Agents for Complex Workflows** - 多 Agent 编排模式
3. **Model Context Protocol Introduction** - MCP 协议设计理念

---

## 总结

Anthropic 的 Agent 架构设计体现了以下核心理念：

1. **简单优先**: 从 LLM + Tools + Loop 的基础架构开始，只在必要时增加复杂性

2. **分层设计**:
   - Tool 层：原子操作
   - Skill 层：任务编排
   - Agent 层：自主决策

3. **标准化集成**: 通过 MCP 协议标准化工具与数据源的连接

4. **渐进式复杂度**:
   - Augmented LLM → Workflows → Autonomous Agents
   - 单一 Agent → 多 Agent 协作

5. **可靠性设计**:
   - 明确的错误处理
   - 重试机制
   - Token 限制处理

这套架构设计为我们构建自己的 RAG 知识库 Agent 提供了清晰的指导和最佳实践参考。
