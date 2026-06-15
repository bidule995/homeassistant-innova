"""Solution Tech DiffusApp REST API client."""
from __future__ import annotations

import re
from typing import Any

BASE_URL = "https://api.innova.solutiontech.tech/api"


class DiffusAppApiError(Exception):
    """Base error for DiffusApp REST failures."""


class UnauthorizedError(DiffusAppApiError):
    """Raised when the cloud token is invalid or expired."""


def bearer(token: str) -> str:
    """Return the Authorization header value used by the Android app."""
    return f"Bearer {token}"


def clean_device_auth(device_auth: str) -> str:
    """Normalize a BLE device_auth value for the cloud registration endpoint."""
    normalized = re.sub(r"[^0-9a-fA-F]", "", device_auth)
    if len(normalized) < 12:
        raise ValueError("device_auth must contain at least 6 bytes of hex data")
    return normalized.upper()


def parse_device_auth_mac(device_auth: str) -> str:
    """Extract the device base MAC from the BLE device_auth hex string."""
    normalized = clean_device_auth(device_auth)
    try:
        raw = bytes.fromhex(normalized[:12])
    except ValueError as err:
        raise ValueError("device_auth must be hexadecimal") from err
    return ":".join(f"{byte:02X}" for byte in raw)


class DiffusAppCloudApi:
    """Small aiohttp-style client for the Solution Tech REST API."""

    def __init__(self, session, base_url: str = BASE_URL) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")

    async def login(self, email: str, password: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "users/login",
            json={"email": email, "password": password},
            auth_token=None,
        )

    async def get_homes(self, token: str) -> list[dict[str, Any]]:
        data = await self._request("GET", "homes", auth_token=token)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("homes"), list):
            return data["homes"]
        return []

    async def create_home(
        self, token: str, name: str, timezone: str
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "homes",
            json={"name": name, "timezone": timezone},
            auth_token=token,
        )

    async def create_device(
        self, token: str, home_id: str, device_auth: str
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "devices",
            json={"homeId": home_id, "deviceAuth": device_auth},
            auth_token=token,
        )

    async def get_device_info(
        self, token: str, mac_address: str
    ) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"devices/{mac_address}",
            auth_token=token,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        auth_token: str | None = None,
    ) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        kwargs: dict[str, Any] = {}
        if json is not None:
            kwargs["json"] = json
        if auth_token:
            kwargs["headers"] = {"Authorization": bearer(auth_token)}

        request = self._session.post if method == "POST" else self._session.get
        async with request(url, **kwargs) as response:
            if response.status == 401:
                raise UnauthorizedError("DiffusApp token is invalid or expired")
            if response.status >= 400:
                body = await response.text()
                raise DiffusAppApiError(
                    f"DiffusApp API {method} {path} failed: {response.status} {body}"
                )
            return await response.json()
