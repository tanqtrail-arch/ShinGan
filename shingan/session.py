"""
セッション管理 - リトライ・エラーハンドリング付き

スクリーンショットの「セッションの作成に失敗しました」エラーに対応。
指数バックオフリトライ、セッション状態管理、自動復旧を実装。
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SessionState(Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    ACTIVE = "active"
    ERROR = "error"
    CLOSED = "closed"


class SessionError(Exception):
    """セッション関連エラー。"""

    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass
class RetryConfig:
    """リトライ設定。"""

    max_retries: int = 4
    base_delay_sec: float = 2.0
    max_delay_sec: float = 30.0
    backoff_factor: float = 2.0


@dataclass
class SessionInfo:
    """セッション情報。"""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: SessionState = SessionState.IDLE
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    message_count: int = 0
    retry_count: int = 0
    error_message: str | None = None


class SessionManager:
    """セッションのライフサイクル管理。リトライと自動復旧を提供。"""

    def __init__(
        self,
        client: object,
        model: str,
        config: object,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._gen_config = config
        self._retry = retry_config or RetryConfig()
        self._chat: object | None = None
        self._session = SessionInfo()

    @property
    def session(self) -> SessionInfo:
        return self._session

    @property
    def is_active(self) -> bool:
        return self._session.state == SessionState.ACTIVE

    def _wait_backoff(self, attempt: int) -> float:
        """指数バックオフの待機時間を計算して待機する。"""
        delay = min(
            self._retry.base_delay_sec * (self._retry.backoff_factor ** attempt),
            self._retry.max_delay_sec,
        )
        logger.info(f"リトライ {attempt + 1}/{self._retry.max_retries} - {delay:.1f}秒後に再試行")
        time.sleep(delay)
        return delay

    def create_session(self) -> SessionInfo:
        """チャットセッションを作成する。失敗時はリトライ。"""
        self._session.state = SessionState.CONNECTING
        self._session.error_message = None

        last_error: Exception | None = None

        for attempt in range(self._retry.max_retries + 1):
            try:
                self._chat = self._client.chats.create(
                    model=self._model,
                    config=self._gen_config,
                )
                self._session.state = SessionState.ACTIVE
                self._session.retry_count = attempt
                self._session.last_active = time.time()
                logger.info(
                    f"セッション作成成功: {self._session.session_id} "
                    f"(試行: {attempt + 1}回)"
                )
                return self._session

            except Exception as e:
                last_error = e
                logger.warning(f"セッション作成失敗 (試行 {attempt + 1}): {e}")

                if attempt < self._retry.max_retries:
                    self._wait_backoff(attempt)
                else:
                    break

        self._session.state = SessionState.ERROR
        self._session.error_message = str(last_error)
        raise SessionError(
            f"セッションの作成に失敗しました ({self._retry.max_retries + 1}回試行): {last_error}",
            retryable=False,
        )

    def send_message(self, message: str) -> object:
        """メッセージを送信する。セッション切断時は自動復旧。"""
        if self._session.state == SessionState.CLOSED:
            raise SessionError("セッションは閉じられています", retryable=False)

        if self._chat is None or self._session.state != SessionState.ACTIVE:
            self.create_session()

        last_error: Exception | None = None

        for attempt in range(self._retry.max_retries + 1):
            try:
                response = self._chat.send_message(message)
                self._session.message_count += 1
                self._session.last_active = time.time()
                return response

            except Exception as e:
                last_error = e
                logger.warning(f"メッセージ送信失敗 (試行 {attempt + 1}): {e}")

                if attempt < self._retry.max_retries:
                    self._wait_backoff(attempt)
                    # セッション再作成を試みる
                    try:
                        self._session = SessionInfo(
                            session_id=self._session.session_id,
                        )
                        self.create_session()
                    except SessionError:
                        pass
                else:
                    break

        self._session.state = SessionState.ERROR
        self._session.error_message = str(last_error)
        raise SessionError(f"メッセージ送信に失敗しました: {last_error}")

    def close(self) -> None:
        """セッションを閉じる。"""
        self._chat = None
        self._session.state = SessionState.CLOSED
        logger.info(f"セッション終了: {self._session.session_id}")

    def reset(self) -> SessionInfo:
        """セッションをリセットして新しいセッションを作成する。"""
        self.close()
        self._session = SessionInfo()
        return self.create_session()
