# src/knowledge/classifier.py

"""
智能文档分类器
上传时自动识别文档类型，支持：
- 学科类型（数学、语文、物理等）
- 文档类型（教材、试题、笔记、公司文档、技术文档等）
- 适用年级（小学到高三）
- 关键词提取
"""

import json
from typing import Dict, Any, Optional, List
from loguru import logger
import asyncio

from src.llm.client import get_llm_client


# 文档类型定义
DOCUMENT_CATEGORIES = {
    # 学科类型
    "数学": "数学相关内容，包括公式、定理、计算方法等",
    "语文": "语文相关内容，包括阅读理解、作文、古诗词等",
    "英语": "英语相关内容，包括语法、词汇、阅读等",
    "物理": "物理相关内容，包括定律、实验、公式等",
    "化学": "化学相关内容，包括方程式、元素、实验等",
    "生物": "生物相关内容，包括细胞、遗传、生态等",
    "历史": "历史相关内容，包括历史事件、人物、年代等",
    "地理": "地理相关内容，包括地形、气候、资源等",
    "政治": "政治相关内容，包括理论、时事、法律等",

    # 非学科类型
    "公司文档": "公司内部文档，包括制度、流程、通知等",
    "技术文档": "技术类文档，包括API文档、开发指南、技术规范等",
    "产品文档": "产品相关文档，包括说明书、需求文档、设计文档等",
    "研究报告": "研究报告、分析报告、调研文档等",
    "政策法规": "政策文件、法律法规、规章制度等",
    "通用知识": "通用知识、百科内容、常识等",
    "其他": "无法归类的其他类型文档"
}

# 文档形式类型
DOCUMENT_TYPES = [
    "教材讲解",    # 知识点讲解、概念解释
    "试题练习",    # 题目、练习、试卷
    "笔记总结",    # 学习笔记、知识总结
    "案例分析",    # 案例分析、实例讲解
    "操作指南",    # 操作指南、教程
    "规范制度",    # 规范、制度、标准
    "参考资料",    # 参考资料手册
    "其他"
]


class DocumentClassifier:
    """智能文档分类器"""

    def __init__(self):
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    async def classify(
        self,
        content: str,
        filename: str = ""
    ) -> Dict[str, Any]:
        """
        智能分类文档

        Args:
            content: 文档内容（前2000字即可）
            filename: 文件名

        Returns:
            {
                "category": "数学",
                "doc_type": "教材讲解",
                "grade_range": ["初二", "初三"],
                "keywords": ["勾股定理", "直角三角形"],
                "summary": "简短摘要",
                "confidence": 0.9
            }
        """
        # 截取内容进行分析（节省 token）
        sample_content = content[:3000] if len(content) > 3000 else content

        # 构建分类提示词
        prompt = self._build_classify_prompt(sample_content, filename)

        try:
            response = await self.llm_client.generate(prompt)
            result = self._parse_result(response)

            logger.info(f"文档分类结果: {result['category']} ({result['confidence']})")
            return result

        except Exception as e:
            logger.error(f"文档分类失败: {e}")
            # 返回默认值
            return {
                "category": "其他",
                "doc_type": "其他",
                "grade_range": [],
                "keywords": [],
                "summary": "",
                "confidence": 0.0
            }

    def _build_classify_prompt(self, content: str, filename: str) -> str:
        """构建分类提示词"""
        categories_desc = "\n".join([f"- {k}: {v}" for k, v in DOCUMENT_CATEGORIES.items()])
        types_desc = "、".join(DOCUMENT_TYPES)

        return f"""请分析以下文档内容，进行智能分类。

【文档信息】
文件名: {filename}
内容摘要:
{content[:2000]}

【分类选项】
文档类别:
{categories_desc}

文档形式: {types_desc}
适用年级: 小学、初一、初二、初三、高一、高二、高三（可选多个）

【输出要求】
请以JSON格式输出分类结果：
```json
{{
    "category": "文档类别（从上述选项中选择）",
    "doc_type": "文档形式（从上述选项中选择）",
    "grade_range": ["适用年级"],
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "summary": "一句话摘要（50字以内）",
    "confidence": 0.9
}}
```

注意：
1. category 必须从给定的类别选项中选择
2. 如果是学科内容，grade_range 填写适用年级
3. 如果不是学科内容，grade_range 填空数组 []
4. keywords 提取 3-5 个核心关键词
5. confidence 表示分类置信度 (0-1)

只输出JSON，不要其他内容。"""

    def _parse_result(self, response: str) -> Dict[str, Any]:
        """解析分类结果"""
        try:
            # 提取 JSON
            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            result = json.loads(json_text.strip())

            # 验证并修正
            if result.get("category") not in DOCUMENT_CATEGORIES:
                result["category"] = "其他"

            if result.get("doc_type") not in DOCUMENT_TYPES:
                result["doc_type"] = "其他"

            if not isinstance(result.get("grade_range"), list):
                result["grade_range"] = []

            if not isinstance(result.get("keywords"), list):
                result["keywords"] = []

            if not result.get("summary"):
                result["summary"] = ""

            if not isinstance(result.get("confidence"), (int, float)):
                result["confidence"] = 0.5

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}")
            return {
                "category": "其他",
                "doc_type": "其他",
                "grade_range": [],
                "keywords": [],
                "summary": "",
                "confidence": 0.0
            }

    async def classify_batch(
        self,
        contents: List[str],
        filenames: List[str] = None
    ) -> List[Dict[str, Any]]:
        """批量分类文档"""
        if filenames is None:
            filenames = [""] * len(contents)

        tasks = [
            self.classify(content, filename)
            for content, filename in zip(contents, filenames)
        ]

        results = await asyncio.gather(*tasks)
        return results


# 全局实例
_classifier: Optional[DocumentClassifier] = None


def get_document_classifier() -> DocumentClassifier:
    """获取文档分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
    return _classifier
