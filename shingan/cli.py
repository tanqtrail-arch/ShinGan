"""
ShinGan CLI - コマンドラインインターフェース

使い方:
  shingan list                       # プロンプト一覧
  shingan show <id>                  # プロンプト詳細
  shingan generate <prompt_id>       # カタログから生成
  shingan gen "プロンプト"            # フリー生成
  shingan batch --category character # カテゴリ一括
  shingan build                      # 対話型ビルダー
  shingan chat                       # 対話モード
  shingan serve                      # Web API サーバー
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from shingan.agent import AgentConfig, ShinGanAgent, MODEL_PRO, MODEL_FLASH
from shingan.builder import (
    ASPECT_RATIOS,
    COMPOSITIONS,
    LIGHTINGS,
    RESOLUTIONS,
    STYLES,
    PromptDraft,
)
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


# =========================================================================
# カタログ
# =========================================================================

@main.command("list")
@click.option("--category", "-c", default=None, help="カテゴリでフィルタ")
def list_prompts(category: str | None):
    """プロンプトカタログ一覧を表示する。"""
    table = Table(title="ShinGan プロンプトカタログ")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("カテゴリ", style="magenta")
    table.add_column("名前", style="green")
    table.add_column("解像度", justify="center")
    table.add_column("比率", justify="center")
    table.add_column("TH", justify="center")
    table.add_column("SR", justify="center")

    prompts = PROMPT_CATALOG
    if category:
        prompts = get_prompts_by_category(category)
        if not prompts:
            console.print(f"[red]カテゴリ '{category}' が見つかりません[/red]")
            return

    for p in prompts:
        table.add_row(
            p.id, CATEGORY_LABELS.get(p.category, p.category),
            p.name_ja, p.resolution, p.aspect_ratio,
            "o" if p.use_thinking else "", "o" if p.use_search_grounding else "",
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
    console.print(f"\n[bold]プロンプト:[/bold]\n[green]{p.prompt}[/green]")
    console.print(f"\n[dim]{p.description_ja}[/dim]")


# =========================================================================
# 生成
# =========================================================================

@main.command("generate")
@click.argument("prompt_id")
@click.pass_context
def generate_from_catalog(ctx, prompt_id: str):
    """カタログのプロンプトから生成リクエストを作成する。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)
    p = get_prompt_by_id(prompt_id)
    if p is None:
        console.print(f"[red]プロンプト '{prompt_id}' が見つかりません[/red]")
        return

    result = agent.generate_from_catalog(prompt_id)
    console.print(f"[green]準備完了[/green] {p.name_ja}")
    console.print(f"  ID: {result.id}")
    console.print(f"  ステータス: {result.status}")
    console.print(f"  メタデータ: output/{result.id}_meta.json")


@main.command("gen")
@click.argument("prompt")
@click.option("--aspect-ratio", "-a", default="1:1")
@click.option("--resolution", "-r", default="2K")
@click.pass_context
def generate_free(ctx, prompt: str, aspect_ratio: str, resolution: str):
    """フリープロンプトで生成リクエストを作成する。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)

    result = agent.generate(prompt, aspect_ratio=aspect_ratio, resolution=resolution)
    console.print(f"[green]準備完了[/green]")
    console.print(f"  ID: {result.id}")
    console.print(f"  プロンプト: {prompt[:60]}...")
    console.print(f"  メタデータ: output/{result.id}_meta.json")


# =========================================================================
# バッチ
# =========================================================================

@main.command("batch")
@click.option("--category", "-c", required=True, help="カテゴリ")
@click.option("--count", "-n", default=None, type=int, help="件数上限")
@click.pass_context
def batch_generate(ctx, category: str, count: int | None):
    """カテゴリ全体を一括生成する。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)

    try:
        results = agent.batch_from_category(category, count=count)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    console.print(f"[green]バッチ準備完了[/green] {len(results)}件")
    for r in results:
        console.print(f"  {r.id} - {r.prompt_used[:50]}...")


# =========================================================================
# プロンプトビルダー
# =========================================================================

