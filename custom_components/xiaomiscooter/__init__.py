from __future__ import annotations

from datetime import timedelta
import logging

from .xiaomi_scooter_ble import ScooterBluetoothDeviceData

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import CONF_TOKEN, DEFAULT_SCAN_INTERVAL, DOMAIN

PLATFORMS: list[Platform] = [
    Platform.SENSOR, 
    Platform.BUTTON
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xiaomi Scooter BLE device from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    address = entry.unique_id
    token = entry.data.get(CONF_TOKEN)

    is_metric = hass.config.units is METRIC_SYSTEM
    assert address is not None

    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)

    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find Xiaomi Scooter device with address: {address}"
        )

    scooter = ScooterBluetoothDeviceData(is_metric, ble_device=ble_device, token=token)

    async def _async_update_method():
        """Get data from Xiaomi Scooter over BLE."""
        _LOGGER.debug("async update method.")
        try:
            current_ble_device = bluetooth.async_ble_device_from_address(
                hass,
                address,
                connectable=True,
            )
            if current_ble_device is None:
                raise UpdateFailed(
                    f"Could not find Xiaomi Scooter device with address: {address}"
                )

            scooter.set_runtime_data(ble_device=current_ble_device)
            data = await scooter.update_data()
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch data: {err}") from err

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_method,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
