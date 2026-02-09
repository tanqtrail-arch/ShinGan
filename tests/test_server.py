"""Web API サーバーのテスト。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from shingan.config import Settings


@pytest.fixture
def client():
    """テスト用 FastAPI クライアント。genai.Client をモックする。"""
    mock_genai_client = MagicMock()

    with patch("shingan.agent.genai.Client", return_value=mock_genai_client):
        from shingan.server import create_app

        settings = Settings(
            default_model="test-model",
            output_dir="/tmp/shingan_test_output",
        )
        app = create_app(settings)
        yield TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_get_prompts(client):
    resp = client.get("/api/prompts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    first = data[0]
    assert "id" in first
    assert "category" in first
    assert "prompt" in first


def test_get_prompts_by_category(client):
    resp = client.get("/api/prompts?category=character")
    assert resp.status_code == 200
    data = resp.json()
    assert all(p["category"] == "character" for p in data)


def test_get_prompt_by_id(client):
    resp = client.get("/api/prompts/char-pixel-mascot")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "char-pixel-mascot"
    assert data["name_ja"] == "ピクセルアートマスコット"


def test_get_prompt_not_found(client):
    resp = client.get("/api/prompts/nonexistent")
    assert resp.status_code == 404


def test_get_categories(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "id" in data[0]
    assert "label" in data[0]
    assert "count" in data[0]


def test_session_state_no_session(client):
    resp = client.get("/api/session/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "none"
