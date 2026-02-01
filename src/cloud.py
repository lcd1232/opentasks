import base64
import json
from dataclasses import dataclass, field

import environ
import httpx
from dataclasses_json import config, dataclass_json


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


@dataclass_json
@dataclass
class HistoryObject:
    object_type: str = field(metadata=config(field_name="t"))
    e: str = field(metadata=config(field_name="e"))
    p: dict = field(metadata=config(field_name="p"))


@dataclass_json
@dataclass
class HistoryResponse:
    current_item_index: int = field(metadata=config(field_name="current-item-index"))
    end_total_content_size: int = field(
        metadata=config(field_name="end-total-content-size")
    )
    latest_total_content_size: int = field(
        metadata=config(field_name="latest-total-content-size")
    )
    schema: int = field(metadata=config(field_name="schema"))
    start_total_content_size: int = field(
        metadata=config(field_name="start-total-content-size")
    )
    items: list[dict[str, HistoryObject]] = field(metadata=config(field_name="items"))


@dataclass_json
@dataclass
class AccountInfoResponse:
    sla_version_accepted: str = field(
        metadata=config(field_name="SLA-version-accepted")
    )
    email: str = field(metadata=config(field_name="email"))
    history_key: str = field(metadata=config(field_name="history-key"))
    issues: list = field(metadata=config(field_name="issues"))
    maildrop_email: str = field(metadata=config(field_name="maildrop-email"))
    status: str = field(metadata=config(field_name="status"))


class CloudAPI:
    def __init__(self, email: str, password: str):
        self.client = httpx.Client(
            headers={
                "things-client-info": get_client_info(auth_mode=False),
                "User-Agent": "ThingsMac/32209501",
            },
            verify=False,
        )
        self.email = email
        self.password = password

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

    def history(self, history_key: str, index: int) -> HistoryResponse:
        r: httpx.Response = self._do_api_request(
            "GET",
            f"https://cloud.culturedcode.com/version/1/history/{history_key}/items",
            params={"start-index": index},
        )
        resp: HistoryResponse = HistoryResponse.from_json(r.text)
        return resp

    def _do_api_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        r: httpx.Response = self.client.request(method, url, **kwargs)
        r.raise_for_status()
        return r


if __name__ == "__main__":
    env = environ.Env()
    environ.Env.read_env()
    api = CloudAPI(env.str("THINGS_EMAIL"), env.str("THINGS_PASSWORD"))
    api.login()
    info = api.account_info()
    history = api.history(info.history_key, 6069)
    print(history)
