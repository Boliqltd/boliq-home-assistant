"""Add Boliq: sign in on Connect to Boliq and choose bollards."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL, DOMAIN, SCOPES


class BoliqFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Sign in with Boliq."""

    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Ask for lowering and raising; the owner decides on the Boliq page."""
        return {"scope": " ".join(SCOPES)}

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """One entry per Boliq link (the owner's approval)."""
        session = async_get_clientsession(self.hass)
        try:
            resp = await session.get(
                f"{API_URL}/devices",
                headers={"Authorization": f"Bearer {data[CONF_TOKEN][CONF_ACCESS_TOKEN]}"},
            )
            body = await resp.json(content_type=None)
        except Exception:  # noqa: BLE001
            self.logger.exception("Could not reach Boliq")
            return self.async_abort(reason="cannot_connect")
        if resp.status != 200:
            return self.async_abort(reason="cannot_connect")
        devices = (body or {}).get("data") or []
        if not devices:
            return self.async_abort(reason="no_devices")
        link = (devices[0].get("connection") or {}).get("id")
        await self.async_set_unique_id(link)
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="wrong_account")
            return self.async_update_reload_and_abort(self._get_reauth_entry(), data=data)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Boliq", data=data)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """The owner disconnected Home Assistant, or the link expired."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask before sending them to Boliq again."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()
