"""
対話型プロンプトビルダー

構造化されたステップでプロンプトを組み立てる。
Nano Banana Pro 推奨フォーマット:
  [Subject + Adjectives] doing [Action] in [Location/Context].
  [Composition/Camera]. [Lighting]. [Style/Media]. [Constraint/Text].
"""

from __future__ import annotations

from dataclasses import dataclass, field


# =========================================================================
# プリセット選択肢
# =========================================================================

STYLES: dict[str, str] = {
    "anime": "modern anime illustration, cel-shading",
    "pixel": "retro pixel art, 16-bit game sprite, clean pixel edges",
    "photorealistic": "photorealistic, DSLR photography",
    "cinematic": "cinematic, digital matte painting, film grain",
    "watercolor": "traditional watercolor painting, soft edges, paper texture",
    "vector": "flat vector illustration, clean lines, minimal",
    "3d_render": "3D render, Octane, subsurface scattering, global illumination",
    "sketch": "pencil sketch, cross-hatching, rough lines",
    "ukiyoe": "traditional Japanese ukiyo-e woodblock print style",
    "concept_art": "professional concept art, game industry quality",
}

COMPOSITIONS: dict[str, str] = {
    "closeup": "extreme close-up, macro detail",
    "portrait": "upper body portrait, slight upward angle",
    "full_body": "full body shot, centered",
    "wide": "wide establishing shot, environmental",
    "overhead": "top-down overhead view, flat lay",
    "isometric": "isometric projection, no vanishing point",
    "3/4": "3/4 view, dynamic angle",
    "side": "side profile view",
    "dutch": "Dutch angle, tilted frame, dramatic",
}

LIGHTINGS: dict[str, str] = {
    "golden_hour": "warm golden hour sunlight, long shadows",
    "blue_hour": "cool blue hour twilight, soft ambient",
    "studio": "professional studio lighting, three-point setup",
    "neon": "neon lighting, cyan and magenta, cyberpunk glow",
    "dramatic": "dramatic chiaroscuro, deep shadows, single key light",
    "flat": "flat even lighting, no harsh shadows",
    "backlit": "strong backlight, rim lighting, silhouette edges",
    "overcast": "soft overcast diffused light, no harsh shadows",
    "moonlight": "cool moonlight, blue tint, nighttime ambiance",
}

ASPECT_RATIOS: dict[str, str] = {
    "1:1": "正方形 (アイコン、プロフィール)",
    "4:3": "横長スタンダード (Web素材)",
    "3:4": "縦長スタンダード (ポートレート)",
    "16:9": "ワイドスクリーン (背景、バナー)",
    "9:16": "縦長ワイド (モバイル、ストーリー)",
    "5:4": "やや横長 (グループ写真)",
}

RESOLUTIONS: dict[str, str] = {
    "1K": "ドラフト / ピクセルアート向き",
    "2K": "スタンダード（デフォルト推奨）",
    "4K": "最高品質（プロダクション向き）",
}


# =========================================================================
# ビルダー
# =========================================================================

@dataclass
class PromptDraft:
    """ビルダーが組み立てるプロンプトのドラフト。"""

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

    def compile(self) -> str:
        """プロンプトドラフトを最終プロンプト文字列にコンパイルする。"""
        parts = []
        if self.subject:
            parts.append(self.subject)
        if self.action:
            parts.append(self.action)
        if self.location:
            parts.append(f"in {self.location}")
        if parts:
            sentence = " ".join(parts) + "."
        else:
            sentence = ""

        extras = []
        if self.composition:
            extras.append(self.composition)
        if self.lighting:
            extras.append(self.lighting)
        if self.style:
            extras.append(f"Style: {self.style}")
        if self.constraint:
            extras.append(self.constraint)

        full = sentence
        if extras:
            full = full + " " + ". ".join(extras) + "."

        return full.strip()

    def to_dict(self) -> dict:
        """APIリクエスト用の辞書に変換する。"""
        return {
            "prompt": self.compile(),
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "use_thinking": self.use_thinking,
            "use_search_grounding": self.use_search_grounding,
            "subject": self.subject,
            "action": self.action,
            "location": self.location,
            "composition": self.composition,
            "lighting": self.lighting,
            "style": self.style,
            "constraint": self.constraint,
            "negative": self.negative,
            "reference_group": self.reference_group,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PromptDraft:
        """辞書からドラフトを復元する。"""
        return cls(
            subject=data.get("subject", ""),
            action=data.get("action", ""),
            location=data.get("location", ""),
            composition=data.get("composition", ""),
            lighting=data.get("lighting", ""),
            style=data.get("style", ""),
            constraint=data.get("constraint", ""),
            negative=data.get("negative", ""),
            aspect_ratio=data.get("aspect_ratio", "1:1"),
            resolution=data.get("resolution", "2K"),
            use_thinking=data.get("use_thinking", False),
            use_search_grounding=data.get("use_search_grounding", False),
            reference_group=data.get("reference_group"),
        )


def get_presets() -> dict:
    """全プリセット選択肢を返す（API/UI用）。"""
    return {
        "styles": STYLES,
        "compositions": COMPOSITIONS,
        "lightings": LIGHTINGS,
        "aspect_ratios": ASPECT_RATIOS,
        "resolutions": RESOLUTIONS,
    }
