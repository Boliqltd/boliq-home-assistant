"""Shared parts of every Boliq entity."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BoliqCoordinator


class BoliqEntity(CoordinatorEntity[BoliqCoordinator]):
    """One part of one bollard."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BoliqCoordinator, device_id: str, key: str) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"
        device = coordinator.data[device_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device.get("label") or "Bollard",
            manufacturer="Boliq",
            model="Automatic bollard",
            sw_version=device.get("firmware_version"),
            serial_number=device.get("code"),
        )

    @property
    def device(self) -> dict[str, Any]:
        """The bollard as Boliq last reported it."""
        return self.coordinator.data[self.device_id]

    @property
    def available(self) -> bool:
        """Gone if the owner took it away from Home Assistant."""
        return super().available and self.device_id in self.coordinator.data
