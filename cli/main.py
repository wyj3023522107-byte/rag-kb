# cli/main.py

import asyncio
import typer
from typer import Typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path
from typing import Optional, List

# 初始化
app = Typer(name="k12-assistant", help="K12智能学习助手")
console = Console()


@app.command()
def chat():
    """启动对话模式"""
    console.print(Panel.fit(
        "[bold green]K12智能学习助手[/bold green]\n"
        "输入问题开始对话，输入 'quit' 退出",
        title="欢迎"
    ))

    asyncio.run(_chat_loop())


async def _chat_loop():
    """对话循环"""
    from src.agent.graph import get_agent

    agent = get_agent()
    session_id = None

    while True:
        try:
            # 获取用户输入
            query = console.input("[bold blue]你:[/bold blue] ")

            if query.lower() in ["quit", "exit", "q"]:
                console.print("[yellow]再见！[/yellow]")
                break

            if not query.strip():
                continue

            # 调用Agent
            with console.status("[bold green]思考中...[/bold green]"):
                result = await agent.run(query, session_id)
                session_id = result["session_id"]

            # 显示响应
            console.print("\n[bold green]助手:[/bold green]")
            console.print(Markdown(result["response"]))
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]再见！[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


@app.command()
def upload(
    file_path: str = typer.Argument(..., help="文件路径"),
    subject: str = typer.Option(..., "--subject", "-s", help="学科"),
    grade: List[str] = typer.Option([], "--grade", "-g", help="年级"),
    title: str = typer.Option("", "--title", "-t", help="标题")
):
    """上传文档到知识库"""
    asyncio.run(_upload_document(file_path, subject, grade, title))


async def _upload_document(file_path: str, subject: str, grade: List[str], title: str):
    """上传文档"""
    from src.knowledge.manager import get_knowledge_manager

    if not Path(file_path).exists():
        console.print(f"[red]文件不存在: {file_path}[/red]")
        return

    manager = get_knowledge_manager()

    with console.status("[bold green]处理中...[/bold green]"):
        result = await manager.upload(
            file_path=file_path,
            subject=subject,
            grade_range=grade,
            title=title
        )

    console.print(f"[green]上传成功![/green]")
    console.print(f"  文档ID: {result.doc_id}")
    console.print(f"  切片数: {result.chunk_count}")


@app.command()
def list_docs(
    subject: str = typer.Option(None, "--subject", "-s", help="按学科筛选")
):
    """列出知识库文档"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()
    docs = manager.list(subject=subject)

    if not docs:
        console.print("[yellow]暂无文档[/yellow]")
        return

    from rich.table import Table
    table = Table(title="知识库文档")
    table.add_column("ID", style="cyan")
    table.add_column("文件名", style="green")
    table.add_column("学科", style="yellow")
    table.add_column("切片数", style="magenta")

    for doc in docs:
        table.add_row(
            doc.doc_id[:12] + "...",
            doc.filename,
            doc.subject,
            str(doc.chunk_count)
        )

    console.print(table)


@app.command()
def stats():
    """查看知识库统计"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()
    stats = manager.stats()

    console.print(Panel.fit(
        f"[bold]总文档数:[/bold] {stats['total_documents']}\n"
        f"[bold]总切片数:[/bold] {stats['total_chunks']}\n"
        f"[bold]存储大小:[/bold] {stats['storage_size_mb']} MB"
    ))

    if stats["by_subject"]:
        from rich.table import Table
        table = Table(title="学科分布")
        table.add_column("学科", style="cyan")
        table.add_column("文档数", style="green")
        table.add_column("切片数", style="yellow")

        for subject, data in stats["by_subject"].items():
            table.add_row(subject, str(data["docs"]), str(data["chunks"]))

        console.print(table)


@app.command()
def delete(doc_id: str = typer.Argument(..., help="文档ID")):
    """删除文档"""
    from src.knowledge.manager import get_knowledge_manager

    manager = get_knowledge_manager()

    if manager.delete(doc_id):
        console.print(f"[green]删除成功: {doc_id}[/green]")
    else:
        console.print(f"[red]文档不存在: {doc_id}[/red]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="主机地址"),
    port: int = typer.Option(8000, "--port", "-p", help="端口")
):
    """启动Web服务"""
    import uvicorn

    console.print(f"[green]启动Web服务: http://{host}:{port}[/green]")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
