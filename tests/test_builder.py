"""プロンプトビルダーのテスト。"""

from shingan.builder import PromptDraft, get_presets


def test_compile_full():
    d = PromptDraft(
        subject="A fierce dragon",
        action="breathing fire",
        location="a volcanic mountain",
        composition="wide establishing shot",
        lighting="dramatic chiaroscuro",
        style="digital matte painting",
        constraint="No text overlay",
    )
    result = d.compile()
    assert "A fierce dragon" in result
    assert "breathing fire" in result
    assert "in a volcanic mountain" in result
    assert "Style: digital matte painting" in result
    assert "No text overlay" in result


def test_compile_minimal():
    d = PromptDraft(subject="A cat")
    result = d.compile()
    assert result == "A cat."


def test_compile_empty():
    d = PromptDraft()
    assert d.compile() == ""


def test_to_dict_and_from_dict():
    d = PromptDraft(
        subject="Robot",
        style="anime",
        aspect_ratio="16:9",
        resolution="4K",
    )
    data = d.to_dict()
    assert data["subject"] == "Robot"
    assert data["aspect_ratio"] == "16:9"

    restored = PromptDraft.from_dict(data)
    assert restored.subject == "Robot"
    assert restored.compile() == d.compile()


def test_get_presets():
    presets = get_presets()
    assert "styles" in presets
    assert "compositions" in presets
    assert "lightings" in presets
    assert "aspect_ratios" in presets
    assert "resolutions" in presets
    assert len(presets["styles"]) > 0
