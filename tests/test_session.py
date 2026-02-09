"""セッション管理のテスト。"""

from unittest.mock import MagicMock, patch

import pytest

from shingan.session import (
    RetryConfig,
    SessionError,
    SessionInfo,
    SessionManager,
    SessionState,
)


def _make_manager(fail_count: int = 0) -> tuple[SessionManager, MagicMock]:
    """テスト用 SessionManager を作成。fail_count 回失敗後に成功する。"""
    client = MagicMock()
    config = MagicMock()

    call_count = 0

    def mock_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= fail_count:
            raise ConnectionError("接続エラー")
        return MagicMock()

    client.chats.create = mock_create

    mgr = SessionManager(
        client=client,
        model="test-model",
        config=config,
        retry_config=RetryConfig(max_retries=3, base_delay_sec=0.01, max_delay_sec=0.05),
    )
    return mgr, client


def test_create_session_success():
    mgr, _ = _make_manager(fail_count=0)
    info = mgr.create_session()
    assert info.state == SessionState.ACTIVE
    assert mgr.is_active


def test_create_session_retry_then_success():
    mgr, _ = _make_manager(fail_count=2)
    info = mgr.create_session()
    assert info.state == SessionState.ACTIVE
    assert info.retry_count == 2


def test_create_session_all_retries_fail():
    mgr, _ = _make_manager(fail_count=10)
    with pytest.raises(SessionError, match="セッションの作成に失敗しました"):
        mgr.create_session()
    assert mgr.session.state == SessionState.ERROR


def test_send_message_auto_creates_session():
    mgr, client = _make_manager(fail_count=0)

    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_chat.send_message.return_value = mock_response
    client.chats.create = MagicMock(return_value=mock_chat)

    mgr = SessionManager(
        client=client,
        model="test-model",
        config=MagicMock(),
        retry_config=RetryConfig(max_retries=3, base_delay_sec=0.01),
    )

    mgr.create_session()
    response = mgr.send_message("hello")
    assert response == mock_response
    assert mgr.session.message_count == 1


def test_close_session():
    mgr, _ = _make_manager(fail_count=0)
    mgr.create_session()
    assert mgr.is_active
    mgr.close()
    assert not mgr.is_active
    assert mgr.session.state == SessionState.CLOSED


def test_reset_session():
    mgr, _ = _make_manager(fail_count=0)
    mgr.create_session()
    old_id = mgr.session.session_id
    info = mgr.reset()
    assert info.state == SessionState.ACTIVE
    # reset creates a new session
    assert info.session_id != old_id


def test_send_message_on_closed_session_raises():
    mgr, _ = _make_manager(fail_count=0)
    mgr.create_session()
    mgr.close()
    with pytest.raises(SessionError, match="閉じられています"):
        mgr.send_message("hello")


def test_session_info_defaults():
    info = SessionInfo()
    assert info.state == SessionState.IDLE
    assert info.message_count == 0
    assert info.error_message is None
    assert len(info.session_id) == 12
