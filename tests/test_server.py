"""Web API サーバーのテスト。"""

import pytest
from fastapi.testclient import TestClient

from shingan.config import Settings
from shingan.server import create_app


@pytest.fixture
def client(tmp_path):
    settings = Settings(default_model="test-model", output_dir=str(tmp_path))
    app = create_app(settings)
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_get_prompts(client):
    resp = client.get("/api/prompts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert "id" in data[0]


def test_get_prompts_by_category(client):
    resp = client.get("/api/prompts?category=character")
    assert resp.status_code == 200
    assert all(p["category"] == "character" for p in resp.json())


def test_get_prompt_by_id(client):
    resp = client.get("/api/prompts/char-pixel-mascot")
    assert resp.status_code == 200
    assert resp.json()["id"] == "char-pixel-mascot"


def test_get_prompt_not_found(client):
    assert client.get("/api/prompts/nonexistent").status_code == 404


def test_get_categories(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_generate(client):
    resp = client.post("/api/generate", json={"prompt": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["id"]


def test_generate_from_catalog(client):
    resp = client.post("/api/generate/char-pixel-mascot", json={})
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


def test_batch(client):
    resp = client.post("/api/batch", json={
        "prompts": [{"prompt": "a"}, {"prompt": "b"}]
    })
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_batch_category(client):
    resp = client.post("/api/batch/category", json={"category": "character", "count": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_references_flow(client):
    # empty
    resp = client.get("/api/references")
    assert resp.status_code == 200
    assert resp.json() == {}

    # add
    resp = client.post("/api/references/brand", json={"paths": ["/a.png"]})
    assert resp.status_code == 200
    assert resp.json()["paths"] == ["/a.png"]

    # get
    resp = client.get("/api/references?group=brand")
    assert "/a.png" in resp.json()["brand"]

    # clear
    resp = client.delete("/api/references/brand")
    assert resp.status_code == 200


def test_builder_presets(client):
    resp = client.get("/api/builder/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert "styles" in data
    assert "compositions" in data


def test_builder_compile(client):
    resp = client.post("/api/builder/compile", json={
        "subject": "A cat",
        "style": "anime"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "A cat" in data["compiled_prompt"]


def test_history_empty(client):
    resp = client.get("/api/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_after_generate(client):
    client.post("/api/generate", json={"prompt": "test"})
    resp = client.get("/api/history")
    assert len(resp.json()) == 1


def test_session_state_none(client):
    resp = client.get("/api/session/state")
    assert resp.status_code == 200
    assert resp.json()["state"] == "none"


def test_session_flow(client):
    # create
    resp = client.post("/api/session")
    assert resp.status_code == 200
    assert resp.json()["state"] == "active"

    # chat
    resp = client.post("/api/session/chat", json={"message": "hello"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    # close
    resp = client.delete("/api/session")
    assert resp.status_code == 200
