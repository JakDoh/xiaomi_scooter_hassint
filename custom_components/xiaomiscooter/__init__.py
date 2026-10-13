from __future__ import annotations

from datetime import timedelta
import logging

from .xiaomi_scooter_ble import ScooterBluetoothDeviceData

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import (
    CONF_TOKEN,
    CONF_SCAN_INTERVAL_CHARGING,
    CONF_SCAN_INTERVAL_NOT_CHARGING,
    DEFAULT_SCAN_INTERVAL_CHARGING,
    DEFAULT_SCAN_INTERVAL_NOT_CHARGING,
    DOMAIN,
)

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
        raise ConfigEntryNotReady(f"Could not find Xiaomi Scooter device with address: {address}")

    scooter = ScooterBluetoothDeviceData(is_metric, ble_device=ble_device, token=token)

    async def _async_update_method():
        try:
            current_ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
            if current_ble_device is None:
                raise UpdateFailed(f"Could not find Xiaomi Scooter device with address: {address}")

            scooter.set_runtime_data(ble_device=current_ble_device)
            data = await scooter.update_data()
            
            # DYNAMICKÝ INTERVAL DLE STAVU NABÍJENÍ
            charging = data.sensors.get("battery_charging_status") == "Charging"
            interval_charging = entry.options.get(CONF_SCAN_INTERVAL_CHARGING, DEFAULT_SCAN_INTERVAL_CHARGING)
            interval_not_charging = entry.options.get(CONF_SCAN_INTERVAL_NOT_CHARGING, DEFAULT_SCAN_INTERVAL_NOT_CHARGING)
            
            new_interval = interval_charging if charging else interval_not_charging
            coordinator.update_interval = timedelta(seconds=new_interval)
            
            _LOGGER.debug(
                "Scooter update done (Charging: %s). Next poll in %s seconds",
                charging, new_interval
            )
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch data: {err}") from err

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_method,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_NOT_CHARGING),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # OKAMŽITÁ AKTUALIZACE PŘI NÁVRATU DO DOSAHU (BLE Advertisement Listener)
    @callback
    def _on_bluetooth_advertisement(service_info, change):
        """Vyvolá okamžitou aktualizaci, pokud koloběžka byla nedostupná a právě se objevila."""
        if not coordinator.last_update_success:
            _LOGGER.info("Scooter %s is back in range! Triggering immediate update.", address)
            hass.async_create_task(coordinator.async_request_refresh())

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _on_bluetooth_advertisement,
            {"address": address},
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )

    entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok