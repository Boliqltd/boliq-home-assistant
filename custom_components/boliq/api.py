"""A small client for the Boliq partner API (https://boliq.co.uk/api/v1)."""

from __future__ import annotations

from json import loads as json_loads
from typing import Any
import uuid

from aiohttp import ClientError, ClientSession

from homeassistant.helpers import config_entry_oauth2_flow

from .const import API_URL


class BoliqError(Exception):
    """The API said no, or could not be reached."""

    def __init__(self, message: str, code: str | None = None, status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class BoliqAuthError(BoliqError):
    """The owner disconnected Home Assistant, or the sign in has to be done again."""


class BoliqApi:
    """Reads bollards and asks them to move, as the owner who signed in."""

    def __init__(self, websession: ClientSession, oauth_session: config_entry_oauth2_flow.OAuth2Session) -> None:
        self._websession = websession
        self._oauth = oauth_session

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        try:
            await self._oauth.async_ensure_token_valid()
        except ClientError as err:
            # A refused refresh (for example the owner disconnected it) needs a new sign in.
            raise BoliqAuthError(str(err)) from err
        token = self._oauth.token["access_token"]
        try:
            resp = await self._websession.request(
                method,
                API_URL + path,
                json=json,
                headers={"Authorization": f"Bearer {token}", **(headers or {})},
            )
            text = await resp.text()
            data = json_loads(text) if text else None
        except (ClientError, TimeoutError, ValueError) as err:
            raise BoliqError(f"Could not reach Boliq: {err}") from err
        if resp.status == 401:
            raise BoliqAuthError("Boliq needs you to sign in again.", status=401)
        if resp.status >= 400:
            error = (data or {}).get("error", {}) if isinstance(data, dict) else {}
            raise BoliqError(error.get("message") or f"Boliq answered {resp.status}.", error.get("code"), resp.status)
        return data

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Every bollard the owner chose for Home Assistant."""
        data = await self._request("GET", "/devices")
        return list((data or {}).get("data", []))

    async def async_move(self, device_id: str, position: str) -> dict[str, Any]:
        """Ask a bollard to raise or lower. Returns the queued command."""
        return await self._request(
            "POST",
            f"/devices/{device_id}/commands",
            json={"position": position},
            headers={"Idempotency-Key": f"ha-{uuid.uuid4()}"},
        )
