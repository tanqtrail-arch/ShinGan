# ShinGan - Project Context

## Overview
Nano Banana Pro (Gemini 3 Pro Image / `gemini-3-pro-image-preview`) 画像生成エージェント。
画像生成はスタブ（外部ダッシュボードで画像を添付・管理する設計）。

## Architecture
- `shingan/agent.py` - コアエージェント（画像生成スタブ、バッチ、リファレンス、アタッチ）
- `shingan/builder.py` - プロンプトビルダー（9ステップ構造化プロンプト生成）
- `shingan/server.py` - FastAPI REST API（24エンドポイント）
- `shingan/cli.py` - CLI（list/show/gen/batch/build/chat/serve）
- `shingan/session.py` - セッション管理（指数バックオフリトライ）
- `shingan/config.py` - 設定（.env対応）
- `shingan/prompts/catalog.py` - プロンプトカタログ（10カテゴリ×20プロンプト）
- `shingan/static/` - Webダッシュボード（HTML/CSS/JS、5タブ）

## Commands
```bash
pip install -e ".[dev]"    # Install with dev deps
pytest tests/ -v           # Run all tests (54 tests)
ruff check shingan/        # Lint
shingan serve              # Start dashboard at :8080
```

## Key Design Decisions
- 画像生成はスタブ: `generate()` はメタデータJSONのみ作成、API呼び出しなし
- アタッチワークフロー: generate → pending → dashboard で画像アップロード → completed
- リファレンス画像グループ: 最大14枚/グループ
- プロンプト構造: `[Subject] [Action] in [Location]. [Composition]. [Lighting]. [Style]. [Constraint].`

## Testing
- テストは `tests/` 配下、`pytest` で実行
- `google.genai` の依存は除去済み（スタブ設計のためモック不要）
