from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # LLM配置
    DASHSCOPE_API_KEY: str = Field(..., env="DASHSCOPE_API_KEY")
    # 优先使用env 变量配置模型
    CHAT_MODEL: str = "qwen-plus"
    EMBEDDING_MODEL: str = "text-embedding-v2"

    # Embedding配置 (硅基流动)
    EMBEDDING_API_KEY: str = Field("", env="EMBEDDING_API_KEY")
    EMBEDDING_BASE_URL: str = Field("https://api.siliconflow.cn/v1", env="EMBEDDING_BASE_URL")

    # Rerank配置 (硅基流动)
    RERANK_API_KEY: str = Field("", env="EMBEDDING_API_KEY")  # 默认使用同一个 Key
    RERANK_BASE_URL: str = Field("https://api.siliconflow.cn/v1", env="RERANK_BASE_URL")
    RERANK_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # Tavily搜索API
    TAVILY_API_KEY: str = Field("", env="TAVILY_API_KEY")

    # 模型参数
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048
    TOP_P: float = 0.9

    # 存储路径
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    BM25_INDEX_DIR: str = "./data/bm25_index"
    METADATA_DIR: str = "./data/metadata"

    # 文档处理
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # 对话配置
    MAX_HISTORY_TURNS: int = 20

    # 日志配置
    LOG_LEVEL: str = "INFO"
    APP_LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
