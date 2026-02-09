"""テスト共通の fixture とモック設定。"""

import sys
from unittest.mock import MagicMock

# google.genai が暗号系ライブラリに依存するためテスト環境ではモック化
_mock_genai = MagicMock()
sys.modules.setdefault("google.genai", _mock_genai)
sys.modules.setdefault("google.genai.types", _mock_genai.types)

# google モジュールがまだ未ロードならモック
if "google" not in sys.modules:
    _mock_google = MagicMock()
    _mock_google.genai = _mock_genai
    sys.modules["google"] = _mock_google
else:
    sys.modules["google"].genai = _mock_genai
