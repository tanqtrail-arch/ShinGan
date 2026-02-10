"""
ShinGan Web API - FastAPI サーバー

エンドポイント:
  GET  /api/health                  - ヘルスチェック
  -- カタログ --
  GET  /api/prompts                 - プロンプト一覧
  GET  /api/prompts/{id}            - プロンプト詳細
  GET  /api/categories              - カテゴリ一覧
  -- 生成 (スタブ) --
  POST /api/generate                - フリープロンプト生成
  POST /api/generate/{id}           - カタログから生成
  -- バッチ --
  POST /api/batch                   - バッチ生成
  POST /api/batch/category          - カテゴリ一括生成
  -- リファレンス画像 --
  GET  /api/references              - リファレンス一覧
  POST /api/references/{group}      - リファレンス追加
  DELETE /api/references/{group}    - リファレンス削除
  -- 画像添付 --
  POST /api/attach/{result_id}      - 画像添付
  -- プロンプトビルダー --
  GET  /api/builder/presets         - プリセット一覧
  POST /api/builder/compile         - プロンプトコンパイル
  -- 履歴 --
  GET  /api/history                 - 生成履歴
  GET  /api/history/{id}            - 生成結果詳細
  GET  /api/history/export          - 履歴エクスポート
  -- セッション --
  POST /api/session                 - セッション作成
  POST /api/session/chat            - チャット
  DELETE /api/session               - セッション終了
  GET  /api/session/state           - セッション状態
  -- 真贋クイズ --
  POST /api/quiz                    - クイズ作成（画像アップロード）
  GET  /api/quiz                    - クイズ一覧
  GET  /api/quiz/{id}               - クイズ詳細
  GET  /api/quiz/{id}/play          - クイズ出題（ランダム配置）
  POST /api/quiz/{id}/answer        - クイズ回答判定
  DELETE /api/quiz/{id}             - クイズ削除
  -- 静的ファイル --
  GET  /                            - ダッシュボード
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from shingan.agent import AgentConfig, GenerationResult, QuizItem, ShinGanAgent
from shingan.builder import PromptDraft, get_presets
from shingan.config import Settings
from shingan.prompts.catalog import (
    CATEGORY_LABELS,
    PROMPT_CATALOG,
    get_prompt_by_id,
    get_prompts_by_category,
    list_categories,
)

logger = logging.getLogger(__name__)


# === Pydantic モデル ===

class GenerateRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"
    resolution: str = "2K"
    use_thinking: bool = True
    use_search_grounding: bool = False
    reference_images: list[str] | None = None

class CatalogGenerateRequest(BaseModel):
    override_prompt: str | None = None
    reference_images: list[str] | None = None

class BatchRequest(BaseModel):
    prompts: list[dict]

class BatchCategoryRequest(BaseModel):
    category: str
    count: int | None = None
    reference_images: list[str] | None = None

class ReferenceAddRequest(BaseModel):
    paths: list[str]

class ChatRequest(BaseModel):
    message: str

class BuilderCompileRequest(BaseModel):
    subject: str = ""
    action: str = ""
    location: str = ""
    composition: str = ""
    lighting: str = ""
    style: str = ""
    constraint: str = ""
    negative: str = ""
    aspect_ratio: str = "1:1"
    resolution: str = "2K"
    use_thinking: bool = False
    use_search_grounding: bool = False
    reference_group: str | None = None

class GenerateResponse(BaseModel):
    id: str = ""
    image_url: str | None = None
    text: str | None = None
    elapsed_sec: float = 0.0
    model: str = ""
    prompt_used: str = ""
    aspect_ratio: str = "1:1"
    resolution: str = "2K"
    reference_images: list[str] = []
    status: str = "pending"
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


class QuizResponse(BaseModel):
    id: str
    title: str
    real_image_url: str | None = None
    fake_image_url: str | None = None
    explanation: str = ""
    ready: bool = False
    created_at: float = 0.0


class QuizPlayResponse(BaseModel):
    id: str
    title: str
    left_image_url: str
    right_image_url: str
    answer: str  # "left" or "right"


class QuizAnswerRequest(BaseModel):
    choice: str  # "left" or "right"
    correct_side: str  # "left" or "right" (from play response)


class QuizAnswerResponse(BaseModel):
    correct: bool
    title: str = ""
    explanation: str = ""


# === ヘルパー ===

def _result_to_response(result: GenerationResult) -> GenerateResponse:
    resp = GenerateResponse(
        id=result.id,
        text=result.text,
        elapsed_sec=result.elapsed_sec,
        model=result.model,
        prompt_used=result.prompt_used,
        aspect_ratio=result.aspect_ratio,
        resolution=result.resolution,
        reference_images=result.reference_images,
        status=result.status,
        session_id=result.session_id,
        error=result.error,
    )
    if result.image_path and result.image_path.exists():
        resp.image_url = f"/api/images/{result.image_path.name}"
    return resp


def _quiz_to_response(item: QuizItem) -> QuizResponse:
    real_url = None
    fake_url = None
    if item.real_image_path and item.real_image_path.exists():
        real_url = f"/api/images/{item.real_image_path.name}"
    if item.fake_image_path and item.fake_image_path.exists():
        fake_url = f"/api/images/{item.fake_image_path.name}"
    return QuizResponse(
        id=item.id,
        title=item.title,
        real_image_url=real_url,
        fake_image_url=fake_url,
        explanation=item.explanation,
        ready=item.ready,
        created_at=item.created_at,
    )


# === アプリ構築 ===

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    app = FastAPI(
        title="ShinGan API",
        description="Nano Banana Pro 画像生成エージェント API",
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
    agent.load_quizzes()

    # --- ヘルスチェック ---
    @app.get("/api/health", response_model=HealthResponse)
    def health():
        return HealthResponse()

    # --- カタログ ---
    @app.get("/api/prompts", response_model=list[PromptResponse])
    def get_prompts(category: str | None = None):
        prompts = get_prompts_by_category(category) if category else PROMPT_CATALOG
        return [
            PromptResponse(
                id=p.id, category=p.category,
                category_label=CATEGORY_LABELS.get(p.category, p.category),
                name=p.name, name_ja=p.name_ja, prompt=p.prompt,
                description_ja=p.description_ja, aspect_ratio=p.aspect_ratio,
                resolution=p.resolution, use_thinking=p.use_thinking,
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
            id=p.id, category=p.category,
            category_label=CATEGORY_LABELS.get(p.category, p.category),
            name=p.name, name_ja=p.name_ja, prompt=p.prompt,
            description_ja=p.description_ja, aspect_ratio=p.aspect_ratio,
            resolution=p.resolution, use_thinking=p.use_thinking,
            use_search_grounding=p.use_search_grounding,
        )

    @app.get("/api/categories")
    def get_categories():
        return [
            {"id": c, "label": CATEGORY_LABELS.get(c, c),
             "count": len(get_prompts_by_category(c))}
            for c in list_categories()
        ]

    # --- 生成（スタブ）---
    @app.post("/api/generate", response_model=GenerateResponse)
    def generate(req: GenerateRequest):
        result = agent.generate(
            req.prompt,
            aspect_ratio=req.aspect_ratio,
            resolution=req.resolution,
            use_thinking=req.use_thinking,
            use_search_grounding=req.use_search_grounding,
            reference_images=req.reference_images,
        )
        return _result_to_response(result)

    @app.post("/api/generate/{prompt_id}", response_model=GenerateResponse)
    def generate_catalog(prompt_id: str, req: CatalogGenerateRequest | None = None):
        try:
            result = agent.generate_from_catalog(
                prompt_id,
                override_prompt=req.override_prompt if req else None,
                reference_images=req.reference_images if req else None,
            )
        except ValueError as e:
            raise HTTPException(404, str(e))
        return _result_to_response(result)

    # --- バッチ ---
    @app.post("/api/batch", response_model=list[GenerateResponse])
    def batch_generate(req: BatchRequest):
        results = agent.batch_generate(req.prompts)
        return [_result_to_response(r) for r in results]

    @app.post("/api/batch/category", response_model=list[GenerateResponse])
    def batch_category(req: BatchCategoryRequest):
        try:
            results = agent.batch_from_category(
                req.category,
                count=req.count,
                reference_images=req.reference_images,
            )
        except ValueError as e:
            raise HTTPException(404, str(e))
        return [_result_to_response(r) for r in results]

    # --- リファレンス画像 ---
    @app.get("/api/references")
    def get_references(group: str | None = None):
        return agent.get_references(group)

    @app.post("/api/references/{group}")
    def add_references(group: str, req: ReferenceAddRequest):
        paths = agent.add_references(group, req.paths)
        return {"group": group, "paths": paths}

    @app.delete("/api/references/{group}")
    def clear_references(group: str):
        agent.clear_references(group)
        return {"status": "cleared", "group": group}

    # --- 画像添付 ---
    @app.post("/api/attach/{result_id}")
    async def attach_image(result_id: str, file: UploadFile = File(...)):
        save_path = config.output_dir / f"{result_id}_{file.filename}"
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        updated = agent.attach_image(result_id, str(save_path))
        if updated is None:
            raise HTTPException(404, f"結果ID '{result_id}' が見つかりません")
        return _result_to_response(updated)

    # --- プロンプトビルダー ---
    @app.get("/api/builder/presets")
    def builder_presets():
        return get_presets()

    @app.post("/api/builder/compile")
    def builder_compile(req: BuilderCompileRequest):
        draft = PromptDraft(
            subject=req.subject, action=req.action, location=req.location,
            composition=req.composition, lighting=req.lighting, style=req.style,
            constraint=req.constraint, negative=req.negative,
            aspect_ratio=req.aspect_ratio, resolution=req.resolution,
            use_thinking=req.use_thinking,
            use_search_grounding=req.use_search_grounding,
            reference_group=req.reference_group,
        )
        return {
            "compiled_prompt": draft.compile(),
            "draft": draft.to_dict(),
        }

    # --- 履歴 ---
    @app.get("/api/history")
    def get_history():
        return [_result_to_response(r).model_dump() for r in agent.history]

    @app.get("/api/history/export")
    def export_history():
        return agent.export_history()

    @app.get("/api/history/{result_id}")
    def get_result(result_id: str):
        r = agent.get_result(result_id)
        if r is None:
            raise HTTPException(404, f"結果 '{result_id}' が見つかりません")
        return _result_to_response(r)

    # --- セッション ---
    @app.post("/api/session", response_model=SessionResponse)
    def create_session():
        session_id = agent.start_chat()
        return SessionResponse(session_id=session_id, state=agent.session_state or "unknown")

    @app.post("/api/session/chat", response_model=GenerateResponse)
    def session_chat(req: ChatRequest):
        result = agent.chat(req.message)
        return _result_to_response(result)

    @app.get("/api/session/state", response_model=SessionResponse)
    def session_state():
        state = agent.session_state
        return SessionResponse(session_id="", state=state or "none")

    @app.delete("/api/session")
    def close_session():
        agent.close_chat()
        return {"status": "closed"}

    # --- 真贋クイズ ---
    @app.post("/api/quiz", response_model=QuizResponse)
    async def create_quiz(
        title: str = Form(...),
        explanation: str = Form(""),
        real_image: UploadFile = File(...),
        fake_image: UploadFile = File(...),
    ):
        item = agent.create_quiz(title, explanation)
        quiz_dir = config.output_dir / "quiz"
        quiz_dir.mkdir(parents=True, exist_ok=True)

        real_path = quiz_dir / f"{item.id}_real_{real_image.filename}"
        with open(real_path, "wb") as f:
            shutil.copyfileobj(real_image.file, f)
        agent.attach_quiz_image(item.id, "real", str(real_path))

        fake_path = quiz_dir / f"{item.id}_fake_{fake_image.filename}"
        with open(fake_path, "wb") as f:
            shutil.copyfileobj(fake_image.file, f)
        agent.attach_quiz_image(item.id, "fake", str(fake_path))

        return _quiz_to_response(item)

    @app.get("/api/quiz", response_model=list[QuizResponse])
    def list_quizzes():
        return [_quiz_to_response(q) for q in agent.quiz_list]

    @app.get("/api/quiz/{quiz_id}", response_model=QuizResponse)
    def get_quiz(quiz_id: str):
        item = agent.get_quiz(quiz_id)
        if item is None:
            raise HTTPException(404, f"クイズ '{quiz_id}' が見つかりません")
        return _quiz_to_response(item)

    @app.get("/api/quiz/{quiz_id}/play", response_model=QuizPlayResponse)
    def play_quiz(quiz_id: str):
        data = agent.play_quiz(quiz_id)
        if data is None:
            raise HTTPException(404, "クイズが見つからないか、画像が未登録です")
        left_name = Path(data["left_image"]).name
        right_name = Path(data["right_image"]).name
        return QuizPlayResponse(
            id=data["id"],
            title=data["title"],
            left_image_url=f"/api/images/{left_name}",
            right_image_url=f"/api/images/{right_name}",
            answer=data["answer"],
        )

    @app.post("/api/quiz/{quiz_id}/answer", response_model=QuizAnswerResponse)
    def answer_quiz(quiz_id: str, req: QuizAnswerRequest):
        result = agent.answer_quiz(quiz_id, req.choice, req.correct_side)
        if "error" in result:
            raise HTTPException(404, result["error"])
        return QuizAnswerResponse(**result)

    @app.delete("/api/quiz/{quiz_id}")
    def delete_quiz(quiz_id: str):
        if not agent.delete_quiz(quiz_id):
            raise HTTPException(404, f"クイズ '{quiz_id}' が見つかりません")
        return {"status": "deleted", "id": quiz_id}

    # --- 生成画像の配信 ---
    @app.get("/api/images/{filename}")
    def get_image(filename: str):
        filepath = config.output_dir / filename
        if not filepath.exists():
            filepath = config.output_dir / "quiz" / filename
        if not filepath.exists():
            raise HTTPException(404, "画像が見つかりません")
        return FileResponse(filepath, media_type="image/png")

    # --- 静的ファイル (ダッシュボード) ---
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        @app.get("/")
        def dashboard():
            return FileResponse(static_dir / "index.html")

        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


app = create_app()
