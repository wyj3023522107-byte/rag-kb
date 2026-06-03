# src/agent/tools/web_search_tool.py

from typing import List
from loguru import logger
import httpx

from .base import BaseTool, ToolParameter, ToolResult
from config.settings import settings


class WebSearchTool(BaseTool):
    """联网搜索工具 - 使用Tavily API"""

    name = "web_search"
    description = """联网搜索获取实时信息。

适用场景：
- 时事新闻：最近发生的事件、热点新闻、体育比赛结果
- 实时数据：天气、汇率、股票、油价等实时变化的信息
- 最新知识：刚刚发布的新技术、新政策、新规定
- 验证信息：核实某个说法是否准确
- 人物事件：名人动态、历史事件的最新解读

不适用场景：
- 基础学科知识（如勾股定理、化学方程式）→ 用知识库或直接回答
- 历史常识（如唐朝建立时间）→ 用知识库或直接回答
- 学生作业辅导 → 引导思考，不直接搜索答案"""

    parameters = [
        ToolParameter(
            name="query",
            type="string",
            description="搜索查询词，使用简洁明确的关键词",
            required=True
        ),
        ToolParameter(
            name="search_depth",
            type="string",
            description="搜索深度：basic(基础搜索，速度快) 或 advanced(深度搜索，结果更全面)",
            required=False,
            enum=["basic", "advanced"]
        ),
        ToolParameter(
            name="max_results",
            type="integer",
            description="返回结果数量，默认5条",
            required=False
        )
    ]

    async def execute(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        **kwargs
    ) -> ToolResult:
        """执行联网搜索"""
        api_key = settings.TAVILY_API_KEY

        if not api_key:
            logger.error("TAVILY_API_KEY 未配置")
            return ToolResult(success=False, error="搜索服务未配置，请联系管理员")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "search_depth": search_depth,
                        "max_results": max_results,
                        "include_answer": True,
                        "include_raw_content": False,
                        "include_images": False
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Tavily API错误: {response.status_code}")
                    return ToolResult(success=False, error=f"搜索服务错误: {response.status_code}")

                data = response.json()

                # 提取搜索结果
                results: List[dict] = data.get("results", [])
                answer = data.get("answer", "")

                # 格式化输出
                output_parts = []

                if answer:
                    output_parts.append(f"【摘要答案】\n{answer}\n")

                if results:
                    output_parts.append("【搜索结果】")
                    for i, item in enumerate(results[:max_results], 1):
                        title = item.get("title", "无标题")
                        url = item.get("url", "")
                        content = item.get("content", "")[:300]  # 截取前300字
                        output_parts.append(f"\n{i}. {title}")
                        output_parts.append(f"   来源: {url}")
                        output_parts.append(f"   摘要: {content}...")

                result_text = "\n".join(output_parts)
                logger.info(f"搜索完成: query={query}, 结果数={len(results)}")

                return ToolResult(success=True, data=result_text)

        except httpx.TimeoutException:
            logger.error("搜索超时")
            return ToolResult(success=False, error="搜索超时，请稍后重试")
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return ToolResult(success=False, error=f"搜索失败: {str(e)}")
