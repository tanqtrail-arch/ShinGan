"""プロンプトカタログのテスト。"""

from shingan.prompts.catalog import (
    CATEGORY_LABELS,
    PROMPT_CATALOG,
    get_prompt_by_id,
    get_prompts_by_category,
    list_categories,
)


def test_catalog_not_empty():
    assert len(PROMPT_CATALOG) > 0


def test_all_prompts_have_required_fields():
    for p in PROMPT_CATALOG:
        assert p.id, f"プロンプトにIDがありません: {p}"
        assert p.category, f"カテゴリが空: {p.id}"
        assert p.name, f"名前が空: {p.id}"
        assert p.name_ja, f"日本語名が空: {p.id}"
        assert p.prompt, f"プロンプトが空: {p.id}"
        assert p.description_ja, f"説明が空: {p.id}"
        assert p.aspect_ratio, f"アスペクト比が空: {p.id}"
        assert p.resolution in ("1K", "2K", "4K"), f"無効な解像度: {p.resolution} ({p.id})"


def test_unique_ids():
    ids = [p.id for p in PROMPT_CATALOG]
    assert len(ids) == len(set(ids)), "重複IDあり"


def test_list_categories():
    cats = list_categories()
    assert len(cats) > 0
    # 全カテゴリがラベルを持つ
    for cat in cats:
        assert cat in CATEGORY_LABELS, f"カテゴリ '{cat}' にラベルがありません"


def test_get_prompts_by_category():
    for cat in list_categories():
        prompts = get_prompts_by_category(cat)
        assert len(prompts) > 0, f"カテゴリ '{cat}' にプロンプトがありません"
        for p in prompts:
            assert p.category == cat


def test_get_prompts_by_invalid_category():
    prompts = get_prompts_by_category("nonexistent")
    assert prompts == []


def test_get_prompt_by_id():
    for p in PROMPT_CATALOG:
        found = get_prompt_by_id(p.id)
        assert found is not None
        assert found.id == p.id


def test_get_prompt_by_invalid_id():
    assert get_prompt_by_id("nonexistent-id") is None
