# src/agent/tools/web_fetch_tool.py

import re
from loguru import logger
import httpx
from bs4 import BeautifulSoup

from .base import BaseTool, ToolParameter, ToolResult


class WebFetchTool(BaseTool):
    """网页抓取工具 - 获取指定URL的网页内容"""

    name = "web_fetch"
    description = """抓取指定URL的网页内容，用于深入了解某个网页的详细信息。

适用场景：
- 用户提供了具体的URL链接，想要了解内容
- 需要查看某个项目的README或文档
- 需要获取某个网页的详细内容进行分析

参数说明：
- url: 要抓取的网页地址（必须是完整的URL，如 https://example.com）
"""

    parameters = [
        ToolParameter(
            name="url",
            type="string",
            description="要抓取的网页URL，必须是完整的URL（包含http://或https://）",
            required=True
        ),
        ToolParameter(
            name="max_length",
            type="integer",
            description="返回内容的最大字符数，默认5000",
            required=False
        )
    ]

    async def execute(
        self,
        url: str,
        max_length: int = 5000,
        **kwargs
    ) -> ToolResult:
        """执行网页抓取"""
        # 验证URL
        if not url.startswith(("http://", "https://")):
            return ToolResult(success=False, error=f"无效的URL格式，必须以http://或https://开头: {url}")

        try:
            logger.info(f"开始抓取网页: {url}")

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                )

                if response.status_code != 200:
                    logger.error(f"网页请求失败: {response.status_code}")
                    return ToolResult(success=False, error=f"网页请求失败，状态码: {response.status_code}")

                content_type = response.headers.get("content-type", "")

                # 处理HTML页面
                if "text/html" in content_type:
                    text = self._parse_html(response.text, url)
                else:
                    # 非HTML内容，直接返回文本
                    text = response.text[:max_length]

                # 截断过长的内容
                if len(text) > max_length:
                    text = text[:max_length] + "\n... (内容已截断)"

                logger.info(f"网页抓取成功: {url}, 内容长度: {len(text)}")
                return ToolResult(success=True, data=f"【网页内容】\nURL: {url}\n\n{text}")

        except httpx.TimeoutException:
            logger.error(f"网页抓取超时: {url}")
            return ToolResult(success=False, error="网页抓取超时，请稍后重试")
        except Exception as e:
            logger.error(f"网页抓取失败: {e}")
            return ToolResult(success=False, error=f"网页抓取失败: {str(e)}")

    def _parse_html(self, html: str, url: str) -> str:
        """解析HTML，提取主要内容"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 移除不需要的标签
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

            # 特殊处理GitHub页面
            if 'github.com' in url:
                return self._parse_github(soup, url)

            # 尝试获取主要内容区域
            main_content = None
            for selector in ['article', 'main', '.content', '.post-content', '.article-content', '#content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                main_content = soup.body if soup.body else soup

            # 获取标题
            title = ""
            if soup.title:
                title = f"标题: {soup.title.string.strip()}\n\n"

            # 提取文本
            text = main_content.get_text(separator='\n', strip=True)

            # 清理多余空行
            text = re.sub(r'\n{3,}', '\n\n', text)

            return title + text

        except Exception as e:
            logger.warning(f"HTML解析失败，返回原始文本: {e}")
            # 如果解析失败，简单地移除HTML标签
            text = re.sub(r'<[^>]+>', '', html)
            return text[:5000]

    def _parse_github(self, soup, url: str) -> str:
        """解析GitHub页面"""
        parts = [f"GitHub URL: {url}"]

        # 获取仓库名称
        repo_title = soup.select_one('strong[itemprop="name"]')
        if repo_title:
            parts.append(f"项目名称: {repo_title.get_text(strip=True)}")

        # 获取描述
        description = soup.select_one('p.f4')
        if description:
            parts.append(f"描述: {description.get_text(strip=True)}")

        # 获取README
        readme = soup.select_one('article.markdown-body, #readme .markdown-body')
        if readme:
            readme_text = readme.get_text(separator='\n', strip=True)
            # 清理README
            readme_text = re.sub(r'\n{3,}', '\n\n', readme_text)
            parts.append(f"\n【README内容】\n{readme_text}")

        # 获取Stars/Forks等统计
        stats = soup.select('span.Counter')
        if len(stats) >= 2:
            parts.append(f"\n【统计信息】")
            stars = stats[0].get_text(strip=True) if len(stats) > 0 else "N/A"
            forks = stats[1].get_text(strip=True) if len(stats) > 1 else "N/A"
            parts.append(f"Stars: {stars}, Forks: {forks}")

        return '\n'.join(parts) if parts else "无法解析GitHub页面内容"
