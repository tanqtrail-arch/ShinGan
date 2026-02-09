"""
ShinGan Agent - Nano Banana Pro (Gemini 3 Pro Image) 画像生成エージェント

対話型のイメージ生成エージェント。テキストプロンプトからの生成、
画像編集、マルチターン会話によるイテレーティブな改善をサポート。
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from google import genai
from google.genai import types

from shingan.prompts.catalog import (
    PROMPT_CATALOG,
    Prompt,
    get_prompt_by_id,
)


# モデル定数
MODEL_PRO = "gemini-3-pro-image-preview"
MODEL_FLASH = "gemini-2.5-flash-image"

DEFAULT_OUTPUT_DIR = Path("output")


@dataclass
class GenerationResult:
    """画像生成の結果。"""

    image_path: Path | None = None
    text: str | None = None
    elapsed_sec: float = 0.0
    model: str = ""
    prompt_used: str = ""


@dataclass
class AgentConfig:
    """エージェント設定。"""

    model: str = MODEL_PRO
    output_dir: Path = DEFAULT_OUTPUT_DIR
    default_resolution: str = "2K"
    default_aspect_ratio: str = "1:1"
    use_thinking: bool = True
    use_search_grounding: bool = False


class ShinGanAgent:
    """Nano Banana Pro 画像生成エージェント。"""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()

        self._chat: genai.chats.Chat | None = None
        self._history: list[dict] = []

    def _build_config(
        self,
        prompt_obj: Prompt | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        use_thinking: bool | None = None,
        use_search_grounding: bool | None = None,
    ) -> types.GenerateContentConfig:
        """生成設定を構築する。"""
        ar = aspect_ratio or (prompt_obj.aspect_ratio if prompt_obj else self.config.default_aspect_ratio)
        res = resolution or (prompt_obj.resolution if prompt_obj else self.config.default_resolution)
        thinking = use_thinking if use_thinking is not None else (
            prompt_obj.use_thinking if prompt_obj else self.config.use_thinking
        )
        grounding = use_search_grounding if use_search_grounding is not None else (
            prompt_obj.use_search_grounding if prompt_obj else self.config.use_search_grounding
        )

        tools = []
        if grounding:
            tools.append({"google_search": {}})

        return types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=ar,
                image_size=res,
            ),
            tools=tools if tools else None,
        )

    def _save_image(self, part, prefix: str = "shingan") -> Path:
        """画像パートをファイルに保存する。"""
        timestamp = int(time.time() * 1000)
        filename = f"{prefix}_{timestamp}.png"
        filepath = self.config.output_dir / filename
        image = part.as_image()
        image.save(str(filepath))
        return filepath

    def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        use_thinking: bool | None = None,
        use_search_grounding: bool | None = None,
        save_prefix: str = "shingan",
    ) -> GenerationResult:
        """テキストプロンプトから画像を生成する。"""
        config = self._build_config(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            use_thinking=use_thinking,
            use_search_grounding=use_search_grounding,
        )

        start = time.monotonic()
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=[prompt],
            config=config,
        )
        elapsed = time.monotonic() - start

        result = GenerationResult(
            elapsed_sec=elapsed,
            model=self.config.model,
            prompt_used=prompt,
        )

        for part in response.parts:
            if part.text is not None:
                result.text = part.text
            elif part.inline_data is not None:
                result.image_path = self._save_image(part, prefix=save_prefix)

        self._history.append({
            "role": "user",
            "prompt": prompt,
            "result": result,
        })

        return result

    def generate_from_catalog(
        self,
        prompt_id: str,
        *,
        override_prompt: str | None = None,
    ) -> GenerationResult:
        """カタログのプロンプトIDを指定して画像を生成する。"""
        prompt_obj = get_prompt_by_id(prompt_id)
        if prompt_obj is None:
            raise ValueError(f"プロンプトID '{prompt_id}' が見つかりません")

        text = override_prompt or prompt_obj.prompt
        config = self._build_config(prompt_obj=prompt_obj)

        start = time.monotonic()
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=[text],
            config=config,
        )
        elapsed = time.monotonic() - start

        result = GenerationResult(
            elapsed_sec=elapsed,
            model=self.config.model,
            prompt_used=text,
        )

        for part in response.parts:
            if part.text is not None:
                result.text = part.text
            elif part.inline_data is not None:
                result.image_path = self._save_image(part, prefix=prompt_obj.id)

        return result

    def start_chat(self) -> None:
        """マルチターンチャットセッションを開始する。"""
        config = self._build_config()
        self._chat = self.client.chats.create(
            model=self.config.model,
            config=config,
        )

    def chat(self, message: str, save_prefix: str = "chat") -> GenerationResult:
        """チャットセッションでメッセージを送信し、画像を生成/編集する。"""
        if self._chat is None:
            self.start_chat()

        start = time.monotonic()
        response = self._chat.send_message(message)
        elapsed = time.monotonic() - start

        result = GenerationResult(
            elapsed_sec=elapsed,
            model=self.config.model,
            prompt_used=message,
        )

        for part in response.parts:
            if part.text is not None:
                result.text = part.text
            elif part.inline_data is not None:
                result.image_path = self._save_image(part, prefix=save_prefix)

        return result

    def edit_image(
        self,
        image_path: str | Path,
        edit_prompt: str,
        *,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
    ) -> GenerationResult:
        """既存画像を編集プロンプトで修正する。"""
        from PIL import Image

        img = Image.open(str(image_path))
        config = self._build_config(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )

        start = time.monotonic()
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=[edit_prompt, img],
            config=config,
        )
        elapsed = time.monotonic() - start

        result = GenerationResult(
            elapsed_sec=elapsed,
            model=self.config.model,
            prompt_used=edit_prompt,
        )

        for part in response.parts:
            if part.text is not None:
                result.text = part.text
            elif part.inline_data is not None:
                result.image_path = self._save_image(part, prefix="edit")

        return result

    @property
    def history(self) -> list[dict]:
        """生成履歴を返す。"""
        return list(self._history)
