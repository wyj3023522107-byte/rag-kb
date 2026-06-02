# src/agent/tools/holiday_tool.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger

from .base import BaseTool, ToolParameter, ToolResult


class HolidayTool(BaseTool):
    """节日查询工具"""

    name = "get_holiday_date"
    description = """查询特定节日的日期。可以查询父亲节、母亲节、劳动节、儿童节、教师节等常见节日今年的具体日期。

适用于：父亲节是什么时候、母亲节几号、今年儿童节是星期几等问题。
不支持：春节、中秋节等农历节日（需要农历计算）。"""
    parameters = [
        ToolParameter(
            name="holiday_name",
            type="string",
            description="节日名称，如：父亲节、母亲节、儿童节、劳动节、教师节、国庆节、元旦、情人节、圣诞节等",
            required=True
        )
    ]

    # 节日定义：固定日期 或 计算规则
    HOLIDAYS = {
        # 固定日期节日
        "元旦": {"type": "fixed", "month": 1, "day": 1},
        "情人节": {"type": "fixed", "month": 2, "day": 14},
        "妇女节": {"type": "fixed", "month": 3, "day": 8},
        "植树节": {"type": "fixed", "month": 3, "day": 12},
        "愚人节": {"type": "fixed", "month": 4, "day": 1},
        "劳动节": {"type": "fixed", "month": 5, "day": 1},
        "青年节": {"type": "fixed", "month": 5, "day": 4},
        "儿童节": {"type": "fixed", "month": 6, "day": 1},
        "建党节": {"type": "fixed", "month": 7, "day": 1},
        "建军节": {"type": "fixed", "month": 8, "day": 1},
        "教师节": {"type": "fixed", "month": 9, "day": 10},
        "国庆节": {"type": "fixed", "month": 10, "day": 1},
        "万圣节": {"type": "fixed", "month": 10, "day": 31},
        "光棍节": {"type": "fixed", "month": 11, "day": 11},
        "圣诞节": {"type": "fixed", "month": 12, "day": 25},

        # 计算类节日（第n个星期x）
        # weekday使用Python格式: 0=周一, 6=周日
        "母亲节": {"type": "nth_weekday", "month": 5, "nth": 2, "weekday": 6},  # 5月第二个星期日
        "父亲节": {"type": "nth_weekday", "month": 6, "nth": 3, "weekday": 6},  # 6月第三个星期日
        "感恩节": {"type": "nth_weekday", "month": 11, "nth": 4, "weekday": 3},  # 11月第四个星期四
    }

    WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    async def execute(self, holiday_name: str, **kwargs) -> ToolResult:
        """查询节日日期"""
        try:
            holiday_name = holiday_name.strip()
            year = datetime.now().year

            # 查找节日
            holiday_info = None
            for name, info in self.HOLIDAYS.items():
                if name in holiday_name or holiday_name in name:
                    holiday_info = info
                    holiday_name = name
                    break

            if not holiday_info:
                return ToolResult(
                    success=False,
                    error=f"未找到节日: {holiday_name}。支持的节日: {list(self.HOLIDAYS.keys())}"
                )

            # 计算日期
            if holiday_info["type"] == "fixed":
                date = datetime(year, holiday_info["month"], holiday_info["day"])
            elif holiday_info["type"] == "nth_weekday":
                date = self._calc_nth_weekday(
                    year,
                    holiday_info["month"],
                    holiday_info["nth"],
                    holiday_info["weekday"]
                )
            else:
                return ToolResult(success=False, error="未知的节日类型")

            weekday = self.WEEKDAYS[date.weekday()]
            result = f"{year}年{holiday_name}是{date.month}月{date.day}日（{weekday}）"

            logger.info(f"节日查询: {holiday_name} → {result}")

            return ToolResult(success=True, data=result)

        except Exception as e:
            logger.error(f"节日查询失败: {e}")
            return ToolResult(success=False, error=str(e))

    def _calc_nth_weekday(self, year: int, month: int, nth: int, weekday: int) -> datetime:
        """计算某月第n个星期x的日期

        Args:
            year: 年份
            month: 月份
            nth: 第几个（1-5）
            weekday: 星期几（Python格式: 0=周一, 6=周日）
        """
        # 该月第一天
        first_day = datetime(year, month, 1)

        # 第一天是星期几（Python: 0=周一, 6=周日）
        first_weekday = first_day.weekday()

        # 计算到第一个目标星期x需要多少天
        days_until_target = (weekday - first_weekday) % 7
        first_target = first_day + timedelta(days=days_until_target)

        # 第n个（从第一个开始，再加n-1周）
        target_date = first_target + timedelta(weeks=nth - 1)

        return target_date
