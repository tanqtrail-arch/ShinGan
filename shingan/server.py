"""
ShinGan Web API - FastAPI サーバー

エンドポイント:
  GET  /api/prompts           - プロンプトカタログ一覧
  GET  /api/prompts/{id}      - プロンプト詳細
  POST /api/generate          - フリープロンプト画像生成
  POST /api/generate/{id}     - カタログから画像生成
  POST /api/session           - チャットセッション作成
  POST /api/session/chat      - チャットメッセージ送信
  DELETE /api/session          - セッション終了
  GET  /api/session/state     - セッション状態
  GET  /api/health            - ヘルスチェック
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from shingan.agent import AgentConfig, GenerationResult, ShinGanAgent
from shingan.config import Settings
from shingan.prompts.catalog import (
    CATEGORY_LABELS,
    PROMPT_CATALOG,
    get_prompt_by_id,
    get_prompts_by_category,
    list_categories,
)
from shingan.session import SessionError

logger = logging.getLogger(__name__)


# === リクエスト / レスポンス モデル ===


class GenerateRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"
    resolution: str = "2K"
    use_thinking: bool = True
    use_search_grounding: bool = False


class CatalogGenerateRequest(BaseModel):
    override_prompt: str | None = None


class ChatRequest(BaseModel):
    message: str


class GenerateResponse(BaseModel):
    image_url: str | None = None
    image_base64: str | None = None
    text: str | None = None
    elapsed_sec: float = 0.0
    model: str = ""
    prompt_used: str = ""
    session_id: str | None = None
    error: str | None = None


class PromptResponse(BaseModel):
    id: str
    category: str
    category_label: str
    name: str
    name_ja: str
    prompt: str
    description_ja: str
    aspect_ratio: str
    resolution: str
    use_thinking: bool
    use_search_grounding: bool


class SessionResponse(BaseModel):
    session_id: str
    state: str
    message_count: int = 0


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


# === アプリ構築 ===


def _result_to_response(result: GenerationResult) -> GenerateResponse:
    """GenerationResult を API レスポンスに変換。"""
    resp = GenerateResponse(
        text=result.text,
        elapsed_sec=result.elapsed_sec,
        model=result.model,
        prompt_used=result.prompt_used,
        session_id=result.session_id,
        error=result.error,
    )
    if result.image_path and result.image_path.exists():
        resp.image_url = f"/api/images/{result.image_path.name}"
        image_bytes = result.image_path.read_bytes()
        resp.image_base64 = base64.b64encode(image_bytes).decode()
    return resp


def create_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI アプリを構築する。"""
    settings = settings or Settings.from_env()

    app = FastAPI(
        title="ShinGan API",
        description="Nano Banana Pro (Gemini 3 Pro Image) 画像生成エージェント API",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    config = AgentConfig(
        model=settings.default_model,
        output_dir=Path(settings.output_dir),
        default_resolution=settings.default_resolution,
        default_aspect_ratio=settings.default_aspect_ratio,
        use_thinking=settings.use_thinking,
        max_retries=settings.max_retries,
        retry_base_delay=settings.retry_base_delay,
    )
    agent = ShinGanAgent(config)

    # --- ヘルスチェック ---

    @app.get("/api/health", response_model=HealthResponse)
    def health():
        return HealthResponse()

    # --- プロンプトカタログ ---

    @app.get("/api/prompts", response_model=list[PromptResponse])
    def get_prompts(category: str | None = None):
        prompts = get_prompts_by_category(category) if category else PROMPT_CATALOG
        return [
            PromptResponse(
                id=p.id,
                category=p.category,
                category_label=CATEGORY_LABELS.get(p.category, p.category),
                name=p.name,
                name_ja=p.name_ja,
                prompt=p.prompt,
                description_ja=p.description_ja,
                aspect_ratio=p.aspect_ratio,
                resolution=p.resolution,
                use_thinking=p.use_thinking,
                use_search_grounding=p.use_search_grounding,
            )
            for p in prompts
        ]

    @app.get("/api/prompts/{prompt_id}", response_model=PromptResponse)
    def get_prompt(prompt_id: str):
        p = get_prompt_by_id(prompt_id)
        if p is None:
            raise HTTPException(404, f"プロンプト '{prompt_id}' が見つかりません")
        return PromptResponse(
            id=p.id,
            category=p.category,
            category_label=CATEGORY_LABELS.get(p.category, p.category),
            name=p.name,
            name_ja=p.name_ja,
            prompt=p.prompt,
            description_ja=p.description_ja,
            aspect_ratio=p.aspect_ratio,
            resolution=p.resolution,
            use_thinking=p.use_thinking,
            use_search_grounding=p.use_search_grounding,
        )

    @app.get("/api/categories")
    def get_categories():
        return [
            {"id": cat, "label": CATEGORY_LABELS.get(cat, cat), "count": len(get_prompts_by_category(cat))}
            for cat in list_categories()
        ]

    # --- 画像生成 ---

    @app.post("/api/generate", response_model=GenerateResponse)
    def generate(req: GenerateRequest):
        result = agent.generate(
            req.prompt,
            aspect_ratio=req.aspect_ratio,
            resolution=req.resolution,
            use_thinking=req.use_thinking,
            use_search_grounding=req.use_search_grounding,
        )
        return _result_to_response(result)

    @app.post("/api/generate/{prompt_id}", response_model=GenerateResponse)
    def generate_from_catalog(prompt_id: str, req: CatalogGenerateRequest | None = None):
        try:
            result = agent.generate_from_catalog(
                prompt_id,
                override_prompt=req.override_prompt if req else None,
            )
        except ValueError as e:
            raise HTTPException(404, str(e))
        return _result_to_response(result)

    # --- セッション管理 ---

    @app.post("/api/session", response_model=SessionResponse)
    def create_session():
        try:
            session_id = agent.start_chat()
        except SessionError as e:
            raise HTTPException(503, f"セッションの作成に失敗しました。もう一度お試しください。 ({e})")
        return SessionResponse(
            session_id=session_id,
            state=agent.session_state or "unknown",
        )

    @app.post("/api/session/chat", response_model=GenerateResponse)
    def session_chat(req: ChatRequest):
        if agent.session_state is None:
            raise HTTPException(400, "セッションが開始されていません。先に POST /api/session を呼んでください。")
        result = agent.chat(req.message)
        return _result_to_response(result)

    @app.get("/api/session/state", response_model=SessionResponse)
    def session_state():
        if agent._session_mgr is None:
            return SessionResponse(session_id="", state="none", message_count=0)
        info = agent._session_mgr.session
        return SessionResponse(
            session_id=info.session_id,
            state=info.state.value,
            message_count=info.message_count,
        )

    @app.post("/api/session/reset", response_model=SessionResponse)
    def reset_session():
        try:
            session_id = agent.reset_chat()
        except SessionError as e:
            raise HTTPException(503, str(e))
        return SessionResponse(
            session_id=session_id,
            state=agent.session_state or "unknown",
        )

    @app.delete("/api/session")
    def close_session():
        agent.close_chat()
        return {"status": "closed"}

    # --- 生成画像の配信 ---

    @app.get("/api/images/{filename}")
    def get_image(filename: str):
        filepath = config.output_dir / filename
        if not filepath.exists():
            raise HTTPException(404, "画像が見つかりません")
        return FileResponse(filepath, media_type="image/png")

    return app


# uvicorn shingan.server:app で起動するためのデフォルトインスタンス
app = create_app()
