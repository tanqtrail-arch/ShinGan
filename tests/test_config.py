"""設定管理のテスト。"""

import os
from pathlib import Path
from unittest.mock import patch

from shingan.config import Settings


def test_defaults():
    with patch.dict(os.environ, {}, clear=True):
        s = Settings.from_env(dotenv_path=Path("/nonexistent/.env"))
    assert s.default_model == "gemini-3-pro-image-preview"
    assert s.default_resolution == "2K"
    assert s.server_port == 8080
    assert s.max_retries == 4
    assert s.use_thinking is True
    assert s.api_key is None


def test_env_override():
    env = {
        "GOOGLE_API_KEY": "test-key-123",
        "SHINGAN_MODEL": "gemini-2.5-flash-image",
        "SHINGAN_RESOLUTION": "4K",
        "SHINGAN_PORT": "9090",
        "SHINGAN_THINKING": "false",
        "SHINGAN_MAX_RETRIES": "2",
    }
    with patch.dict(os.environ, env, clear=True):
        s = Settings.from_env(dotenv_path=Path("/nonexistent/.env"))
    assert s.api_key == "test-key-123"
    assert s.default_model == "gemini-2.5-flash-image"
    assert s.default_resolution == "4K"
    assert s.server_port == 9090
    assert s.use_thinking is False
    assert s.max_retries == 2


def test_api_key_fallback():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fallback-key"}, clear=True):
        s = Settings.from_env(dotenv_path=Path("/nonexistent/.env"))
    assert s.api_key == "fallback-key"


def test_dotenv_loading(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SHINGAN_RESOLUTION=1K\nSHINGAN_PORT=3000\n")
    with patch.dict(os.environ, {}, clear=True):
        s = Settings.from_env(dotenv_path=env_file)
    assert s.default_resolution == "1K"
    assert s.server_port == 3000
