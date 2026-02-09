"""
Nano Banana Pro (Gemini 3 Pro Image) プロンプトカタログ

カテゴリ別に整理された画像生成プロンプト一覧。
各プロンプトは Nano Banana Pro の特性（4K出力、テキスト描画、物理リアリズム、
Thinking モード）を最大限に活用するよう設計されています。
"""

from dataclasses import dataclass


@dataclass
class Prompt:
    id: str
    category: str
    name: str
    name_ja: str
    prompt: str
    description_ja: str
    aspect_ratio: str = "1:1"
    resolution: str = "2K"
    use_thinking: bool = False
    use_search_grounding: bool = False


PROMPT_CATALOG: list[Prompt] = [
    # =========================================================================
    # 1. キャラクターデザイン
    # =========================================================================
    Prompt(
        id="char-pixel-mascot",
        category="character",
        name="Pixel Art Mascot",
        name_ja="ピクセルアートマスコット",
        prompt=(
            "A cute pixel art mascot character, 32x32 sprite style. "
            "The character is a small round creature with expressive dot eyes "
            "and tiny legs. Warm brown and orange color palette. "
            "Clean pixel edges, no anti-aliasing. White background. "
            "Style: retro 16-bit game sprite."
        ),
        description_ja="レトロゲーム風の可愛いピクセルアートマスコット",
        aspect_ratio="1:1",
        resolution="1K",
    ),
    Prompt(
        id="char-anime-portrait",
        category="character",
        name="Anime Character Portrait",
        name_ja="アニメキャラポートレート",
        prompt=(
            "A detailed anime-style character portrait. Young adventurer with "
            "wind-blown hair, determined expression, wearing a cloak with "
            "glowing rune symbols. Soft cel-shading with vibrant highlights. "
            "Upper body composition, slight upward camera angle. "
            "Warm sunset lighting from the left. Style: modern anime illustration."
        ),
        description_ja="アニメ風キャラクターの上半身ポートレート",
        aspect_ratio="3:4",
        resolution="2K",
    ),
    Prompt(
        id="char-chibi-emote",
        category="character",
        name="Chibi Emote Set",
        name_ja="ちびキャラエモートセット",
        prompt=(
            "A sheet of 9 chibi character emotes arranged in a 3x3 grid. "
            "Same character in each cell showing different emotions: happy, sad, "
            "angry, surprised, sleepy, laughing, confused, love-struck, determined. "
            "Simple round head, large expressive eyes. Flat color style, "
            "white background, clean line art. Each cell clearly separated."
        ),
        description_ja="9種類の表情を持つちびキャラエモートシート",
        aspect_ratio="1:1",
        resolution="2K",
    ),
    Prompt(
        id="char-rpg-class",
        category="character",
        name="RPG Character Class",
        name_ja="RPGキャラクタークラス",
        prompt=(
            "Full-body character design sheet for an RPG mage class. "
            "Front view and side view on the same canvas. Elaborate staff "
            "with crystal orb, flowing robes with arcane patterns. "
            "Color callouts and design annotations around the character. "
            "Style: professional game concept art. White background."
        ),
        description_ja="RPGメイジクラスのキャラクターデザインシート",
        aspect_ratio="16:9",
        resolution="2K",
    ),

    # =========================================================================
    # 2. 背景・環境アート
    # =========================================================================
    Prompt(
        id="bg-fantasy-landscape",
        category="background",
        name="Fantasy Landscape",
        name_ja="ファンタジー風景",
        prompt=(
            "A breathtaking fantasy landscape. Floating islands with waterfalls "
            "cascading into clouds below. Ancient stone bridges connecting the "
            "islands. Lush vegetation and glowing crystal formations. "
            "Golden hour lighting with volumetric god rays. "
            "Wide establishing shot, high detail. "
            "Style: digital matte painting, cinematic."
        ),
        description_ja="浮遊島とクリスタルのファンタジー風景",
        aspect_ratio="16:9",
        resolution="4K",
        use_thinking=True,
    ),
    Prompt(
        id="bg-cyberpunk-alley",
        category="background",
        name="Cyberpunk Alley",
        name_ja="サイバーパンク路地裏",
        prompt=(
            "A narrow cyberpunk alley at night in a rain-soaked Asian metropolis. "
            "Dense neon signage in Japanese and Chinese characters. "
            "Holographic advertisements floating above. Steam rising from vents. "
            "Wet reflections on the ground mirroring all the neon lights. "
            "Deep perspective vanishing point. Moody blue and magenta lighting. "
            "Style: photorealistic, Blade Runner aesthetic."
        ),
        description_ja="ネオン輝くサイバーパンクの路地裏（雨の夜景）",
        aspect_ratio="9:16",
        resolution="4K",
        use_thinking=True,
    ),
    Prompt(
        id="bg-pixel-dungeon",
        category="background",
        name="Pixel Art Dungeon",
        name_ja="ピクセルアートダンジョン",
        prompt=(
            "A top-down pixel art dungeon tilemap. Stone floors, torch-lit corridors, "
            "treasure chests, spike traps, and a boss room with a large skull door. "
            "16-bit retro game style with a limited color palette of 32 colors. "
            "Each tile is clearly defined at 16x16 pixels. "
            "Overhead view, no perspective distortion."
        ),
        description_ja="16bit風トップダウンダンジョンタイルマップ",
        aspect_ratio="1:1",
        resolution="1K",
    ),
    Prompt(
        id="bg-isometric-room",
        category="background",
        name="Isometric Room",
        name_ja="アイソメトリック部屋",
        prompt=(
            "An isometric cozy bedroom interior. Warm wood flooring, "
            "a bed with rumpled sheets, desk with a glowing laptop, "
            "bookshelf overflowing with books, potted plants on the windowsill. "
            "Soft warm afternoon light streaming through the window. "
            "Perfectly isometric projection, no vanishing point. "
            "Style: detailed illustration with soft textures."
        ),
        description_ja="温かみのあるアイソメトリック寝室",
        aspect_ratio="1:1",
        resolution="2K",
    ),

    # =========================================================================
    # 3. UI/UXデザイン素材
    # =========================================================================
    Prompt(
        id="ui-app-icons",
        category="ui",
        name="App Icon Set",
        name_ja="アプリアイコンセット",
        prompt=(
            "A set of 12 mobile app icons arranged in a 4x3 grid. "
            "Categories: camera, messaging, music, weather, maps, settings, "
            "calendar, notes, fitness, shopping, food, travel. "
            "Consistent rounded-square shape, colorful gradient backgrounds, "
            "clean white symbolic icons. Modern iOS/Android style. "
            "Each icon clearly separated on a light gray background."
        ),
        description_ja="12種のモダンなモバイルアプリアイコンセット",
        aspect_ratio="4:3",
        resolution="2K",
    ),
    Prompt(
        id="ui-game-hud",
        category="ui",
        name="Game HUD Elements",
        name_ja="ゲームHUD素材",
        prompt=(
            "A fantasy RPG game HUD element sheet on a transparent-style dark background. "
            "Include: health bar (red gradient), mana bar (blue gradient), "
            "experience bar (gold), minimap frame (ornate gold border), "
            "inventory slot (stone texture), dialog box (parchment style), "
            "and 4 action buttons with sword/shield/potion/magic icons. "
            "Style: hand-painted fantasy game UI."
        ),
        description_ja="ファンタジーRPGゲーム用HUD素材シート",
        aspect_ratio="16:9",
        resolution="2K",
    ),

    # =========================================================================
    # 4. プロダクト・マーケティング
    # =========================================================================
    Prompt(
        id="prod-sneaker-shot",
        category="product",
        name="Product Sneaker Shot",
        name_ja="スニーカー商品写真",
        prompt=(
            "A premium product photograph of a futuristic sneaker. "
            "The shoe is floating at a dynamic 3/4 angle above a reflective "
            "dark surface. Dramatic rim lighting from behind in cyan and magenta. "
            "Particle effects and light streaks around the shoe. "
            "Sharp focus on the shoe, shallow depth of field background. "
            "Style: high-end commercial photography, 4K studio quality."
        ),
        description_ja="フューチャリスティックなスニーカーの商品写真",
        aspect_ratio="4:3",
        resolution="4K",
    ),
    Prompt(
        id="prod-food-flat",
        category="product",
        name="Food Flat Lay",
        name_ja="フード俯瞰写真",
        prompt=(
            "A beautiful overhead flat lay food photograph. A Japanese bento box "
            "in the center with perfectly arranged sushi, tamagoyaki, edamame, "
            "and pickled vegetables. Chopsticks, a small soy sauce dish, "
            "and green tea cup arranged around it. "
            "Natural soft daylight from above, slight shadows. "
            "Clean white marble surface. Style: food magazine editorial photography."
        ),
        description_ja="日本の弁当フラットレイ写真（俯瞰撮影）",
        aspect_ratio="1:1",
        resolution="4K",
    ),

    # =========================================================================
    # 5. インフォグラフィック・テキスト入り
    # =========================================================================
    Prompt(
        id="info-tech-diagram",
        category="infographic",
        name="Tech Architecture Diagram",
        name_ja="技術アーキテクチャ図",
        prompt=(
            "A clean technical architecture diagram showing a microservices system. "
            "Include labeled boxes for: 'API Gateway', 'Auth Service', 'User Service', "
            "'Payment Service', 'Database', 'Message Queue', 'Cache Layer'. "
            "Connect them with directional arrows showing data flow. "
            "Use a modern flat design with a dark navy background, "
            "white text labels, and color-coded service categories "
            "(blue for core, green for data, orange for infrastructure). "
            "Title at top: 'System Architecture Overview'."
        ),
        description_ja="マイクロサービスシステムアーキテクチャ図",
        aspect_ratio="16:9",
        resolution="4K",
        use_thinking=True,
    ),
    Prompt(
        id="info-recipe-card",
        category="infographic",
        name="Recipe Card",
        name_ja="レシピカード",
        prompt=(
            "A visually appealing recipe card infographic for 'Matcha Latte'. "
            "Include: a beautiful illustration of the drink at the top, "
            "ingredient list on the left (matcha powder, milk, honey, hot water), "
            "step-by-step instructions numbered 1-4 on the right with small icons. "
            "Calorie count and prep time at the bottom. "
            "Soft green and cream color palette. "
            "Title 'MATCHA LATTE' in elegant typography at the top. "
            "Style: modern minimalist infographic."
        ),
        description_ja="抹茶ラテのビジュアルレシピカード",
        aspect_ratio="3:4",
        resolution="2K",
        use_thinking=True,
    ),

    # =========================================================================
    # 6. ロゴ・タイポグラフィ
    # =========================================================================
    Prompt(
        id="logo-minimalist",
        category="logo",
        name="Minimalist Logo Set",
        name_ja="ミニマリストロゴセット",
        prompt=(
            "8 minimalist logo concepts arranged in a 4x2 grid on white background. "
            "Each logo is a single expressive word where the letters visually convey "
            "the word's meaning: 'FIRE' (letters made of flames), "
            "'WAVE' (letters shaped like ocean waves), "
            "'GROW' (letters sprouting leaves), "
            "'FAST' (letters with motion blur streaks), "
            "'BREAK' (letters cracking apart), "
            "'FLOAT' (letters drifting upward with bubbles), "
            "'HEAVY' (letters sinking/compressed), "
            "'SHARP' (letters with pointed angular edges). "
            "Flat vector style, black on white."
        ),
        description_ja="意味を視覚的に表現する8つのミニマリストロゴ",
        aspect_ratio="16:9",
        resolution="2K",
        use_thinking=True,
    ),
    Prompt(
        id="logo-japanese-brand",
        category="logo",
        name="Japanese Brand Logo",
        name_ja="和風ブランドロゴ",
        prompt=(
            "A sophisticated Japanese brand logo for a tea company called '真茶 SHINCHA'. "
            "The logo combines a minimal brushstroke tea leaf symbol with "
            "the Japanese characters '真茶' and the romanized 'SHINCHA' below. "
            "Zen-inspired negative space design. "
            "Color: deep matcha green on white background. "
            "Style: premium brand identity, clean vector."
        ),
        description_ja="日本の茶ブランド「真茶」のロゴデザイン",
        aspect_ratio="1:1",
        resolution="2K",
    ),

    # =========================================================================
    # 7. サーチグラウンディング（リアルタイムデータ連携）
    # =========================================================================
    Prompt(
        id="search-weather-chart",
        category="search_grounded",
        name="Live Weather Visualization",
        name_ja="リアルタイム天気ビジュアル",
        prompt=(
            "Visualize the current weather forecast for the next 5 days in Tokyo "
            "as a clean, modern weather chart. Show temperature highs and lows, "
            "weather icons for each day, and precipitation probability. "
            "Add a visual suggestion of what to wear each day. "
            "Style: modern mobile app weather widget, dark theme."
        ),
        description_ja="東京の5日間天気予報ビジュアライゼーション",
        aspect_ratio="9:16",
        resolution="2K",
        use_search_grounding=True,
    ),
    Prompt(
        id="search-trending-topic",
        category="search_grounded",
        name="Trending Topic Infographic",
        name_ja="トレンドトピックインフォグラフィック",
        prompt=(
            "Create an informative infographic about the latest AI technology trends "
            "in 2026. Research current developments and visualize the top 5 trends "
            "with icons, brief descriptions, and adoption statistics. "
            "Modern flat design, gradient blue-purple color scheme. "
            "Title: 'AI Trends 2026' in bold typography."
        ),
        description_ja="2026年AIトレンドのインフォグラフィック",
        aspect_ratio="9:16",
        resolution="2K",
        use_search_grounding=True,
        use_thinking=True,
    ),

    # =========================================================================
    # 8. フォトリアリスティック
    # =========================================================================
    Prompt(
        id="photo-portrait-studio",
        category="photorealistic",
        name="Studio Portrait",
        name_ja="スタジオポートレート",
        prompt=(
            "A professional studio portrait photograph. Subject facing 3/4 to camera "
            "with a subtle smile. Rembrandt lighting setup: key light at 45 degrees "
            "creating a triangle of light on the shadow side of the face. "
            "Dark charcoal gray backdrop, shallow depth of field. "
            "Catch light visible in the eyes. "
            "Style: editorial portrait photography, 85mm f/1.4 lens look."
        ),
        description_ja="レンブラントライティングのスタジオポートレート",
        aspect_ratio="3:4",
        resolution="4K",
    ),
    Prompt(
        id="photo-macro-nature",
        category="photorealistic",
        name="Macro Nature",
        name_ja="マクロ自然写真",
        prompt=(
            "An extreme macro photograph of a dewdrop on a spider web strand at dawn. "
            "The dewdrop acts as a lens, refracting the blurred garden behind it. "
            "Precise focus on the water droplet with everything else in soft bokeh. "
            "Warm golden backlight from the rising sun creating rainbow light dispersion. "
            "Style: National Geographic macro photography."
        ),
        description_ja="朝露のマクロ写真（蜘蛛の巣の水滴）",
        aspect_ratio="1:1",
        resolution="4K",
        use_thinking=True,
    ),

    # =========================================================================
    # 9. アブストラクト・アート
    # =========================================================================
    Prompt(
        id="art-surreal-composition",
        category="abstract",
        name="Surreal Composition",
        name_ja="シュルレアリスム構図",
        prompt=(
            "A crystalline chess set where the pieces are made of freezing water "
            "and the board is made of burning lava. The pieces are melting slightly "
            "where they touch the board. Steam rising at the contact points. "
            "Macro photography perspective, hyper-realistic detail. "
            "Reason through the lighting interactions between fire and ice "
            "before generating. Style: surrealist photography."
        ),
        description_ja="氷のチェス駒と溶岩のチェスボード",
        aspect_ratio="1:1",
        resolution="4K",
        use_thinking=True,
    ),
    Prompt(
        id="art-generative-pattern",
        category="abstract",
        name="Generative Pattern",
        name_ja="ジェネラティブパターン",
        prompt=(
            "A mesmerizing generative art pattern inspired by Japanese wave motifs. "
            "Thousands of flowing lines creating a turbulent ocean surface. "
            "Lines transition from deep indigo at the edges to white foam at peaks. "
            "Mathematical precision in the wave interference patterns. "
            "Style: computational art meets traditional ukiyo-e. Black background."
        ),
        description_ja="浮世絵風ジェネラティブ波パターン",
        aspect_ratio="16:9",
        resolution="4K",
    ),

    # =========================================================================
    # 10. テクスチャ・素材
    # =========================================================================
    Prompt(
        id="tex-seamless-set",
        category="texture",
        name="Seamless Texture Set",
        name_ja="シームレステクスチャセット",
        prompt=(
            "A 2x3 grid of seamless tileable textures for game development. "
            "Include: weathered stone bricks, dark wood planks, mossy ground, "
            "rusted metal plate, woven fabric, and cracked dry earth. "
            "Each texture is photorealistic and designed to tile seamlessly. "
            "Consistent lighting from top-left across all textures. "
            "Labels below each: 'Stone', 'Wood', 'Moss', 'Metal', 'Fabric', 'Earth'."
        ),
        description_ja="ゲーム開発用6種シームレステクスチャセット",
        aspect_ratio="3:4",
        resolution="4K",
        use_thinking=True,
    ),
]


def list_categories() -> list[str]:
    """全カテゴリの一覧を返す。"""
    seen = []
    for p in PROMPT_CATALOG:
        if p.category not in seen:
            seen.append(p.category)
    return seen


def get_prompts_by_category(category: str) -> list[Prompt]:
    """指定カテゴリのプロンプト一覧を返す。"""
    return [p for p in PROMPT_CATALOG if p.category == category]


def get_prompt_by_id(prompt_id: str) -> Prompt | None:
    """IDでプロンプトを取得する。"""
    for p in PROMPT_CATALOG:
        if p.id == prompt_id:
            return p
    return None


CATEGORY_LABELS: dict[str, str] = {
    "character": "キャラクターデザイン",
    "background": "背景・環境アート",
    "ui": "UI/UXデザイン素材",
    "product": "プロダクト・マーケティング",
    "infographic": "インフォグラフィック",
    "logo": "ロゴ・タイポグラフィ",
    "search_grounded": "サーチグラウンディング",
    "photorealistic": "フォトリアリスティック",
    "abstract": "アブストラクト・アート",
    "texture": "テクスチャ・素材",
}
