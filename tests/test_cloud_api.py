from __future__ import annotations

import pytest

from helpers import load_innova_module

cloud_api = load_innova_module("cloud_api")
DiffusAppCloudApi = cloud_api.DiffusAppCloudApi
UnauthorizedError = cloud_api.UnauthorizedError
clean_device_auth = cloud_api.clean_device_auth
parse_device_auth_mac = cloud_api.parse_device_auth_mac


def test_parse_device_auth_mac_extracts_office_base_mac() -> None:
    auth = "fc012cfa131c" + ("00" * 131)

    assert parse_device_auth_mac(auth) == "FC:01:2C:FA:13:1C"


def test_parse_device_auth_mac_extracts_bedroom_base_mac() -> None:
    auth = "FC012CF8152C" + ("aa" * 131)

    assert parse_device_auth_mac(auth) == "FC:01:2C:F8:15:2C"


def test_clean_device_auth_strips_separators_and_uppercases() -> None:
    auth = "fc:01:2c:fa:13:1c 00-aa"

    assert clean_device_auth(auth) == "FC012CFA131C00AA"


class FakeResponse:
    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        self._payload = payload

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def json(self) -> object:
        return self._payload

    async def text(self) -> str:
        return str(self._payload)


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.responses: list[FakeResponse] = []

    def queue(self, status: int, payload: object) -> None:
        self.responses.append(FakeResponse(status, payload))

    def post(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append(("POST", url, kwargs))
        return self.responses.pop(0)

    def get(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append(("GET", url, kwargs))
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_login_sends_solutiontech_payload() -> None:
    session = FakeSession()
    session.queue(200, {"token": "abc123", "user": {"email": "user@example.com"}})
    api = DiffusAppCloudApi(session)

    result = await api.login("user@example.com", "secret")

    assert result["token"] == "abc123"
    assert session.calls == [
        (
            "POST",
            "https://api.innova.solutiontech.tech/api/users/login",
            {"json": {"email": "user@example.com", "password": "secret"}},
        )
    ]


@pytest.mark.asyncio
async def test_create_device_uses_bearer_auth_and_does_not_store_auth() -> None:
    session = FakeSession()
    session.queue(200, {"macAddress": "FC:01:2C:FA:13:1C", "name": "Office"})
    api = DiffusAppCloudApi(session)

    result = await api.create_device(
        token="abc123",
        home_id="00000000-0000-0000-0000-000000000001",
        device_auth="fc012cfa131c" + ("00" * 131),
    )

    assert result["macAddress"] == "FC:01:2C:FA:13:1C"
    assert session.calls[0] == (
        "POST",
        "https://api.innova.solutiontech.tech/api/devices",
        {
            "json": {
                "homeId": "00000000-0000-0000-0000-000000000001",
                "deviceAuth": "fc012cfa131c" + ("00" * 131),
            },
            "headers": {"Authorization": "Bearer abc123"},
        },
    )


@pytest.mark.asyncio
async def test_unauthorized_response_raises_reauth_error() -> None:
    session = FakeSession()
    session.queue(401, {"message": "expired"})
    api = DiffusAppCloudApi(session)

    with pytest.raises(UnauthorizedError):
        await api.get_homes("expired-token")
