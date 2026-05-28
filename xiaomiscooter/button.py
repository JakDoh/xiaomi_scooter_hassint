
"""Support for the Xiaomi scooter."""
from __future__ import annotations

import logging
from .xiaomi_scooter_ble import ScooterDevice

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)

from .const import DOMAIN

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)

REFRESH_BUTTON: ButtonEntityDescription = ButtonEntityDescription(
    key="refresh",
    name="Refresh",
    device_class=ButtonDeviceClass.UPDATE,
    entity_category=EntityCategory.CONFIG,
)


def _stable_unique_id(scooter: ScooterDevice, key: str) -> str:
    base_id = (scooter.mac_address or scooter.name).replace(":", "").lower()
    return f"{base_id}_{key}"


def _legacy_unique_id(scooter: ScooterDevice, key: str) -> str:
    return f"{scooter.name}_{key}"


def _device_identifiers(scooter: ScooterDevice) -> set[tuple[str, str]]:
    identifiers = {(DOMAIN, scooter.mac_address or scooter.name)}
    if scooter.name:
        identifiers.add((DOMAIN, scooter.name))
    return identifiers


async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:

    entity_registry = async_get(hass)

    async def migrate_entity_if_needed(old_unique_id: str, new_unique_id: str) -> None:
        if old_unique_id == new_unique_id:
            return

        try:
            entity_id = entity_registry.async_get_entity_id("button", DOMAIN, old_unique_id)
            if entity_id is None:
                return

            if entity_registry.async_get_entity_id("button", DOMAIN, new_unique_id):
                entity_registry.async_remove(entity_id)
                _LOGGER.debug("Removed duplicate legacy button entity %s", entity_id)
                return

            entity_registry.async_update_entity(entity_id, new_unique_id=new_unique_id)
            _LOGGER.debug("Migrated button entity %s to %s", entity_id, new_unique_id)
        except Exception as err:
            _LOGGER.debug(f"Unexpected error during entity migration, {err=}, {type(err)=}")
            raise
    
    
    coordinator: DataUpdateCoordinator[ScooterDevice] = hass.data[DOMAIN][entry.entry_id]

    entities = []
    await migrate_entity_if_needed(
        _legacy_unique_id(coordinator.data, REFRESH_BUTTON.key),
        _stable_unique_id(coordinator.data, REFRESH_BUTTON.key),
    )
    entities.append(ScooterButton(coordinator,coordinator.data, REFRESH_BUTTON))

    async_add_entities(entities, False)


class ScooterButton(
    CoordinatorEntity[DataUpdateCoordinator[ScooterDevice]], ButtonEntity
):
    _attr_has_entity_name = True
    entry: ConfigEntry = None
    def __init__(
        self,
        coordinator: DataUpdateCoordinator[ScooterDevice],
        scooter: ScooterDevice,
        entity_description: ButtonEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            connections={
                (
                    CONNECTION_BLUETOOTH,
                    scooter.mac_address,
                )
            },
            identifiers=_device_identifiers(scooter),
            name=scooter.name,
            manufacturer=scooter.manufacturer,
            model=scooter.model,
            sw_version=scooter.version,
        )
        self._attr_unique_id = _stable_unique_id(scooter, entity_description.key)
        self.entity_description = entity_description

    async def async_press(self) -> None:
        """Triggers the restart."""
        _LOGGER.debug("Refresh triggered by button")
        await self.coordinator.async_refresh()