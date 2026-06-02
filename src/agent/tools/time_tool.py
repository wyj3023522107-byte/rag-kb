# src/agent/tools/time_tool.py

from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from .base import BaseTool, ToolParameter, ToolResult


class TimeTool(BaseTool):
    """获取时间工具"""

    name = "get_current_time"
    description = """获取日期和时间信息。

可以查询：
- 当前时间：现在几点、当前时间
- 相对日期：今天/明天/昨天/后天/大后天是几号、星期几

此工具返回真实的日期时间，可用于推算其他信息。"""
    parameters = [
        ToolParameter(
            name="format",
            type="string",
            description="时间格式：datetime(完整日期时间)、date(仅日期)、time(仅时间)、weekday(日期+星期)",
            required=False,
            enum=["datetime", "date", "time", "weekday"]
        ),
        ToolParameter(
            name="offset",
            type="string",
            description="日期偏移：today(今天)、tomorrow(明天)、yesterday(昨天)、after_tomorrow(后天)、three_days_later(大后天)",
            required=False,
            enum=["today", "tomorrow", "yesterday", "after_tomorrow", "three_days_later"]
        )
    ]

    async def execute(self, format: str = "datetime", offset: str = "today", **kwargs) -> ToolResult:
        """获取时间"""
        try:
            now = datetime.now()

            # 计算日期偏移
            offset_days = {
                "today": 0,
                "tomorrow": 1,
                "yesterday": -1,
                "after_tomorrow": 2,
                "three_days_later": 3
            }
            days = offset_days.get(offset, 0)
            target_date = now + timedelta(days=days)

            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

            if format == "date":
                result = target_date.strftime("%Y年%m月%d日")
            elif format == "time":
                result = target_date.strftime("%H:%M:%S")
            elif format == "weekday":
                weekday_name = weekdays[target_date.weekday()]
                result = f"{target_date.strftime('%Y年%m月%d日')} {weekday_name}"
            else:  # datetime
                weekday_name = weekdays[target_date.weekday()]
                result = f"{target_date.strftime('%Y年%m月%d日')} {weekday_name} {target_date.strftime('%H:%M:%S')}"

            logger.info(f"时间工具执行: format={format}, offset={offset}, result={result}")

            return ToolResult(success=True, data=result)

        except Exception as e:
            logger.error(f"时间工具执行失败: {e}")
            return ToolResult(success=False, error=str(e))
