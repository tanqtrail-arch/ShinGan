"""
ShinGan CLI - コマンドラインインターフェース

使い方:
  shingan list                  # プロンプト一覧
  shingan generate <prompt_id>  # カタログから生成
  shingan gen "自由なプロンプト" # フリープロンプトで生成
  shingan chat                  # 対話モード
  shingan edit <image> "指示"   # 画像編集
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from shingan.agent import AgentConfig, ShinGanAgent, MODEL_PRO, MODEL_FLASH
from shingan.prompts.catalog import (
    CATEGORY_LABELS,
    PROMPT_CATALOG,
    get_prompt_by_id,
    get_prompts_by_category,
    list_categories,
)

console = Console()


@click.group()
@click.option("--model", default=MODEL_PRO, help="使用モデル (pro/flash)")
@click.option("--output-dir", default="output", help="出力ディレクトリ")
@click.pass_context
def main(ctx, model: str, output_dir: str):
    """ShinGan - Nano Banana Pro 画像生成エージェント"""
    if model == "flash":
        model = MODEL_FLASH
    elif model == "pro":
        model = MODEL_PRO

    ctx.ensure_object(dict)
    ctx.obj["config"] = AgentConfig(
        model=model,
        output_dir=Path(output_dir),
    )


@main.command("list")
@click.option("--category", "-c", default=None, help="カテゴリでフィルタ")
def list_prompts(category: str | None):
    """プロンプトカタログ一覧を表示する。"""
    table = Table(title="ShinGan プロンプトカタログ (Nano Banana Pro)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("カテゴリ", style="magenta")
    table.add_column("名前", style="green")
    table.add_column("解像度", justify="center")
    table.add_column("比率", justify="center")
    table.add_column("Thinking", justify="center")
    table.add_column("Search", justify="center")

    prompts = PROMPT_CATALOG
    if category:
        prompts = get_prompts_by_category(category)
        if not prompts:
            console.print(f"[red]カテゴリ '{category}' が見つかりません[/red]")
            console.print(f"利用可能: {', '.join(list_categories())}")
            return

    for p in prompts:
        cat_label = CATEGORY_LABELS.get(p.category, p.category)
        table.add_row(
            p.id,
            cat_label,
            p.name_ja,
            p.resolution,
            p.aspect_ratio,
            "✓" if p.use_thinking else "",
            "✓" if p.use_search_grounding else "",
        )

    console.print(table)
    console.print(f"\n合計: [bold]{len(prompts)}[/bold] プロンプト")

    if not category:
        console.print("\n[dim]カテゴリ一覧:[/dim]")
        for cat in list_categories():
            label = CATEGORY_LABELS.get(cat, cat)
            count = len(get_prompts_by_category(cat))
            console.print(f"  [cyan]{cat}[/cyan] - {label} ({count})")


@main.command("show")
@click.argument("prompt_id")
def show_prompt(prompt_id: str):
    """プロンプトの詳細を表示する。"""
    p = get_prompt_by_id(prompt_id)
    if p is None:
        console.print(f"[red]プロンプト '{prompt_id}' が見つかりません[/red]")
        return

    console.print(f"\n[bold cyan]{p.name_ja}[/bold cyan] ({p.name})")
    console.print(f"ID: [cyan]{p.id}[/cyan]")
    console.print(f"カテゴリ: [magenta]{CATEGORY_LABELS.get(p.category, p.category)}[/magenta]")
    console.print(f"解像度: {p.resolution} / 比率: {p.aspect_ratio}")
    console.print(f"Thinking: {'有効' if p.use_thinking else '無効'}")
    console.print(f"Search Grounding: {'有効' if p.use_search_grounding else '無効'}")
    console.print(f"\n[bold]プロンプト:[/bold]")
    console.print(f"[green]{p.prompt}[/green]")
    console.print(f"\n[dim]{p.description_ja}[/dim]")


@main.command("generate")
@click.argument("prompt_id")
@click.pass_context
def generate_from_catalog(ctx, prompt_id: str):
    """カタログのプロンプトから画像を生成する。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)

    p = get_prompt_by_id(prompt_id)
    if p is None:
        console.print(f"[red]プロンプト '{prompt_id}' が見つかりません[/red]")
        return

    console.print(f"[bold]生成中...[/bold] {p.name_ja}")
    console.print(f"  モデル: {config.model}")
    console.print(f"  解像度: {p.resolution} / 比率: {p.aspect_ratio}")

    with console.status("Nano Banana Pro で生成中..."):
        result = agent.generate_from_catalog(prompt_id)

    if result.image_path:
        console.print(f"[green]✓ 画像保存: {result.image_path}[/green]")
    if result.text:
        console.print(f"[dim]モデル応答: {result.text}[/dim]")
    console.print(f"[dim]所要時間: {result.elapsed_sec:.1f}秒[/dim]")


