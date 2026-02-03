"""Tests for Things3 Cloud API client."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from opentasks.cloud import (
    CloudAPI,
    LoginResponse,
    ThingsLoginAuth,
    ThingsPasswordAuth,
    _base64_encode,
    get_client_info,
)


class TestBase64Encode:
    def test_encode_simple_string(self) -> None:
        result = _base64_encode("test")
        assert result == "dGVzdA=="

    def test_encode_json(self) -> None:
        data = {"key": "value"}
        result = _base64_encode(json.dumps(data))
        decoded = json.loads(__import__("base64").b64decode(result).decode())
        assert decoded == data


class TestGetClientInfo:
    def test_auth_mode_false(self) -> None:
        result = get_client_info(auth_mode=False)
        decoded = json.loads(__import__("base64").b64decode(result).decode())
        assert decoded["nn"] == "ThingsMac"
        assert "wn" not in decoded
        assert "wv" not in decoded

    def test_auth_mode_true(self) -> None:
        result = get_client_info(auth_mode=True)
        decoded = json.loads(__import__("base64").b64decode(result).decode())
        assert decoded["nn"] == "ThingsMac"
        assert decoded["wn"] == "ThingsAccount"
        assert decoded["wv"] == "0.1"


class TestThingsLoginAuth:
    def test_get_auth_header(self) -> None:
        auth = ThingsLoginAuth("test@example.com", "secret123")
        header = auth.get_auth_header()
        decoded = json.loads(__import__("base64").b64decode(header).decode())
        assert decoded["emailAndPassword"]["email"] == "test@example.com"
        assert decoded["emailAndPassword"]["password"] == "secret123"

    def test_auth_flow(self) -> None:
        auth = ThingsLoginAuth("test@example.com", "secret123")
        request = MagicMock()
        request.headers = {}
        flows = list(auth.auth_flow(request))
        assert len(flows) == 1
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("TAB ")


class TestThingsPasswordAuth:
    def test_auth_flow(self) -> None:
        auth = ThingsPasswordAuth("password123")
        request = MagicMock()
        request.headers = {}
        flows = list(auth.auth_flow(request))
        assert len(flows) == 1
        assert request.headers["Authorization"] == "Password password123"


class TestLoginResponse:
    def test_from_json(self) -> None:
        raw = {"headIndex": 42, "historyKeySessionToken": "token-abc-123"}
        resp = LoginResponse.from_dict(raw)
        assert resp.head_index == 42
        assert resp.history_key_session_token == "token-abc-123"


class TestCloudAPILogin:
    @patch("cloud.httpx.Client")
    def test_login_success(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "headIndex": 100,
                "historyKeySessionToken": "session-token",
            }
        )
        mock_client.request.return_value = mock_response

        api = CloudAPI("test@example.com", "password123")
        result = api.login()

        assert result.head_index == 100
        assert result.history_key_session_token == "session-token"
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "getT3SharedSession" in call_args[0][1]


class TestCloudAPIAccountInfo:
    @patch("cloud.httpx.Client")
    def test_account_info_success(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "SLA-version-accepted": "1.0",
                "email": "test@example.com",
                "history-key": "history-key-123",
                "issues": [],
                "maildrop-email": "drop@things.email",
                "status": "active",
            }
        )
        mock_client.request.return_value = mock_response

        api = CloudAPI("test@example.com", "password123")
        result = api.account_info()

        assert result.email == "test@example.com"
        assert result.history_key == "history-key-123"
        assert result.status == "active"


class TestCloudAPIHistory:
    @patch("cloud.httpx.Client")
    def test_history_success(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        account_response = MagicMock()
        account_response.text = json.dumps(
            {
                "SLA-version-accepted": "1.0",
                "email": "test@example.com",
                "history-key": "history-key-123",
                "issues": [],
                "maildrop-email": None,
                "status": "active",
            }
        )

        history_response = MagicMock()
        history_response.text = json.dumps(
            {
                "current-item-index": 0,
                "end-total-content-size": 1000,
                "latest-total-content-size": 1000,
                "schema": 312,
                "start-total-content-size": 0,
                "items": [{"uuid-1": {"t": 0, "e": "Task6", "p": {"tt": "Test Task"}}}],
            }
        )

        mock_client.request.side_effect = [account_response, history_response]

        api = CloudAPI("test@example.com", "password123")

        with patch("builtins.open", MagicMock()):
            result = api.history(0)

        assert result.current_item_index == 0
        assert result.end_total_content_size == 1000
        assert len(result.items) == 1


class TestCloudAPIFullHistory:
    @patch("cloud.httpx.Client")
    def test_full_history_single_page(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        account_response = MagicMock()
        account_response.text = json.dumps(
            {
                "SLA-version-accepted": "1.0",
                "email": "test@example.com",
                "history-key": "history-key-123",
                "issues": [],
                "maildrop-email": None,
                "status": "active",
            }
        )

        history_response = MagicMock()
        history_response.text = json.dumps(
            {
                "current-item-index": 0,
                "end-total-content-size": 1000,
                "latest-total-content-size": 1000,
                "schema": 312,
                "start-total-content-size": 0,
                "items": [{"uuid-1": {"t": 0, "e": "Task6", "p": {"tt": "Task 1"}}}],
            }
        )

        mock_client.request.side_effect = [account_response, history_response]

        api = CloudAPI("test@example.com", "password123")

        with patch("builtins.open", MagicMock()):
            result = api.full_history()

        assert len(result) == 1
        assert result[0].end_total_content_size == 1000

    @patch("cloud.httpx.Client")
    def test_full_history_multiple_pages(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        account_response = MagicMock()
        account_response.text = json.dumps(
            {
                "SLA-version-accepted": "1.0",
                "email": "test@example.com",
                "history-key": "history-key-123",
                "issues": [],
                "maildrop-email": None,
                "status": "active",
            }
        )

        history_page_1 = MagicMock()
        history_page_1.text = json.dumps(
            {
                "current-item-index": 0,
                "end-total-content-size": 500,
                "latest-total-content-size": 1000,
                "schema": 312,
                "start-total-content-size": 0,
                "items": [
                    {"uuid-1": {"t": 0, "e": "Task6", "p": {"tt": "Task 1"}}},
                    {"uuid-2": {"t": 0, "e": "Task6", "p": {"tt": "Task 2"}}},
                ],
            }
        )

        history_page_2 = MagicMock()
        history_page_2.text = json.dumps(
            {
                "current-item-index": 2,
                "end-total-content-size": 1000,
                "latest-total-content-size": 1000,
                "schema": 312,
                "start-total-content-size": 500,
                "items": [
                    {"uuid-3": {"t": 0, "e": "Task6", "p": {"tt": "Task 3"}}},
                ],
            }
        )

        mock_client.request.side_effect = [
            account_response,
            history_page_1,
            history_page_2,
        ]

        api = CloudAPI("test@example.com", "password123")

        with patch("builtins.open", MagicMock()):
            result = api.full_history()

        assert len(result) == 2
        assert result[0].end_total_content_size == 500
        assert result[1].end_total_content_size == 1000


class TestCloudAPIFullState:
    @patch("cloud.httpx.Client")
    def test_full_state(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        account_response = MagicMock()
        account_response.text = json.dumps(
            {
                "SLA-version-accepted": "1.0",
                "email": "test@example.com",
                "history-key": "history-key-123",
                "issues": [],
                "maildrop-email": None,
                "status": "active",
            }
        )

        history_response = MagicMock()
        history_response.text = json.dumps(
            {
                "current-item-index": 0,
                "end-total-content-size": 1000,
                "latest-total-content-size": 1000,
                "schema": 312,
                "start-total-content-size": 0,
                "items": [
                    {
                        "task-1": {
                            "t": 0,
                            "e": "Task6",
                            "p": {"tt": "My Task", "ss": 0},
                        },
                        "area-1": {"t": 0, "e": "Area3", "p": {"tt": "Work"}},
                    }
                ],
            }
        )

        mock_client.request.side_effect = [account_response, history_response]

        api = CloudAPI("test@example.com", "password123")

        with patch("builtins.open", MagicMock()):
            state = api.full_state()

        assert len(state.tasks) == 1
        assert "task-1" in state.tasks
        assert state.tasks["task-1"].title == "My Task"
        assert len(state.areas) == 1
        assert "area-1" in state.areas


class TestCloudAPIHistoryKey:
    @patch("cloud.httpx.Client")
    def test_history_key_cached(self, mock_client_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        account_response = MagicMock()
        account_response.text = json.dumps(
            {
                "SLA-version-accepted": "1.0",
                "email": "test@example.com",
                "history-key": "history-key-123",
                "issues": [],
                "maildrop-email": None,
                "status": "active",
            }
        )
        mock_client.request.return_value = account_response

        api = CloudAPI("test@example.com", "password123")

        key1 = api.history_key
        key2 = api.history_key

        assert key1 == "history-key-123"
        assert key2 == "history-key-123"
        assert mock_client.request.call_count == 1
