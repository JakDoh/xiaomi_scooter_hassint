from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict

from .xiaomi_scooter_ble import ScooterBluetoothDeviceData, ScooterDevice
from bleak import BleakError
import voluptuous as vol
from homeassistant import exceptions
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothServiceInfo,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_ADDRESS

from .const import (
    AUTH_METHOD_BUTTON,
    AUTH_METHOD_TOKEN,
    CONF_AUTH_METHOD,
    CONF_TOKEN,
    DOMAIN,
    SCOOTER_LIST,
)

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class Discovery:
    """A discovered bluetooth device."""

    name: str
    discovery_info: BluetoothServiceInfo
    device: ScooterDevice | None


class ScooterDeviceAuthError(exceptions.HomeAssistantError):
    """Custom error class for device updates."""

class ScooterDeviceUpdateError(exceptions.HomeAssistantError):
    """Custom error class for device updates."""

class ScooterDeviceCheckError(exceptions.HomeAssistantError):
    """Custom error class for device updates."""

class ScooterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xiaomi BLE."""

    VERSION = 1
    AUTH_METHOD_OPTIONS = {
        AUTH_METHOD_BUTTON: "Scooter button pairing",
        AUTH_METHOD_TOKEN: "Existing token / key",
    }
    
    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
    #     """Return the options flow."""
    #     return OptionsFlowHandler(config_entry)
    

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: Discovery | None = None
        self._discovered_devices: dict[str, Discovery] = {}

    async def _get_device_data(
        self,
        discovery_info: BluetoothServiceInfo,
        token: str | None = None,
    ) -> ScooterDevice:
        ble_device = bluetooth.async_ble_device_from_address(self.hass, discovery_info.address, connectable=True)

        if ble_device is None:
            _LOGGER.debug("no ble_device in _get_device_data")
            raise ScooterDeviceUpdateError("No ble_device")

        try:
            scooter = ScooterBluetoothDeviceData(True, token=token)
            data = await scooter.initialize_device(ble_device)
        except ValueError as err:
            _LOGGER.error("Invalid token for %s: %s", discovery_info.address, err)
            raise ScooterDeviceAuthError("Invalid token") from err
        except BleakError as err:
            _LOGGER.error(f"Error connecting to and getting data from {discovery_info.address}: {err}")
            raise ScooterDeviceUpdateError("Failed getting device data") from err
        except Exception as err:
            _LOGGER.error(f"Unknown error occurred from {discovery_info.address}: {err}")
            raise err
        return data
    
    async def _register_device_with_button(self, discovery_info: BluetoothServiceInfo) -> str:
        ble_device = bluetooth.async_ble_device_from_address(self.hass, discovery_info.address, connectable=True)

        if ble_device is None:
            _LOGGER.debug("no ble_device in _get_device_data")
            raise ScooterDeviceAuthError("No ble_device")
        scooter = ScooterBluetoothDeviceData(True)

        try:
            await scooter.register_device(ble_device)
            token = scooter.token_hex()
            if token is None:
                raise ScooterDeviceAuthError("No token received")
        except BleakError as err:
            _LOGGER.error(f"Error connecting to and getting data from {discovery_info.address}: {err}")
            raise ScooterDeviceAuthError("Failed getting device data") from err
        except Exception as err:
            _LOGGER.error(f"Unknown error occurred from {discovery_info.address}: {err}")
            raise err
        return token
    
    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfo) -> FlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug(f"Discovered BT device: {discovery_info}")
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        name = discovery_info.name or discovery_info.address
        self.context["title_placeholders"] = {"name": name, "type": "Xiaomi Scooter"}
        _LOGGER.debug(f"Titled device: {name}")
        self._discovered_device = Discovery(name, discovery_info, None)

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Confirm discovery."""
        _LOGGER.debug("Entering async_step_bluetooth_confirm")
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
        """Confirm authentification."""
        _LOGGER.debug("Entering auth confirmation")
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
                    data={
                        CONF_AUTH_METHOD: AUTH_METHOD_BUTTON,
                        CONF_TOKEN: token,
                    },
                )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="auth_confirm",
            description_placeholders=self.context["title_placeholders"],
            errors=errors,
        )

    async def async_step_auth_token(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual token entry."""
        _LOGGER.debug("Entering async_step_auth_token")
        errors: Dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]
            try:
                device = await self._get_device_data(
                    self._discovered_device.discovery_info,
                    token=token,
                )
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
                    data={
                        CONF_AUTH_METHOD: AUTH_METHOD_TOKEN,
                        CONF_TOKEN: token,
                    },
                )

        return self.async_show_form(
            step_id="auth_token",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOKEN): str,
                }
            ),
            description_placeholders=self.context["title_placeholders"],
            errors=errors,
        )
    
    async def async_step_auth_method(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select auth method."""
        _LOGGER.debug("Entering async_step_auth_method")
        errors: Dict[str, str] = {}
        if user_input is not None:
            method = user_input[CONF_AUTH_METHOD]
            _LOGGER.debug(f"Auth method : {method}")
            if method == AUTH_METHOD_BUTTON:
                return await self.async_step_auth_confirm()
            if method == AUTH_METHOD_TOKEN:
                return await self.async_step_auth_token()
            
        return self.async_show_form(
            step_id="auth_method",
            data_schema=vol.Schema(
                {   
                    vol.Required(
                        CONF_AUTH_METHOD,
                        default=AUTH_METHOD_BUTTON,
                    ): vol.In(self.AUTH_METHOD_OPTIONS)
                }
            ),
            description_placeholders=self.context["title_placeholders"],
            errors=errors
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the user step to pick discovered device."""
        _LOGGER.debug("Entering async_step_user")
        errors: Dict[str, str] = {}
        if user_input is not None:
            _LOGGER.debug("user_input is not None")
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            discovery = self._discovered_devices[address]

            self.context["title_placeholders"] = {"name": discovery.name}

            self._discovered_device = discovery
            return await self.async_step_auth_method()
            
            

        current_addresses = self._async_current_ids()

        for discovery_info in list(async_discovered_service_info(self.hass, connectable = True)).copy():
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue

            _LOGGER.debug(f"Name: {discovery_info.name}")
            _LOGGER.debug(f"Address: {discovery_info.address}")
            _LOGGER.debug(f"Manufacturer data: {discovery_info.manufacturer_data}")
            _LOGGER.debug(f"Service data: {discovery_info.service_data}")
            
            name = discovery_info.name or ""
            not_known_name = not any(substring in name for substring in SCOOTER_LIST)
            if not_known_name: continue
            
            self.context["title_placeholders"] = {"name": name, "type": "Xiaomi Scooter"}
            _LOGGER.debug(f"Titled device: {name}")
            self._discovered_devices[address] = Discovery(name, discovery_info, device=None)
                

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        titles = {
            address: discovery.name
            for (address, discovery) in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(titles),
                },
            ),
            description_placeholders={"description": "Test", "title": "Titulek"},
            errors=errors
        )
# class OptionsFlowHandler(OptionsFlow):
#     """Handle a option flow for Yeelight."""

#     def __init__(self, config_entry: ConfigEntry) -> None:
#         """Initialize the option flow."""
#         self._config_entry = config_entry

#     async def async_step_init(self, user_input=None):
#         """Handle the initial step."""
#         data = self._config_entry.data
#         options = self._config_entry.options
#         detected_model = data.get(CONF_DETECTED_MODEL)
#         model = options[CONF_MODEL] or detected_model

#         if user_input is not None:
#             return self.async_create_entry(
#                 title="", data={CONF_MODEL: model, **options, **user_input}
#             )

#         schema_dict = {}
#         known_models = get_known_models()
#         if is_unknown_model := model not in known_models:
#             known_models.insert(0, model)

#         if is_unknown_model or model != detected_model:
#             schema_dict.update(
#                 {
#                     vol.Optional(CONF_MODEL, default=model): vol.In(known_models),
#                 }
#             )
#         schema_dict.update(
#             {
#                 vol.Required(
#                     CONF_TRANSITION, default=options[CONF_TRANSITION]
#                 ): cv.positive_int,
#                 vol.Required(CONF_MODE_MUSIC, default=options[CONF_MODE_MUSIC]): bool,
#                 vol.Required(
#                     CONF_SAVE_ON_CHANGE, default=options[CONF_SAVE_ON_CHANGE]
#                 ): bool,
#                 vol.Required(
#                     CONF_NIGHTLIGHT_SWITCH, default=options[CONF_NIGHTLIGHT_SWITCH]
#                 ): bool,
#             }
#         )

#         return self.async_show_form(
#             step_id="init",
#             data_schema=vol.Schema(schema_dict),
#         )


#      async def async_step_init(
#         self, user_input: dict[str, Any] | None = None
#     ) -> FlowResult:
#         """Handle options flow."""
#         if user_input is not None:
#             self.hass.config_entries.async_update_entry(
#                 self.config_entry,
#                 data={
#                     **self.config_entry.data,
#                     CONF_STATIONS: user_input.pop(CONF_STATIONS),
#                 },
#             )
#             return self.async_create_entry(title="", data=user_input)

#         nearby_stations = await async_get_nearby_stations(
#             self.hass, self.config_entry.data
#         )
#         if stations := nearby_stations.get("stations"):
#             for station in stations:
#                 self._stations[station["id"]] = (
#                     f"{station['brand']} {station['street']} {station['houseNumber']} -"
#                     f" ({station['dist']}km)"
#                 )

#         # add possible extra selected stations from import
#         for selected_station in self.config_entry.data[CONF_STATIONS]:
#             if selected_station not in self._stations:
#                 self._stations[selected_station] = f"id: {selected_station}"

#         return self.async_show_form(
#             step_id="init",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(
#                         CONF_SHOW_ON_MAP,
#                         default=self.config_entry.options[CONF_SHOW_ON_MAP],
#                     ): bool,
#                     vol.Required(
#                         CONF_STATIONS, default=self.config_entry.data[CONF_STATIONS]
#                     ): cv.multi_select(self._stations),
#                 }
#             ),
#         )    
    
