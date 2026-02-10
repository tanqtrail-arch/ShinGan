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


# === 真贋クイズ ===

def _create_test_quiz(client):
    """テスト用クイズを作成するヘルパー。"""
    import io
    real_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    resp = client.post(
        "/api/quiz",
        data={"title": "テスト作品", "explanation": "本物は色が鮮やか"},
        files=[
            ("real_image", ("real.png", real_img, "image/png")),
            ("fake_image", ("fake.png", fake_img, "image/png")),
        ],
    )
    return resp


def test_quiz_create(client):
    resp = _create_test_quiz(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "テスト作品"
    assert data["ready"] is True
    assert data["explanation"] == "本物は色が鮮やか"


def test_quiz_list(client):
    _create_test_quiz(client)
    resp = client.get("/api/quiz")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["title"] == "テスト作品"


def test_quiz_get(client):
    create_resp = _create_test_quiz(client)
    quiz_id = create_resp.json()["id"]
    resp = client.get(f"/api/quiz/{quiz_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == quiz_id


def test_quiz_get_not_found(client):
    assert client.get("/api/quiz/nonexistent").status_code == 404


def test_quiz_play(client):
    create_resp = _create_test_quiz(client)
    quiz_id = create_resp.json()["id"]
    resp = client.get(f"/api/quiz/{quiz_id}/play")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == quiz_id
    assert data["answer"] in ("left", "right")
    assert data["left_image_url"]
    assert data["right_image_url"]


def test_quiz_answer_correct(client):
    create_resp = _create_test_quiz(client)
    quiz_id = create_resp.json()["id"]
    play_resp = client.get(f"/api/quiz/{quiz_id}/play")
    correct_side = play_resp.json()["answer"]
    resp = client.post(
        f"/api/quiz/{quiz_id}/answer",
        json={"choice": correct_side, "correct_side": correct_side},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is True
    assert data["explanation"] == ""


def test_quiz_answer_incorrect(client):
    create_resp = _create_test_quiz(client)
    quiz_id = create_resp.json()["id"]
    play_resp = client.get(f"/api/quiz/{quiz_id}/play")
    correct_side = play_resp.json()["answer"]
    wrong_side = "right" if correct_side == "left" else "left"
    resp = client.post(
        f"/api/quiz/{quiz_id}/answer",
        json={"choice": wrong_side, "correct_side": correct_side},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["explanation"] == "本物は色が鮮やか"


def test_quiz_delete(client):
    create_resp = _create_test_quiz(client)
    quiz_id = create_resp.json()["id"]
    resp = client.delete(f"/api/quiz/{quiz_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    # 削除後は404
    assert client.get(f"/api/quiz/{quiz_id}").status_code == 404


def test_quiz_delete_not_found(client):
    assert client.delete("/api/quiz/nonexistent").status_code == 404
