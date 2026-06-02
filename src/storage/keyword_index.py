from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.qparser import QueryParser, OrGroup
from whoosh.analysis import ChineseAnalyzer
from typing import List, Optional, Dict, Any
from pathlib import Path
from loguru import logger

from config.settings import settings


class KeywordIndex:
    """BM25关键词索引"""

    def __init__(self, index_dir: Optional[str] = None):
        self.index_dir = index_dir or settings.BM25_INDEX_DIR

        # 确保目录存在
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)

        # 定义schema
        self.schema = Schema(
            doc_id=ID(stored=True, unique=True),
            content=TEXT(analyzer=ChineseAnalyzer(), stored=True),
            subject=KEYWORD(stored=True)
        )

        # 初始化索引
        if exists_in(self.index_dir):
            self._ix = open_dir(self.index_dir)
        else:
            self._ix = create_in(self.index_dir, self.schema)

        logger.info(f"关键词索引初始化完成: path={self.index_dir}")

    def add(self, docs: List[Dict[str, Any]]) -> int:
        """添加文档到索引"""
        try:
            writer = self._ix.writer()
            count = 0

            for doc in docs:
                writer.add_document(
                    doc_id=doc["doc_id"],
                    content=doc["content"],
                    subject=doc.get("metadata", {}).get("subject", "")
                )
                count += 1

            writer.commit()
            logger.debug(f"成功添加 {count} 个文档到索引")
            return count
        except Exception as e:
            logger.error(f"添加文档到索引失败: {e}")
            raise

    def search(self, query: str, top_k: int = 10, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """关键词检索"""
        try:
            searcher = self._ix.searcher()

            # 构建查询
            parser = QueryParser("content", self._ix.schema, group=OrGroup)
            q = parser.parse(query)

            # 如果指定了学科，添加过滤
            if subject:
                from whoosh.query import And, Term
                q = And([q, Term("subject", subject)])

            # 执行搜索
            results = searcher.search(q, limit=top_k)

            # 格式化结果
            formatted = []
            for hit in results:
                formatted.append({
                    "doc_id": hit["doc_id"],
                    "content": hit["content"],
                    "score": hit.score,
                    "metadata": {"subject": hit.get("subject", "")}
                })

            searcher.close()
            logger.debug(f"关键词检索返回 {len(formatted)} 条结果")
            return formatted
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []

    def delete(self, doc_ids: List[str]) -> int:
        """从索引删除文档"""
        try:
            writer = self._ix.writer()
            count = 0

            for doc_id in doc_ids:
                writer.delete_by_term("doc_id", doc_id)
                count += 1

            writer.commit()
            logger.debug(f"从索引删除 {count} 个文档")
            return count
        except Exception as e:
            logger.error(f"从索引删除文档失败: {e}")
            raise

    def count(self) -> int:
        """获取文档数量"""
        searcher = self._ix.searcher()
        count = searcher.doc_count()
        searcher.close()
        return count

    def clear(self):
        """清空索引"""
        writer = self._ix.writer()
        writer.commit(mergetype="clear")
        logger.debug("索引已清空")


# 全局实例
_index: Optional[KeywordIndex] = None


def get_keyword_index() -> KeywordIndex:
    """获取关键词索引实例"""
    global _index
    if _index is None:
        _index = KeywordIndex()
    return _index
