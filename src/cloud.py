from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import environ
import httpx
from dataclasses_json import config, dataclass_json

from models import AccountInfoResponse, HistoryResponse
from parser import StateBuilder

if TYPE_CHECKING:
    from parser import State


def _base64_encode(data: str) -> str:
    return base64.b64encode(data.encode()).decode("utf-8")


def get_client_info(auth_mode: bool) -> str:
    data: dict = {
        "dm": "Mac15,6",
        "lr": "US",
        "nf": True,
        "nk": False,
        "nn": "ThingsMac",
        "nv": "32209501",
        "on": "macOS",
        "ov": "15.7.2",
        "pl": "en-US",
        "ul": "en-Latn-US",
    }
    if auth_mode:
        data["wn"] = "ThingsAccount"
        data["wv"] = "0.1"
    return _base64_encode(json.dumps(data))


class ThingsLoginAuth(httpx.Auth):
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

    def get_auth_header(self) -> str:
        data: dict = {
            "emailAndPassword": {
                "email": self.email,
                "password": self.password,
            }
        }
        return _base64_encode(json.dumps(data))

    def auth_flow(self, request):
        request.headers["Authorization"] = f"TAB {self.get_auth_header()}"
        yield request


class ThingsPasswordAuth(httpx.Auth):
    def __init__(self, password: str):
        self.password = password

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Password {self.password}"
        yield request


@dataclass_json
@dataclass
class LoginResponse:
    head_index: int = field(metadata=config(field_name="headIndex"))
    history_key_session_token: str = field(
        metadata=config(field_name="historyKeySessionToken")
    )


EVENT_TYPES: set[str] = {
    "ChecklistItem3",
    "Area3",
    "Task6",
    "Tag4",
    "Settings5",
    "Tombstone2",
}


class CloudAPI:
    def __init__(self, email: str, password: str):
        self.client = httpx.Client(
            headers={
                "things-client-info": get_client_info(auth_mode=False),
                "User-Agent": "ThingsMac/32209501",
            },
            timeout=30.0,
        )
        self.email = email
        self.password = password

    _history_key: str | None = None

    def login(self) -> LoginResponse:
        r: httpx.Response = self._do_api_request(
            "POST",
            "https://cloud.culturedcode.com/api/account/session/getT3SharedSession",
            auth=ThingsLoginAuth(self.email, self.password),
            headers={"things-client-info": get_client_info(auth_mode=True)},
        )
        resp: LoginResponse = LoginResponse.from_json(r.text)
        return resp

    def account_info(self) -> AccountInfoResponse:
        r: httpx.Response = self._do_api_request(
            "GET",
            f"https://cloud.culturedcode.com/version/1/account/{self.email}",
            auth=ThingsPasswordAuth(self.password),
        )
        resp: AccountInfoResponse = AccountInfoResponse.from_json(r.text)
        return resp

    def history(self, index: int) -> HistoryResponse:
        r: httpx.Response = self._do_api_request(
            "GET",
            f"https://cloud.culturedcode.com/version/1/history/{self.history_key}/items",
            params={"start-index": index},
        )
        with open(f"history_{index}.json", "w", encoding="utf-8") as f:
            f.write(r.text)
        resp: HistoryResponse = HistoryResponse.from_json(r.text)
        return resp

    @property
    def history_key(self) -> str:
        if self._history_key is None:
            info = self.account_info()
            self._history_key = info.history_key
        return self._history_key

    def full_history(self) -> list[HistoryResponse]:
        all_items: list[HistoryResponse] = []
        index = 0
        while True:
            resp = self.history(index)
            all_items.append(resp)
            if resp.end_total_content_size == resp.latest_total_content_size:
                break
            index += len(resp.items)
        return all_items

    def full_state(self) -> State:
        builder = StateBuilder()
        builder.apply_all(self.full_history())
        return builder.build()

    def _do_api_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        r: httpx.Response = self.client.request(method, url, **kwargs)
        r.raise_for_status()
        return r


if __name__ == "__main__":
    env = environ.Env()
    environ.Env.read_env()
    api = CloudAPI(env.str("THINGS_EMAIL"), env.str("THINGS_PASSWORD"))
    state: State = api.full_state()
    for uid, task in state.tasks.items():
        if task.is_open and task.is_project:
            print(f"{uid} | {task.title}")
