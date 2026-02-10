"""
ShinGan Agent - Nano Banana Pro (Gemini 3 Pro Image) 画像生成エージェント

画像生成はスタブ（ダッシュボードで別管理）。
プロンプト管理・セッション・バッチ・リファレンス管理を提供。
"""

from __future__ import annotations

import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from shingan.prompts.catalog import (
    Prompt,
    get_prompt_by_id,
)

logger = logging.getLogger(__name__)

# モデル定数
MODEL_PRO = "gemini-3-pro-image-preview"
MODEL_FLASH = "gemini-2.5-flash-image"

DEFAULT_OUTPUT_DIR = Path("output")


@dataclass
class GenerationResult:
    """画像生成の結果。"""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    image_path: Path | None = None
    text: str | None = None
    elapsed_sec: float = 0.0
    model: str = ""
    prompt_used: str = ""
    session_id: str | None = None
    error: str | None = None
    aspect_ratio: str = "1:1"
    resolution: str = "2K"
    reference_images: list[str] = field(default_factory=list)
    status: str = "pending"  # pending / completed / error


@dataclass
class AgentConfig:
    """エージェント設定。"""

    model: str = MODEL_PRO
    output_dir: Path = DEFAULT_OUTPUT_DIR
    default_resolution: str = "2K"
    default_aspect_ratio: str = "1:1"
    use_thinking: bool = True
    use_search_grounding: bool = False
    max_retries: int = 4
    retry_base_delay: float = 2.0


@dataclass
class QuizItem:
    """真贋クイズの問題。"""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""  # 作品名
    real_image_path: Path | None = None  # A欄: 本物
    fake_image_path: Path | None = None  # B欄: 偽物
    explanation: str = ""  # 真贋ポイント（解説）
    created_at: float = field(default_factory=time.time)

    @property
    def ready(self) -> bool:
        """両方の画像がアップロード済みか。"""
        return self.real_image_path is not None and self.fake_image_path is not None


