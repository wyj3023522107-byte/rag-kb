# src/agent/tools/__init__.py

from typing import Dict, List, Optional, Type, Any
from loguru import logger

from .base import BaseTool, ToolResult
from .time_tool import TimeTool
from .holiday_tool import HolidayTool
from .knowledge_tool import KnowledgeSearchTool
from .web_search_tool import WebSearchTool
from .web_fetch_tool import WebFetchTool


# 注册所有工具
TOOLS: Dict[str, Type[BaseTool]] = {
    "get_current_time": TimeTool,
    "get_holiday_date": HolidayTool,
    "knowledge_search": KnowledgeSearchTool,
    "web_search": WebSearchTool,
    "web_fetch": WebFetchTool,
}


class ToolManager:
    """工具管理器"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._init_tools()

    def _init_tools(self):
        """初始化所有工具实例"""
        for name, tool_cls in TOOLS.items():
            self._tools[name] = tool_cls()
            logger.info(f"工具已注册: {name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具实例"""
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """获取所有工具实例"""
        return list(self._tools.values())

    def get_all_schemas(self) -> List[Dict]:
        """获取所有工具的schema"""
        return [tool.get_schema() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """执行指定工具"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(success=False, error=f"工具不存在: {name}")

        logger.info(f"执行工具: {name}, 参数: {kwargs}")
        return await tool.execute(**kwargs)


# 全局工具管理器实例
_tool_manager: Optional[ToolManager] = None


def get_tool_manager() -> ToolManager:
    """获取工具管理器实例"""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager
