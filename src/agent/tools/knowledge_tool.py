# src/agent/tools/knowledge_tool.py

from typing import Optional, Dict, Any
from loguru import logger

from .base import BaseTool, ToolParameter, ToolResult


class KnowledgeSearchTool(BaseTool):
    """知识库检索工具"""

    name = "knowledge_search"
    description = """从知识库中检索相关的知识点和学习资料。

适用于：
- 学科知识问答（如勾股定理是什么、光合作用的过程）
- 作业辅导时查找相关知识点
- 需要参考教材或学习资料时

输入搜索关键词，返回最相关的知识内容。"""
    parameters = [
        ToolParameter(
            name="query",
            type="string",
            description="搜索关键词或问题，如'勾股定理'、'光合作用'、'一元二次方程'",
            required=True
        ),
        ToolParameter(
            name="subject",
            type="string",
            description="学科筛选（可选）：数学、语文、英语、物理、化学、生物、历史、地理、政治",
            required=False
        )
    ]

    def __init__(self):
        self._rag_engine = None

    @property
    def rag_engine(self):
        if self._rag_engine is None:
            from src.rag.engine import get_rag_engine
            self._rag_engine = get_rag_engine()
        return self._rag_engine

    async def execute(self, query: str, subject: Optional[str] = None, **kwargs) -> ToolResult:
        """执行知识检索"""
        try:
            logger.info(f"知识检索: query={query}, subject={subject}")

            # 调用RAG引擎检索
            docs = await self.rag_engine.retrieve(query, top_k=3, subject=subject)

            if not docs:
                return ToolResult(
                    success=True,
                    data="知识库中暂无相关内容"
                )

            # 格式化检索结果
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.get("content", "")
                source = doc.get("metadata", {}).get("filename", "未知来源")
                results.append(f"【资料{i}】(来源: {source})\n{content[:500]}...")

            result_text = "\n\n".join(results)
            logger.info(f"知识检索完成: 找到 {len(docs)} 条相关资料")

            return ToolResult(success=True, data=result_text)

        except Exception as e:
            logger.error(f"知识检索失败: {e}")
            return ToolResult(success=False, error=str(e))
