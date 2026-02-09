"""Agent のテスト（スタブ版）。"""

import json

from shingan.agent import AgentConfig, ShinGanAgent


def test_generate_returns_pending(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    result = agent.generate("a cute cat")
    assert result.status == "pending"
    assert result.id
    assert result.prompt_used == "a cute cat"
    assert result.image_path is None  # スタブなので画像なし


def test_generate_saves_metadata(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    result = agent.generate("test prompt", aspect_ratio="16:9", resolution="4K")
    meta_path = tmp_path / f"{result.id}_meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert meta["prompt"] == "test prompt"
    assert meta["aspect_ratio"] == "16:9"
    assert meta["resolution"] == "4K"


def test_generate_from_catalog(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    result = agent.generate_from_catalog("char-pixel-mascot")
    assert result.status == "pending"
    assert "stub" in result.text.lower()


def test_generate_from_catalog_invalid(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    try:
        agent.generate_from_catalog("nonexistent-id")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_batch_generate(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    results = agent.batch_generate([
        {"prompt": "cat"},
        {"prompt": "dog"},
        {"prompt_id": "char-pixel-mascot"},
    ])
    assert len(results) == 3
    assert all(r.status == "pending" for r in results)


def test_batch_from_category(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    results = agent.batch_from_category("character", count=2)
    assert len(results) == 2


def test_references(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))

    # Add
    paths = agent.add_references("brand", ["/img/a.png", "/img/b.png"])
    assert len(paths) == 2

    # Duplicate
    paths = agent.add_references("brand", ["/img/a.png"])
    assert len(paths) == 2  # no duplicate

    # Get
    refs = agent.get_references("brand")
    assert "brand" in refs
    assert len(refs["brand"]) == 2

    # Get all
    agent.add_references("other", ["/x.png"])
    all_refs = agent.get_references()
    assert len(all_refs) == 2

    # Remove
    agent.remove_reference("brand", "/img/a.png")
    assert len(agent.get_references("brand")["brand"]) == 1

    # Clear group
    agent.clear_references("brand")
    assert len(agent.get_references("brand")["brand"]) == 0

    # Clear all
    agent.clear_references()
    assert agent.get_references() == {}


def test_attach_image(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    result = agent.generate("test")
    # Create dummy image
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"fake")

    updated = agent.attach_image(result.id, str(img_path))
    assert updated is not None
    assert updated.status == "completed"
    assert updated.image_path == img_path


def test_attach_image_invalid_id(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    assert agent.attach_image("nonexistent", "/x.png") is None


def test_session_lifecycle(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))

    assert agent.session_state is None
    sid = agent.start_chat()
    assert agent.session_state == "active"
    assert len(sid) == 12

    result = agent.chat("hello")
    assert result.session_id == sid
    assert result.status == "pending"

    agent.close_chat()
    assert agent.session_state is None


def test_history_and_export(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    agent.generate("a")
    agent.generate("b")
    assert len(agent.history) == 2

    exported = agent.export_history()
    assert len(exported) == 2
    assert exported[0]["prompt"] == "a"
    assert exported[1]["prompt"] == "b"


def test_get_result(tmp_path):
    agent = ShinGanAgent(AgentConfig(output_dir=tmp_path))
    r = agent.generate("find me")
    found = agent.get_result(r.id)
    assert found is not None
    assert found.id == r.id
    assert agent.get_result("no-such-id") is None
