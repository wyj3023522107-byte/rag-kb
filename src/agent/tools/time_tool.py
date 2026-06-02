# src/agent/tools/time_tool.py

from datetime import datetime
from typing import Optional
from loguru import logger

from .base import BaseTool, ToolParameter, ToolResult


class TimeTool(BaseTool):
    """获取当前时间工具"""

    name = "get_current_time"
    description = "获取当前的日期和时间。当用户询问现在几点、今天几号、当前时间等问题时使用此工具。"
    parameters = [
        ToolParameter(
            name="format",
            type="string",
            description="时间格式，可选：datetime(完整日期时间)、date(仅日期)、time(仅时间)、weekday(星期几)",
            required=False,
            enum=["datetime", "date", "time", "weekday"]
        )
    ]

    async def execute(self, format: str = "datetime", **kwargs) -> ToolResult:
        """获取当前时间"""
        try:
            now = datetime.now()

            if format == "date":
                result = now.strftime("%Y年%m月%d日")
            elif format == "time":
                result = now.strftime("%H:%M:%S")
            elif format == "weekday":
                weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
                result = f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]}"
            else:  # datetime
                weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
                result = f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]} {now.strftime('%H:%M:%S')}"

            logger.info(f"时间工具执行: format={format}, result={result}")

            return ToolResult(success=True, data=result)

        except Exception as e:
            logger.error(f"时间工具执行失败: {e}")
            return ToolResult(success=False, error=str(e))
