import asyncio
from bleak import BleakClient, BleakScanner
from .base import BLEBase
from .uuids import UUIDS
import logging
_LOGGER = logging.getLogger(__name__)

class Bleak(BLEBase):
    def __init__(self, client: BleakClient):
        self.client = client
        self.handler = None

        self.channels = {
            UUIDS.AVDTP: None,
            UUIDS.UPNP: None,
            UUIDS.TX: None,
            UUIDS.RX: None,
        }

        BLEBase.__init__(self)

    async def handleNotification(self, sender: int, data: bytearray):
        if self.handler is None:
            raise Exception("BLE set handler first")
        if not data:
            return
        await self.handler(data)

    def set_handler(self, handler):
        self.handler = handler

    async def enable_notify(self, ch):
        await self.client.start_notify(ch, self.handleNotification)
        await asyncio.sleep(0.1)

    async def disable_notify(self, ch):
        await self.client.stop_notify(ch)
        await asyncio.sleep(0.1)

    async def write(self, ch, data):
        _LOGGER.debug(f'Write data: {data} to char: {ch}')
        await self.client.write_gatt_char(ch, data)

    async def write_chunked(self, ch, data, chunk_size=20):
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            await self.write(ch, chunk)

    async def write_parcel(self, ch, data, chunk_size=18):
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunk = bytes([i // chunk_size + 1, 0]) + chunk
            await self.write(ch, chunk)

    async def connect(self)-> bool: 
        await self.client.connect()
        services = self.client.services

        for service in services:
            if service.uuid == UUIDS.AUTH:
                for char in service.characteristics:
                    if char.uuid == UUIDS.AVDTP:
                        self.channels[UUIDS.AVDTP] = char
                    elif char.uuid == UUIDS.UPNP:
                        self.channels[UUIDS.UPNP] = char

            elif service.uuid == UUIDS.UART:
                for char in service.characteristics:
                    if char.uuid == UUIDS.TX:
                        self.channels[UUIDS.TX] = char
                    elif char.uuid == UUIDS.RX:
                        self.channels[UUIDS.RX] = char

        if not any(value is None for value in self.channels.values()):
            await self.enable_notify(self.channels[UUIDS.AVDTP])
            await self.enable_notify(self.channels[UUIDS.UPNP])
            await self.enable_notify(self.channels[UUIDS.RX])
            return True
        else:
            return False

        

    async def disconnect(self):
        if not getattr(self.client, "is_connected", False):
            return

        for channel_uuid in (UUIDS.RX, UUIDS.UPNP, UUIDS.AVDTP):
            channel = self.channels.get(channel_uuid)
            if channel is None:
                continue

            try:
                await self.disable_notify(channel)
            except Exception as err:
                _LOGGER.debug("Failed to stop notify on %s: %s", channel_uuid, err)

        await self.client.disconnect()
        _LOGGER.debug("Device disconnected")


    async def wait_notify(self, secs=2.0):
        await asyncio.sleep(secs)
    