def _pick(label: str, options: dict[str, str]) -> str:
    """選択肢から選ばせる。空Enterでスキップ。"""
    console.print(f"\n[bold]{label}[/bold]")
    keys = list(options.keys())
    for i, (k, v) in enumerate(options.items()):
        console.print(f"  [cyan]{i+1}[/cyan]. {k} - {v}")
    console.print(f"  [dim]Enter でスキップ / 番号 or キーワード入力[/dim]")

    choice = Prompt.ask("選択", default="")
    if not choice:
        return ""
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            return options[keys[idx]]
    if choice in options:
        return options[choice]
    return choice  # 自由入力


@main.command("build")
@click.pass_context
def build_prompt(ctx):
    """対話型プロンプトビルダー。"""
    config = ctx.obj["config"]

    console.print(Panel("[bold]ShinGan プロンプトビルダー[/bold]\n"
                        "ステップごとにプロンプトを組み立てます。"))

    draft = PromptDraft()

    # 1. Subject
    draft.subject = Prompt.ask("\n[bold]1. 被写体[/bold] (何を描く？)", default="")

    # 2. Action
    draft.action = Prompt.ask("[bold]2. アクション[/bold] (何をしている？)", default="")

    # 3. Location
    draft.location = Prompt.ask("[bold]3. 場所/文脈[/bold]", default="")

    # 4. Style
    draft.style = _pick("4. スタイル", STYLES)

    # 5. Composition
    draft.composition = _pick("5. 構図/カメラ", COMPOSITIONS)

    # 6. Lighting
    draft.lighting = _pick("6. ライティング", LIGHTINGS)

    # 7. Constraint
    draft.constraint = Prompt.ask("\n[bold]7. 追加指示[/bold] (テキスト描画、制約等)", default="")

    # 8. Aspect Ratio
    draft.aspect_ratio = _pick("8. アスペクト比", ASPECT_RATIOS) or "1:1"
    # _pick returns the description, so re-map
    for k, v in ASPECT_RATIOS.items():
        if draft.aspect_ratio == v:
            draft.aspect_ratio = k
            break

    # 9. Resolution
    draft.resolution = _pick("9. 解像度", RESOLUTIONS) or "2K"
    for k, v in RESOLUTIONS.items():
        if draft.resolution == v:
            draft.resolution = k
            break

    # Compile and show
    compiled = draft.compile()
    console.print(Panel(f"[green]{compiled}[/green]", title="生成プロンプト"))
    console.print(f"比率: {draft.aspect_ratio} / 解像度: {draft.resolution}")

    # Generate?
    do_gen = Prompt.ask("\nこのプロンプトで生成リクエストを作成しますか？", choices=["y", "n"], default="y")
    if do_gen == "y":
        agent = ShinGanAgent(config)
        result = agent.generate(
            compiled,
            aspect_ratio=draft.aspect_ratio,
            resolution=draft.resolution,
        )
        console.print(f"\n[green]準備完了[/green] ID: {result.id}")
        console.print(f"メタデータ: output/{result.id}_meta.json")


# =========================================================================
# チャット
# =========================================================================

@main.command("chat")
@click.pass_context
def chat_mode(ctx):
    """対話型チャットモード。"""
    config = ctx.obj["config"]
    agent = ShinGanAgent(config)

    console.print("[bold]ShinGan チャットモード[/bold] (stub)")
    console.print("'quit' で終了 / 'history' で履歴\n")

    agent.start_chat()

    while True:
        try:
            user_input = console.input("[bold cyan]> [/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break

        cmd = user_input.strip().lower()
        if cmd in ("quit", "exit", "q"):
            break
        if cmd == "history":
            for r in agent.history:
                console.print(f"  {r.id} - {r.prompt_used[:50]}...")
            continue
        if not cmd:
            continue

        result = agent.chat(user_input)
        console.print(f"  [{result.id}] {result.text}")
        console.print()


# =========================================================================
# サーバー
# =========================================================================

@main.command("serve")
@click.option("--host", default="0.0.0.0")
@click.option("--port", "-p", default=8080, type=int)
@click.option("--reload", is_flag=True, help="自動リロード（開発用）")
def serve(host: str, port: int, reload: bool):
    """Web APIサーバーを起動する。"""
    import uvicorn

    console.print(f"[bold]ShinGan API Server[/bold]")
    console.print(f"  http://{host}:{port}")
    console.print(f"  Docs: http://{host}:{port}/docs")

    uvicorn.run("shingan.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