class ShinGanAgent:
    """Nano Banana Pro 画像生成エージェント。

    画像生成自体はスタブ。ダッシュボードで画像を添付・調整する前提。
    プロンプト構築、セッション管理、バッチ管理、リファレンス画像管理を提供。
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self._session_id: str | None = None
        self._history: list[GenerationResult] = []
        self._references: dict[str, list[str]] = {}  # group_name -> [paths]
        self._quizzes: list[QuizItem] = []

    # =========================================================================
    # プロンプト構築
    # =========================================================================

    def build_params(
        self,
        prompt: str,
        *,
        prompt_obj: Prompt | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        use_thinking: bool | None = None,
        use_search_grounding: bool | None = None,
        reference_images: list[str] | None = None,
    ) -> dict:
        """生成パラメータを dict で構築する。"""
        ar = aspect_ratio or (
            prompt_obj.aspect_ratio if prompt_obj else self.config.default_aspect_ratio
        )
        res = resolution or (
            prompt_obj.resolution if prompt_obj else self.config.default_resolution
        )
        thinking = use_thinking if use_thinking is not None else (
            prompt_obj.use_thinking if prompt_obj else self.config.use_thinking
        )
        grounding = use_search_grounding if use_search_grounding is not None else (
            prompt_obj.use_search_grounding if prompt_obj else self.config.use_search_grounding
        )

        return {
            "model": self.config.model,
            "prompt": prompt,
            "aspect_ratio": ar,
            "resolution": res,
            "use_thinking": thinking,
            "use_search_grounding": grounding,
            "reference_images": reference_images or [],
            "response_modalities": ["TEXT", "IMAGE"],
        }

    # =========================================================================
    # 生成（スタブ — 画像はダッシュボードで別管理）
    # =========================================================================

    def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        use_thinking: bool | None = None,
        use_search_grounding: bool | None = None,
        reference_images: list[str] | None = None,
    ) -> GenerationResult:
        """生成リクエストを作成する（画像はスタブ）。"""
        params = self.build_params(
            prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            use_thinking=use_thinking,
            use_search_grounding=use_search_grounding,
            reference_images=reference_images,
        )

        result = GenerationResult(
            model=params["model"],
            prompt_used=prompt,
            aspect_ratio=params["aspect_ratio"],
            resolution=params["resolution"],
            reference_images=params["reference_images"],
            status="pending",
            text="[stub] パラメータ準備完了。ダッシュボードで画像を添付してください。",
        )

        self._save_metadata(result, params)
        self._history.append(result)
        return result

    def generate_from_catalog(
        self,
        prompt_id: str,
        *,
        override_prompt: str | None = None,
        reference_images: list[str] | None = None,
    ) -> GenerationResult:
        """カタログのプロンプトIDから生成リクエストを作成する。"""
        prompt_obj = get_prompt_by_id(prompt_id)
        if prompt_obj is None:
            raise ValueError(f"プロンプトID '{prompt_id}' が見つかりません")

        text = override_prompt or prompt_obj.prompt
        params = self.build_params(text, prompt_obj=prompt_obj, reference_images=reference_images)

        result = GenerationResult(
            model=params["model"],
            prompt_used=text,
            aspect_ratio=params["aspect_ratio"],
            resolution=params["resolution"],
            reference_images=params["reference_images"],
            status="pending",
            text=f"[stub] カタログ '{prompt_id}' 準備完了。",
        )

        self._save_metadata(result, params)
        self._history.append(result)
        return result

    def _save_metadata(self, result: GenerationResult, params: dict) -> None:
        """生成メタデータをJSONで保存する。"""
        meta_path = self.config.output_dir / f"{result.id}_meta.json"
        meta = {
            "id": result.id,
            "prompt": params["prompt"],
            "model": params["model"],
            "aspect_ratio": params["aspect_ratio"],
            "resolution": params["resolution"],
            "use_thinking": params["use_thinking"],
            "use_search_grounding": params["use_search_grounding"],
            "reference_images": params["reference_images"],
            "status": result.status,
            "created_at": time.time(),
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    # =========================================================================
    # バッチ生成
    # =========================================================================

    def batch_generate(self, prompts: list[dict]) -> list[GenerationResult]:
        """複数プロンプトを一括処理する。

        prompts: [{"prompt": "..."}, ...] or [{"prompt_id": "char-pixel-mascot"}, ...]
        """
        results = []
        for item in prompts:
            if "prompt_id" in item:
                r = self.generate_from_catalog(
                    item["prompt_id"],
                    override_prompt=item.get("override_prompt"),
                    reference_images=item.get("reference_images"),
                )
            else:
                r = self.generate(
                    item["prompt"],
                    aspect_ratio=item.get("aspect_ratio"),
                    resolution=item.get("resolution"),
                    use_thinking=item.get("use_thinking"),
                    use_search_grounding=item.get("use_search_grounding"),
                    reference_images=item.get("reference_images"),
                )
            results.append(r)
        return results

    def batch_from_category(
        self,
        category: str,
        *,
        count: int | None = None,
        reference_images: list[str] | None = None,
    ) -> list[GenerationResult]:
        """カテゴリ全体を一括処理する。"""
        from shingan.prompts.catalog import get_prompts_by_category

        prompts = get_prompts_by_category(category)
        if not prompts:
            raise ValueError(f"カテゴリ '{category}' が見つかりません")
        if count is not None:
            prompts = prompts[:count]

        return [
            self.generate_from_catalog(p.id, reference_images=reference_images)
            for p in prompts
        ]

    # =========================================================================
    # リファレンス画像管理
    # =========================================================================

    def add_references(self, group: str, paths: list[str]) -> list[str]:
        """リファレンス画像グループに画像パスを追加する。"""
        if group not in self._references:
            self._references[group] = []
        for p in paths:
            if p not in self._references[group]:
                self._references[group].append(p)
        return self._references[group]

    def remove_reference(self, group: str, path: str) -> list[str]:
        """リファレンス画像を削除する。"""
        if group in self._references and path in self._references[group]:
            self._references[group].remove(path)
        return self._references.get(group, [])

    def get_references(self, group: str | None = None) -> dict[str, list[str]]:
        """リファレンス画像を取得する。"""
        if group:
            return {group: self._references.get(group, [])}
        return dict(self._references)

    def clear_references(self, group: str | None = None) -> None:
        """リファレンスをクリアする。"""
        if group:
            self._references.pop(group, None)
        else:
            self._references.clear()

    # =========================================================================
    # セッション（スタブ）
    # =========================================================================

    def start_chat(self) -> str:
        """チャットセッションを開始する。"""
        self._session_id = uuid.uuid4().hex[:12]
        return self._session_id

    @property
    def session_state(self) -> str | None:
        """現在のセッション状態を返す。"""
        if self._session_id:
            return "active"
        return None

    def chat(self, message: str) -> GenerationResult:
        """チャットメッセージ（スタブ）。"""
        if not self._session_id:
            self.start_chat()
        result = GenerationResult(
            model=self.config.model,
            prompt_used=message,
            session_id=self._session_id,
            status="pending",
            text="[stub] チャットメッセージ受信。ダッシュボードで画像を添付してください。",
        )
        self._save_metadata(result, self.build_params(message))
        self._history.append(result)
        return result

    def reset_chat(self) -> str:
        """セッションリセット。"""
        return self.start_chat()

    def close_chat(self) -> None:
        """セッションを閉じる。"""
        self._session_id = None

    # =========================================================================
    # 画像添付（ダッシュボードから）
    # =========================================================================

    def attach_image(self, result_id: str, image_path: str) -> GenerationResult | None:
        """生成結果に画像を添付する（ダッシュボードから呼ばれる）。"""
        for r in self._history:
            if r.id == result_id:
                r.image_path = Path(image_path)
                r.status = "completed"
                meta_path = self.config.output_dir / f"{r.id}_meta.json"
                if meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    meta["image_path"] = image_path
                    meta["status"] = "completed"
                    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
                return r
        return None

    # =========================================================================
    # 履歴
    # =========================================================================

    @property
    def history(self) -> list[GenerationResult]:
        """生成履歴を返す。"""
        return list(self._history)

    def get_result(self, result_id: str) -> GenerationResult | None:
        """IDで生成結果を取得する。"""
        for r in self._history:
            if r.id == result_id:
                return r
        return None

    def export_history(self) -> list[dict]:
        """履歴をエクスポート可能なdictリストで返す。"""
        return [
            {
                "id": r.id,
                "prompt": r.prompt_used,
                "model": r.model,
                "aspect_ratio": r.aspect_ratio,
                "resolution": r.resolution,
                "status": r.status,
                "image_path": str(r.image_path) if r.image_path else None,
                "reference_images": r.reference_images,
                "error": r.error,
            }
            for r in self._history
        ]

    # =========================================================================
    # 真贋クイズ
    # =========================================================================

    def create_quiz(self, title: str, explanation: str = "") -> QuizItem:
        """クイズ問題を作成する。"""
        quiz_dir = self.config.output_dir / "quiz"
        quiz_dir.mkdir(parents=True, exist_ok=True)
        item = QuizItem(title=title, explanation=explanation)
        self._quizzes.append(item)
        self._save_quiz_meta(item)
        return item

    def get_quiz(self, quiz_id: str) -> QuizItem | None:
        """IDでクイズを取得する。"""
        for q in self._quizzes:
            if q.id == quiz_id:
                return q
        return None

    @property
    def quiz_list(self) -> list[QuizItem]:
        """全クイズ一覧を返す。"""
        return list(self._quizzes)

    def delete_quiz(self, quiz_id: str) -> bool:
        """クイズを削除する。"""
        for i, q in enumerate(self._quizzes):
            if q.id == quiz_id:
                self._quizzes.pop(i)
                meta_path = self.config.output_dir / "quiz" / f"{quiz_id}_meta.json"
                if meta_path.exists():
                    meta_path.unlink()
                return True
        return False

    def attach_quiz_image(
        self, quiz_id: str, image_type: str, image_path: str
    ) -> QuizItem | None:
        """クイズに画像を添付する。image_type: 'real' or 'fake'"""
        item = self.get_quiz(quiz_id)
        if item is None:
            return None
        if image_type == "real":
            item.real_image_path = Path(image_path)
        elif image_type == "fake":
            item.fake_image_path = Path(image_path)
        else:
            return None
        self._save_quiz_meta(item)
        return item

    def play_quiz(self, quiz_id: str) -> dict | None:
        """クイズ出題用データを返す（本物の位置をランダム化）。"""
        item = self.get_quiz(quiz_id)
        if item is None or not item.ready:
            return None
        real_on_left = random.choice([True, False])
        if real_on_left:
            left_path = item.real_image_path
            right_path = item.fake_image_path
        else:
            left_path = item.fake_image_path
            right_path = item.real_image_path
        return {
            "id": item.id,
            "title": item.title,
            "left_image": str(left_path),
            "right_image": str(right_path),
            "answer": "left" if real_on_left else "right",
        }

    def answer_quiz(self, quiz_id: str, choice: str, correct_side: str) -> dict:
        """クイズの回答を判定する。"""
        item = self.get_quiz(quiz_id)
        if item is None:
            return {"correct": False, "error": "クイズが見つかりません"}
        is_correct = choice == correct_side
        result = {
            "correct": is_correct,
            "title": item.title,
            "explanation": item.explanation if not is_correct else "",
        }
        return result

    def _save_quiz_meta(self, item: QuizItem) -> None:
        """クイズメタデータをJSONで保存する。"""
        quiz_dir = self.config.output_dir / "quiz"
        quiz_dir.mkdir(parents=True, exist_ok=True)
        meta_path = quiz_dir / f"{item.id}_meta.json"
        meta = {
            "id": item.id,
            "title": item.title,
            "explanation": item.explanation,
            "real_image_path": str(item.real_image_path) if item.real_image_path else None,
            "fake_image_path": str(item.fake_image_path) if item.fake_image_path else None,
            "created_at": item.created_at,
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    def load_quizzes(self) -> None:
        """ディスクからクイズメタデータを読み込む。"""
        quiz_dir = self.config.output_dir / "quiz"
        if not quiz_dir.exists():
            return
        for meta_path in sorted(quiz_dir.glob("*_meta.json")):
            try:
                meta = json.loads(meta_path.read_text())
                item = QuizItem(
                    id=meta["id"],
                    title=meta["title"],
                    explanation=meta.get("explanation", ""),
                    created_at=meta.get("created_at", 0.0),
                )
                if meta.get("real_image_path"):
                    item.real_image_path = Path(meta["real_image_path"])
                if meta.get("fake_image_path"):
                    item.fake_image_path = Path(meta["fake_image_path"])
                if not any(q.id == item.id for q in self._quizzes):
                    self._quizzes.append(item)
            except (json.JSONDecodeError, KeyError):
                logger.warning("クイズメタデータの読み込みに失敗: %s", meta_path)
