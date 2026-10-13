from __future__ import annotations

import logging
from typing import Any, Callable

from .mi.miclient import MiClient
from .models import ScooterDevice
from .protocol import (
    CMD_BMS_DATA_CH1,
    CMD_BMS_DATA_CH2,
    CMD_BMS_DATA_CH3,
    CMD_BMS_DATA_INITIAL,
    CMD_ESC_DATA,
    CMD_ESC_DATA_INITIAL,
    decode_initial_battery_data,
    decode_initial_scooter_data,
    decode_runtime_battery_cell_data,
    decode_runtime_battery_data_ch1,
    decode_runtime_battery_data_ch2,
    decode_runtime_scooter_data,
)
from .session import ScooterSession

BLEDevice = Any

_LOGGER = logging.getLogger(__name__)
MAX_ATTEMPTS = 3

class ScooterBluetoothDeviceData:
    def __init__(
        self,
        is_metric: bool,
        ble_device: BLEDevice | None = None,
        token: str | bytes | None = None,
        token_provider: Callable[[], str | bytes | None] | None = None,
    ):
        self._is_metric = is_metric
        self._ble_device = ble_device
        self._token: bytes | None = self._normalize_token(token)
        self._token_provider = token_provider
        self.miClient = None
        self.device = None
        super().__init__()

    @staticmethod
    def _normalize_token(token: str | bytes | None) -> bytes | None:
        if token is None:
            return None
        if isinstance(token, bytes):
            return token[:12] if len(token) > 12 else token

        normalized = (
            token.replace("0x", "")
            .replace("0X", "")
            .replace(" ", "")
            .replace(":", "")
            .replace("-", "")
            .strip()
        )
        if not normalized:
            return None

        raw_token = bytes.fromhex(normalized)
        return raw_token[:12] if len(raw_token) > 12 else raw_token

    def set_runtime_data(
        self,
        ble_device: BLEDevice | None = None,
        token: str | bytes | None = None,
    ) -> None:
        if ble_device is not None:
            self._ble_device = ble_device
        if token is not None:
            self._token = self._normalize_token(token)

    def token_hex(self) -> str | None:
        if self._token is None:
            return None
        return self._token.hex()

    def _resolve_token(self) -> bytes | None:
        if self._token is not None:
            return self._token
        if self._token_provider is None:
            return None
        return self._normalize_token(self._token_provider())

    def _require_token(self) -> bytes:
        token = self._resolve_token()
        if token is None:
            raise ValueError("Authentication token is not configured")
        return token

    async def _get_initial_sensor_data(self, mc: MiClient, device: ScooterDevice) -> ScooterDevice:
        _LOGGER.debug("Retrieving: scooter data")
        for _ in range(MAX_ATTEMPTS):
            resp: bytes | None = await mc.comm(CMD_ESC_DATA_INITIAL)
            if resp:
                try:
                    parsed = decode_initial_scooter_data(resp)
                    device.raw_serial_num = parsed["raw_serial_num"]
                    device.decode_scooter_sn()
                    device.version = parsed["version"]
                    break
                except Exception as e:
                    _LOGGER.debug("Failed to decode initial scooter data: %r", e)

        _LOGGER.debug("Retrieving: battery data")
        for _ in range(MAX_ATTEMPTS):
            resp: bytes | None = await mc.comm(CMD_BMS_DATA_INITIAL)
            if resp:
                try:
                    parsed = decode_initial_battery_data(resp)
                    device.batt_serial_num = parsed.pop("batt_serial_num")
                    device.decode_battery_sn()
                    device.sensors.update(parsed)
                    break
                except Exception as e:
                    _LOGGER.debug("Failed to decode initial BMS data: %r", e)
        return device

    async def _get_sensor_data_chunked(self, mc: MiClient, device: ScooterDevice) -> ScooterDevice:
        _LOGGER.debug("Retrieving runtime data")
        commands = [
            (CMD_ESC_DATA, decode_runtime_scooter_data),
            (CMD_BMS_DATA_CH1, decode_runtime_battery_data_ch1),
            (CMD_BMS_DATA_CH2, decode_runtime_battery_data_ch2),
            (CMD_BMS_DATA_CH3, decode_runtime_battery_cell_data),
        ]
        for cmd, decoder in commands:
            for _ in range(MAX_ATTEMPTS):
                resp: bytes | None = await mc.comm(cmd)
                if resp:
                    try:
                        device.sensors.update(decoder(resp))
                        break
                    except Exception as e:
                        _LOGGER.debug("Failed to decode payload for cmd %s: %r", cmd, e)
        return device

    async def register_device(self, ble_device: BLEDevice) -> bool:
        try:
            async with ScooterSession(ble_device) as session:
                self._token = await session.register()
            return True
        except Exception as err:
            _LOGGER.error("Error logging to MiClient: %r", err)
            raise

    async def if_token_exist(self) -> bool:
        return bool(self._resolve_token())

    async def try_use_token(self, ble_device: BLEDevice) -> bool:
        try:
            async with ScooterSession(ble_device) as session:
                self.miClient = await session.login(self._require_token())
            return True
        except Exception as err:
            _LOGGER.error("Error logging to MiClient: %r", err)
            return False

    async def initialize_device(self, ble_device: BLEDevice) -> ScooterDevice:
        return await self.update_device(ble_device)

    async def check_device(self, ble_device: BLEDevice) -> bool:
        try:
            _LOGGER.debug("Checking device.")
            async with ScooterSession(ble_device):
                return True
        except Exception as err:
            _LOGGER.debug("Error while checking device: %r", err)
            return False

    async def update_device(self, ble_device: BLEDevice) -> ScooterDevice:
        try:
            device = ScooterDevice()
            device.mac_address = ble_device.address
            async with ScooterSession(ble_device) as session:
                mc = await session.login(self._require_token())
                self.miClient = mc
                device = await self._get_initial_sensor_data(mc, device)
                device = await self._get_sensor_data_chunked(mc, device)
                
                # ULOŽENÍ A VYSTAVENÍ TOKENU DO SENZORŮ HA
                device.sensors["mitoken"] = self.token_hex() or "N/A"
                
        except Exception as err:
            _LOGGER.error("Error updating device data: %r", err)
            raise Exception(f"Device data update failed: {err!r}") from err
        return device

    async def update_data(self) -> ScooterDevice:
        if self._ble_device is None:
            raise RuntimeError("BLE device is not configured")
        return await self.update_device(self._ble_device)

    async def connect(self, ble_device: BLEDevice) -> ScooterBluetoothDeviceData:
        self._ble_device = ble_device
        return self

ScooterClient = ScooterBluetoothDeviceData

__all__ = [
    "ScooterBluetoothDeviceData",
    "ScooterClient",
    "ScooterDevice",
    "ScooterSession",
]