"""
設定管理 - 環境変数 / .env ファイルからの設定読み込み
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path | None = None) -> None:
    """シンプルな .env ファイル読み込み（外部依存なし）。"""
    env_path = path or Path(".env")
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


@dataclass
class Settings:
    """アプリケーション全体の設定。"""

    # API
    google_api_key: str = ""
    gemini_api_key: str = ""

    # モデル
    default_model: str = "gemini-3-pro-image-preview"
    fallback_model: str = "gemini-2.5-flash-image"

    # 生成デフォルト
    default_resolution: str = "2K"
    default_aspect_ratio: str = "1:1"
    use_thinking: bool = True

    # サーバー
    server_host: str = "0.0.0.0"
    server_port: int = 8080

    # リトライ
    max_retries: int = 4
    retry_base_delay: float = 2.0

    # 出力
    output_dir: str = "output"

    @classmethod
    def from_env(cls, dotenv_path: Path | None = None) -> Settings:
        """環境変数から設定を読み込む。"""
        _load_dotenv(dotenv_path)

        def _bool(val: str) -> bool:
            return val.lower() in ("1", "true", "yes", "on")

        return cls(
            google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
            gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
            default_model=os.environ.get("SHINGAN_MODEL", "gemini-3-pro-image-preview"),
            fallback_model=os.environ.get("SHINGAN_FALLBACK_MODEL", "gemini-2.5-flash-image"),
            default_resolution=os.environ.get("SHINGAN_RESOLUTION", "2K"),
            default_aspect_ratio=os.environ.get("SHINGAN_ASPECT_RATIO", "1:1"),
            use_thinking=_bool(os.environ.get("SHINGAN_THINKING", "true")),
            server_host=os.environ.get("SHINGAN_HOST", "0.0.0.0"),
            server_port=int(os.environ.get("SHINGAN_PORT", "8080")),
            max_retries=int(os.environ.get("SHINGAN_MAX_RETRIES", "4")),
            retry_base_delay=float(os.environ.get("SHINGAN_RETRY_DELAY", "2.0")),
            output_dir=os.environ.get("SHINGAN_OUTPUT_DIR", "output"),
        )

    @property
    def api_key(self) -> str | None:
        """有効なAPIキーを返す。"""
        return self.google_api_key or self.gemini_api_key or None
