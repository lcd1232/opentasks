import base64
import json
from dataclasses import dataclass, field

import environ
import httpx
from dataclasses_json import config, dataclass_json


def _base64_encode(data: str) -> str:
    return base64.b64encode(data.encode()).decode("utf-8")


def get_client_info() -> str:
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
        "wn": "ThingsAccount",
        "wv": "0.1",
    }
    return _base64_encode(json.dumps(data))


class ThingsAuth(httpx.Auth):
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


@dataclass_json
@dataclass
class LoginResponse:
    head_index: int = field(metadata=config(field_name="headIndex"))
    history_key_session_token: str = field(
        metadata=config(field_name="historyKeySessionToken")
    )


class CloudAPI:
    def __init__(self):
        self.client = httpx.Client(headers={"things-client-info": get_client_info()})

    def login(self, email: str, password: str) -> bool:
        r: httpx.Response = self.client.post(
            "https://cloud.culturedcode.com/api/account/session/getT3SharedSession",
            auth=ThingsAuth(email, password),
        )
        resp: LoginResponse = LoginResponse.from_json(r.text)
        print(resp)

    def _do_api_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        r: httpx.Response = self.client.request(method, url, **kwargs)
        r.raise_for_status()
        return r


if __name__ == "__main__":
    env = environ.Env()
    environ.Env.read_env()
    api = CloudAPI()
    api.login(env.str("THINGS_EMAIL"), env.str("THINGS_PASSWORD"))
