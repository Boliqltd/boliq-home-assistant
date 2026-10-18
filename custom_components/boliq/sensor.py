"""Battery level of each bollard that reports one (mains bollards do not)."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BoliqConfigEntry
from .entity import BoliqEntity


async def async_setup_entry(hass: HomeAssistant, entry: BoliqConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Add a battery sensor for each bollard with a battery."""
    coordinator = entry.runtime_data
    async_add_entities(
        BoliqBattery(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if device.get("battery_pct") is not None
    )


class BoliqBattery(BoliqEntity, SensorEntity):
    """Battery percentage."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id, "battery")

    @property
    def native_value(self) -> int | None:
        value = self.device.get("battery_pct")
        return None if value is None else int(value)
