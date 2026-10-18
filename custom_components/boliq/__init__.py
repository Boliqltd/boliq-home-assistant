"""Boliq automatic bollards in Home Assistant.

Signs in through Connect to Boliq (the owner chooses which bollards and
whether raising is allowed) and uses the Boliq partner API at
https://boliq.co.uk/api/v1. Each bollard is a cover: open means lowered.
"""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow

from .api import BoliqApi
from .coordinator import BoliqConfigEntry, BoliqCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.COVER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: BoliqConfigEntry) -> bool:
    """Set up Boliq from a config entry."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    api = BoliqApi(aiohttp_client.async_get_clientsession(hass), oauth_session)
    coordinator = BoliqCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BoliqConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
