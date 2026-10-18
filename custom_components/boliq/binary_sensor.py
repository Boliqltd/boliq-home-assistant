"""Whether each bollard is online (checking in with Boliq)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BoliqConfigEntry
from .entity import BoliqEntity


async def async_setup_entry(hass: HomeAssistant, entry: BoliqConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Add an online sensor for each bollard."""
    coordinator = entry.runtime_data
    async_add_entities(BoliqOnline(coordinator, device_id) for device_id in coordinator.data)


class BoliqOnline(BoliqEntity, BinarySensorEntity):
    """On while the bollard is checking in (a reported fault still counts as online)."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id, "online")

    @property
    def is_on(self) -> bool:
        return self.device.get("status") in ("online", "fault")
