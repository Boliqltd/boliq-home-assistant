"""Each bollard as a cover. Open means LOWERED (cars can pass), closed means RAISED."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import BoliqError
from .const import LOWERED, RAISED
from .coordinator import BoliqConfigEntry
from .entity import BoliqEntity


async def async_setup_entry(hass: HomeAssistant, entry: BoliqConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Add a cover for each bollard."""
    coordinator = entry.runtime_data
    async_add_entities(BoliqBollard(coordinator, device_id) for device_id in coordinator.data)


class BoliqBollard(BoliqEntity, CoverEntity):
    """A Boliq bollard."""

    _attr_name = None
    _attr_device_class = CoverDeviceClass.GATE

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id, "bollard")

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Lowering if the owner allowed it, raising only if they ticked Allow raising."""
        permissions = self.device.get("permissions") or {}
        features = CoverEntityFeature(0)
        if permissions.get("control"):
            features |= CoverEntityFeature.OPEN
        if permissions.get("raise"):
            features |= CoverEntityFeature.CLOSE
        return features

    @property
    def current_cover_position(self) -> int | None:
        """100 when lowered, 0 when raised."""
        position = self.device.get("position")
        return 100 if position == LOWERED else 0 if position == RAISED else None

    @property
    def is_closed(self) -> bool | None:
        """Closed means raised."""
        position = self.device.get("position")
        return None if position not in (LOWERED, RAISED) else position == RAISED

    @property
    def is_opening(self) -> bool:
        return self.device.get("pending_position") == LOWERED and self.device.get("position") != LOWERED

    @property
    def is_closing(self) -> bool:
        return self.device.get("pending_position") == RAISED and self.device.get("position") != RAISED

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "position_source": self.device.get("position_source"),
            "last_seen_at": self.device.get("last_seen_at"),
            "fault": self.device.get("fault"),
        }

    async def _move(self, position: str) -> None:
        try:
            await self.coordinator.api.async_move(self.device_id, position)
        except BoliqError as err:
            raise HomeAssistantError(f"Boliq: {err}") from err
        # The bollard confirms when it next checks in; read again soon.
        await self.coordinator.async_request_refresh()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Lower the bollard."""
        await self._move(LOWERED)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Raise the bollard."""
        await self._move(RAISED)