@main.command("gen")
@click.argument("prompt")
@click.option("--aspect-ratio", "-a", default="1:1", help="アスペクト比")
@click.option("--resolution", "-r", default="2K", help="解像度 (1K/2K/4K)")
@click.option("--thinking/--no-thinking", default=True, help="Thinkingモード")
@click.option("--search/--no-search", default=False, help="Search Grounding")
@click.pass_context
def generate_free(ctx, prompt: str, aspect_ratio: str, resolution: str, thinking: bool, search: bool):
    """フリープロンプトで画像を生成する。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)

    console.print(f"[bold]生成中...[/bold]")
    console.print(f"  プロンプト: {prompt[:80]}...")
    console.print(f"  モデル: {config.model} / 解像度: {resolution} / 比率: {aspect_ratio}")

    with console.status("Nano Banana Pro で生成中..."):
        result = agent.generate(
            prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            use_thinking=thinking,
            use_search_grounding=search,
        )

    if result.image_path:
        console.print(f"[green]✓ 画像保存: {result.image_path}[/green]")
    if result.text:
        console.print(f"[dim]モデル応答: {result.text}[/dim]")
    console.print(f"[dim]所要時間: {result.elapsed_sec:.1f}秒[/dim]")


@main.command("chat")
@click.pass_context
def chat_mode(ctx):
    """対話型チャットモードで画像を生成・編集する。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)

    console.print("[bold]ShinGan チャットモード[/bold]")
    console.print(f"モデル: {config.model}")
    console.print("'quit' で終了 / 'history' で履歴表示\n")

    agent.start_chat()

    while True:
        try:
            user_input = console.input("[bold cyan]あなた>[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n終了します。")
            break

        if user_input.strip().lower() in ("quit", "exit", "q"):
            console.print("終了します。")
            break

        if user_input.strip().lower() == "history":
            for i, h in enumerate(agent.history):
                console.print(f"  [{i+1}] {h['prompt'][:60]}...")
            continue

        if not user_input.strip():
            continue

        with console.status("生成中..."):
            result = agent.chat(user_input)

        if result.image_path:
            console.print(f"[green]✓ 画像保存: {result.image_path}[/green]")
        if result.text:
            console.print(f"[bold]ShinGan>[/bold] {result.text}")
        console.print(f"[dim]({result.elapsed_sec:.1f}秒)[/dim]\n")


@main.command("edit")
@click.argument("image_path")
@click.argument("edit_prompt")
@click.option("--aspect-ratio", "-a", default=None, help="アスペクト比")
@click.option("--resolution", "-r", default=None, help="解像度")
@click.pass_context
def edit_image(ctx, image_path: str, edit_prompt: str, aspect_ratio: str | None, resolution: str | None):
    """既存画像を編集する。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)

    if not Path(image_path).exists():
        console.print(f"[red]画像ファイルが見つかりません: {image_path}[/red]")
        return

    console.print(f"[bold]画像編集中...[/bold]")
    console.print(f"  元画像: {image_path}")
    console.print(f"  指示: {edit_prompt}")

    with console.status("編集中..."):
        result = agent.edit_image(
            image_path,
            edit_prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )

    if result.image_path:
        console.print(f"[green]✓ 編集後画像: {result.image_path}[/green]")
    if result.text:
        console.print(f"[dim]モデル応答: {result.text}[/dim]")
    console.print(f"[dim]所要時間: {result.elapsed_sec:.1f}秒[/dim]")


if __name__ == "__main__":
    main()
