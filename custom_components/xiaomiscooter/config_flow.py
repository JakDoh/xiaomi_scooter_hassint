from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict

from bleak import BleakError
import voluptuous as vol

from homeassistant import exceptions
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .xiaomi_scooter_ble import ScooterBluetoothDeviceData, ScooterDevice

from .const import (
    AUTH_METHOD_BUTTON,
    AUTH_METHOD_TOKEN,
    CONF_AUTH_METHOD,
    CONF_TOKEN,
    DOMAIN,
    SCOOTER_LIST,
    CONF_SCAN_INTERVAL_CHARGING,
    CONF_SCAN_INTERVAL_NOT_CHARGING,
    DEFAULT_SCAN_INTERVAL_CHARGING,
    DEFAULT_SCAN_INTERVAL_NOT_CHARGING,
)

_LOGGER = logging.getLogger(__name__)

@dataclasses.dataclass
class Discovery:
    name: str
    discovery_info: BluetoothServiceInfoBleak
    device: ScooterDevice | None

class ScooterDeviceAuthError(exceptions.HomeAssistantError):
    """Custom error class for device auth."""

class ScooterDeviceUpdateError(exceptions.HomeAssistantError):
    """Custom error class for device updates."""

class ScooterConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    AUTH_METHOD_OPTIONS = {
        AUTH_METHOD_BUTTON: "Scooter button pairing",
        AUTH_METHOD_TOKEN: "Existing token / key",
    }

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Return the options flow."""
        return OptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        self._discovered_device: Discovery | None = None
        self._discovered_devices: dict[str, Discovery] = {}

    async def _get_device_data(self, discovery_info: BluetoothServiceInfoBleak, token: str | None = None) -> ScooterDevice:
        ble_device = bluetooth.async_ble_device_from_address(self.hass, discovery_info.address, connectable=True)
        if ble_device is None:
            raise ScooterDeviceUpdateError("No ble_device")

        try:
            scooter = ScooterBluetoothDeviceData(True, token=token)
            data = await scooter.initialize_device(ble_device)
        except ValueError as err:
            raise ScooterDeviceAuthError("Invalid token") from err
        except BleakError as err:
            raise ScooterDeviceUpdateError("Failed getting device data") from err
        except Exception as err:
            raise err
        return data
    
    async def _register_device_with_button(self, discovery_info: BluetoothServiceInfoBleak) -> str:
        ble_device = bluetooth.async_ble_device_from_address(self.hass, discovery_info.address, connectable=True)
        if ble_device is None:
            raise ScooterDeviceAuthError("No ble_device")
        
        scooter = ScooterBluetoothDeviceData(True)
        try:
            await scooter.register_device(ble_device)
            token = scooter.token_hex()
            if token is None:
                raise ScooterDeviceAuthError("No token received")
        except BleakError as err:
            raise ScooterDeviceAuthError("Failed getting device data") from err
        except Exception as err:
            raise err
        return token
    
    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak) -> FlowResult:
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        name = discovery_info.name or discovery_info.address
        self.context["title_placeholders"] = {"name": name, "type": "Xiaomi Scooter"}
        self._discovered_device = Discovery(name, discovery_info, None)
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            return await self.async_step_auth_method()

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
            errors=errors
        )

    async def async_step_auth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                token = await self._register_device_with_button(self._discovered_device.discovery_info)
            except ScooterDeviceAuthError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=self._discovered_device.name,
                    data={CONF_AUTH_METHOD: AUTH_METHOD_BUTTON, CONF_TOKEN: token},
                )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="auth_confirm",
            description_placeholders=self.context["title_placeholders"],
            errors=errors,
        )

    async def async_step_auth_token(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN]
            try:
                device = await self._get_device_data(self._discovered_device.discovery_info, token=token)
            except ScooterDeviceAuthError:
                errors[CONF_TOKEN] = "invalid_auth"
            except ScooterDeviceUpdateError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                self._discovered_device.device = device
                return self.async_create_entry(
                    title=device.name or self._discovered_device.name,
                    data={CONF_AUTH_METHOD: AUTH_METHOD_TOKEN, CONF_TOKEN: token},
                )

        return self.async_show_form(
            step_id="auth_token",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            description_placeholders=self.context["title_placeholders"],
            errors=errors,
        )
    
    async def async_step_auth_method(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            method = user_input[CONF_AUTH_METHOD]
            if method == AUTH_METHOD_BUTTON:
                return await self.async_step_auth_confirm()
            if method == AUTH_METHOD_TOKEN:
                return await self.async_step_auth_token()
            
        return self.async_show_form(
            step_id="auth_method",
            data_schema=vol.Schema(
                {vol.Required(CONF_AUTH_METHOD, default=AUTH_METHOD_BUTTON): vol.In(self.AUTH_METHOD_OPTIONS)}
            ),
            description_placeholders=self.context["title_placeholders"],
            errors=errors
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            discovery = self._discovered_devices[address]
            self.context["title_placeholders"] = {"name": discovery.name}
            self._discovered_device = discovery
            return await self.async_step_auth_method()
            
        current_addresses = self._async_current_ids()
        for discovery_info in list(async_discovered_service_info(self.hass, connectable=True)).copy():
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue
            name = discovery_info.name or ""
            if not any(substring in name for substring in SCOOTER_LIST):
                continue
            self._discovered_devices[address] = Discovery(name, discovery_info, device=None)
                
        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        titles = {address: discovery.name for (address, discovery) in self._discovered_devices.items()}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(titles)}),
            description_placeholders={"description": "Test", "title": "Titulek"},
            errors=errors
        )

class OptionsFlowHandler(OptionsFlow):
    """Handle options flow for changing intervals and re-pairing."""
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Zobrazí rozcestník (Menu) pro volbu akce."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["polling", "reauth_button", "reauth_token"]
        )

    async def async_step_polling(self, user_input=None) -> FlowResult:
        """Původní nastavení intervalů."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required(
                CONF_SCAN_INTERVAL_NOT_CHARGING,
                default=self._config_entry.options.get(CONF_SCAN_INTERVAL_NOT_CHARGING, DEFAULT_SCAN_INTERVAL_NOT_CHARGING),
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            vol.Required(
                CONF_SCAN_INTERVAL_CHARGING,
                default=self._config_entry.options.get(CONF_SCAN_INTERVAL_CHARGING, DEFAULT_SCAN_INTERVAL_CHARGING),
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        })

        return self.async_show_form(step_id="polling", data_schema=schema)

    async def async_step_reauth_button(self, user_input=None) -> FlowResult:
        """Vyvolá nové párování přes tlačítko u existující koloběžky."""
        errors = {}
        if user_input is not None:
            address = self._config_entry.unique_id
            ble_device = bluetooth.async_ble_device_from_address(self.hass, address, connectable=True)
            if ble_device is None:
                errors["base"] = "cannot_connect"
            else:
                scooter = ScooterBluetoothDeviceData(True)
                try:
                    await scooter.register_device(ble_device)
                    token = scooter.token_hex()
                    if token is None:
                        raise ValueError("No token received")

                    # Přepis originálního data objektu (jádro HA to uloží a samo reloadne integraci)
                    new_data = dict(self._config_entry.data)
                    new_data[CONF_TOKEN] = token
                    new_data[CONF_AUTH_METHOD] = AUTH_METHOD_BUTTON
                    self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
                    
                    return self.async_create_entry(title="", data=self._config_entry.options)
                except Exception as err:
                    _LOGGER.error("Re-pairing via button failed: %r", err)
                    errors["base"] = "cannot_connect"

        return self.async_show_form(step_id="reauth_button", errors=errors)

    async def async_step_reauth_token(self, user_input=None) -> FlowResult:
        """Povolí zadání nového tokenu ručně u existující koloběžky."""
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN]
            address = self._config_entry.unique_id
            ble_device = bluetooth.async_ble_device_from_address(self.hass, address, connectable=True)
            if ble_device is None:
                errors["base"] = "cannot_connect"
            else:
                try:
                    scooter = ScooterBluetoothDeviceData(True, token=token)
                    await scooter.initialize_device(ble_device)
                    
                    # Přepis originálního data objektu a reload
                    new_data = dict(self._config_entry.data)
                    new_data[CONF_TOKEN] = token
                    new_data[CONF_AUTH_METHOD] = AUTH_METHOD_TOKEN
                    self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
                    
                    return self.async_create_entry(title="", data=self._config_entry.options)
                except ValueError:
                    errors[CONF_TOKEN] = "invalid_auth"
                except Exception as err:
                    _LOGGER.error("Token update failed: %r", err)
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reauth_token",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors
        )
