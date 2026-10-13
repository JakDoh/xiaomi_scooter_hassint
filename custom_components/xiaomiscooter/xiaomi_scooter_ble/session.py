from __future__ import annotations

import logging
import asyncio
from typing import Any

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from .ble.bleak import BleakTransport
from .mi.miclient import MiClient

BLEDevice = Any
_LOGGER = logging.getLogger(__name__)

class ScooterSession:
    """Own the BLE connection lifecycle for one scooter session."""

    def __init__(self, ble_device: BLEDevice) -> None:
        self._ble_device = ble_device
        self._transport: BleakTransport | None = None
        self._mi_client: MiClient | None = None

    async def __aenter__(self) -> ScooterSession:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.disconnect()

    @property
    def mi_client(self) -> MiClient:
        if self._mi_client is None:
            raise RuntimeError("Scooter session is not connected")
        return self._mi_client

    async def connect(self) -> MiClient:
        if self._transport is not None and getattr(self._transport.client, "is_connected", False):
            return self.mi_client

        client = await establish_connection(
            BleakClient,
            self._ble_device,
            self._ble_device.address,
        )
        transport = BleakTransport(client)
        mi_client = MiClient(transport)

        try:
            ready = await transport.connect()
            if not ready:
                raise RuntimeError("Required Xiaomi scooter GATT characteristics were not discovered")
        except Exception:
            await transport.disconnect()
            raise

        self._transport = transport
        self._mi_client = mi_client
        _LOGGER.debug("Scooter session connected for %s", self._ble_device.address)
        return mi_client

    async def disconnect(self) -> None:
        transport = self._transport
        self._transport = None
        self._mi_client = None

        if transport is not None:
            await transport.disconnect()

    async def register(self) -> bytes:
        mi_client = await self.connect()
        try:
            token = await mi_client.register()
        except TimeoutError:
            _LOGGER.warning(">>> PLEASE PRESS THE SCOOTER POWER BUTTON NOW! <<<")
            await self.disconnect()
            await asyncio.sleep(5.0)
            
            _LOGGER.debug("Reconnecting for auth pass 2 (Trick 17)")
            mi_client = await self.connect()
            token = await mi_client.register()
            
        if not token:
            raise RuntimeError("Registration did not return a valid token")
            
        return token

    async def login(self, token: bytes) -> MiClient:
        mi_client = await self.connect()
        mi_client.token = token
        await mi_client.login()
        return mi_client