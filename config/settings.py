from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "K12智能学习助手"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # LLM配置
    DASHSCOPE_API_KEY: str = Field(..., env="DASHSCOPE_API_KEY")
    CHAT_MODEL: str = "qwen-plus"
    EMBEDDING_MODEL: str = "text-embedding-v2"

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
    LOG_FILE: str = "./logs/app.log"

    # 支持的学科
    SUBJECTS: List[str] = [
        "语文", "数学", "英语", "物理", "化学",
        "生物", "历史", "地理", "政治"
    ]

    # 支持的年级
    GRADES: List[str] = [
        "小学", "初一", "初二", "初三",
        "高一", "高二", "高三"
    ]

    # 意图类型
    INTENTS: List[str] = [
        "study_qa",
        "homework_help",
        "emotion_support",
        "chitchat"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
