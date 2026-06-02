#!/usr/bin/env python3
"""
RAG-KB - 基于 LangGraph 的教育问答 Agent
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def load_env():
    """加载环境变量"""
    # 设置HuggingFace镜像（国内加速）
    os.environ["HF_ENDPOINT"] = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")

    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print("✓ 环境变量已加载")
    else:
        print("⚠ 未找到 .env 文件，请确保已配置环境变量")


def check_api_key():
    """检查API密钥"""
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key or api_key == "your_dashscope_api_key_here":
        print("⚠ 警告: DASHSCOPE_API_KEY 未配置")
        print("  请在 .env 文件中设置有效的 API 密钥")
        return False
    print(f"✓ API密钥已配置: {api_key[:10]}...")
    return True


def create_directories():
    """创建必要的目录"""
    directories = [
        "./data/chroma",
        "./data/bm25_index",
        "./data/metadata",
        "./data/sessions.db",
        "./logs"
    ]

    for d in directories:
        path = Path(d)
        if path.suffix:  # 是文件
            path = path.parent
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {path}")


def start_web(host: str = "0.0.0.0", port: int = 8000):
    """启动Web服务"""
    print("\n" + "=" * 50)
    print("  RAG-KB 教育问答 Agent")
    print("=" * 50)
    print()

    load_env()
    check_api_key()
    create_directories()

    print()
    print("启动Web服务...")
    print(f"  - 对话页面: http://localhost:{port}")
    print(f"  - 知识库管理: http://localhost:{port}/knowledge")
    print(f"  - API文档: http://localhost:{port}/docs")
    print()

    # 启动uvicorn
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


def start_cli():
    """启动CLI对话模式"""
    load_env()
    check_api_key()
    create_directories()

    print("\n启动CLI对话模式...")
    from cli.main import app
    import typer
    typer.run(app)


def main():
    parser = argparse.ArgumentParser(
        description="RAG-KB 教育问答 Agent 启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py web              # 启动Web服务
  python run.py web --port 9000  # 指定端口
  python run.py cli              # 启动CLI对话模式
  python run.py upload file.pdf -s 数学  # 上传文档
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # Web服务命令
    web_parser = subparsers.add_parser("web", help="启动Web服务")
    web_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    web_parser.add_argument("--port", type=int, default=8000, help="监听端口")

    # CLI命令
    cli_parser = subparsers.add_parser("cli", help="启动CLI对话模式")

    # 上传文档命令
    upload_parser = subparsers.add_parser("upload", help="上传文档到知识库")
    upload_parser.add_argument("file", help="文件路径")
    upload_parser.add_argument("-s", "--subject", required=True, help="学科")
    upload_parser.add_argument("-t", "--title", default="", help="标题")

    args = parser.parse_args()

    if args.command == "web":
        start_web(args.host, args.port)
    elif args.command == "cli":
        start_cli()
    elif args.command == "upload":
        load_env()
        import asyncio
        from src.knowledge.manager import get_knowledge_manager

        async def upload():
            manager = get_knowledge_manager()
            result = await manager.upload(
                file_path=args.file,
                subject=args.subject,
                title=args.title
            )
            print(f"✓ 上传成功!")
            print(f"  文档ID: {result.doc_id}")
            print(f"  切片数: {result.chunk_count}")

        asyncio.run(upload())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
