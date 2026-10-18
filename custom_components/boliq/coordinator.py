"""Reads every bollard from Boliq on a timer."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BoliqApi, BoliqAuthError, BoliqError
from .const import DOMAIN, MOVING_INTERVAL_S, UPDATE_INTERVAL_S

_LOGGER = logging.getLogger(__name__)

type BoliqConfigEntry = ConfigEntry[BoliqCoordinator]


class BoliqCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Bollards by id. Reads more often while one is on its way."""

    config_entry: BoliqConfigEntry

    def __init__(self, hass: HomeAssistant, entry: BoliqConfigEntry, api: BoliqApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_S),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.api.async_get_devices()
        except BoliqAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except BoliqError as err:
            raise UpdateFailed(str(err)) from err
        moving = any(d.get("pending_position") for d in devices)
        self.update_interval = timedelta(seconds=MOVING_INTERVAL_S if moving else UPDATE_INTERVAL_S)
        return {d["id"]: d for d in devices}
