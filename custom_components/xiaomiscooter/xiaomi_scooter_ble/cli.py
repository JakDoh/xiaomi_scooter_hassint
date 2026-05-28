#
#     MiAuth - Authenticate and interact with Xiaomi devices over BLE
#     Copyright (C) 2021-2022  Daljeet Nandha
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations
import asyncio
import struct
import dataclasses
import logging

from typing import Any
from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection


from .mi.miclient import MiClient
from .ble.blue import Bleak
from .ble.message import *


_LOGGER = logging.getLogger(__name__)
MAX_ATTEMPTS = 3


@dataclasses.dataclass
class ScooterDevice:
    """Response data with information about the device"""
    miClient = None
    name: str = ""
    friendly_name: str = ""
    mac_address: str = ""
    raw_serial_num: str = ""
    raw_batt_serial_num: str = ""

    manufacturer: str = ""
    model: str = ""
    color: str = ""
    version: str = ""
    serial_num: str = ""
    
    batt_model: str = ""
    batt_serial_num: str = ""
    
    sensors: dict[str, str | float | None] = dataclasses.field(
        default_factory=lambda: {}
    )

    def setMiClient(self, mc: MiClient) -> None:
        self.miClient = mc

    def friendly_name(self) -> str:
        return f"MiScooter_{self.serial_num}"
    
    def decode_scooter_sn(self) -> bool:
        if self.raw_serial_num:
            sn_split = self.raw_serial_num.split("/")
            self.model, self.color, self.version, self.manufacturer = SCOOTER_SN_MAP.get(sn_split[0], ("Unknown", "Unknown", "Unknown","Unknown"))
            self.serial_num = sn_split[1]
            self.name = f"MiScooter_{self.serial_num}"
            return True
        else: return False
    
    def decode_battery_sn(self) -> bool:
        if self.batt_serial_num:
            self.batt_model = BATTERY_SN_MAP.get(self.batt_serial_num[:4], ("Unknown"))
            return True
        else: return False

class ScooterBluetoothDeviceData:
    def __init__(
        self,
        is_metric: bool,
        ble_device: BLEDevice | None = None,
        token: str | bytes | None = None,
    ):
        self._is_metric = is_metric
        self._ble_device = ble_device
        self._token: bytes | None = self._normalize_token(token)
        self.miClient = None
        self.device = None
        super().__init__()

    @staticmethod
    def _normalize_token(token: str | bytes | None) -> bytes | None:
        if token is None:
            return None
        if isinstance(token, bytes):
            return token

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

        return bytes.fromhex(normalized)

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

    def _load_legacy_token(self) -> bytes | None:
        try:
            with open("/home/homeassistant/.homeassistant/mi_token", "rb") as token_file:
                return token_file.read()
        except FileNotFoundError:
            return None

    def _apply_token(self, mc: MiClient) -> None:
        token = self._token or self._load_legacy_token()
        if token is None:
            raise ValueError("Authentication token is not configured")
        mc.token = token



    
    async def _get_initial_sensor_data(
        self, mc: MiClient, device: ScooterDevice
    ) -> ScooterDevice:
        
        _LOGGER.debug("Retrieving: scooter data")
        max_attempts = MAX_ATTEMPTS
        while max_attempts > 0:        
            resp:bytes = await mc.comm(CMD_ESC_DATA_INITIAL)
            if resp is not None:
                resp = struct.unpack(f"<14s6x1H", resp)
                _LOGGER.debug(resp)
                device.raw_serial_num = resp[0].decode('utf-8')
                device.decode_scooter_sn()
                device.version = resp[1]
                break
            max_attempts -= 1  
       
        _LOGGER.debug("Retrieving: battery data")
        max_attempts = MAX_ATTEMPTS
        while max_attempts > 0:
            resp:bytes = await mc.comm(CMD_BMS_DATA_INITIAL)
            if resp is not None:
                resp = struct.unpack(f"<14s4H", resp)
                _LOGGER.debug(resp)
                device.batt_serial_num = resp[0].decode('utf-8')
                device.decode_battery_sn()
                device.sensors["battery_firmware_ver"] = resp[1]
                device.sensors["battery_designed_capacity"] = resp[2]
                device.sensors["battery_full_charge_capacity"] = resp[3]
                device.sensors["battery_nominal_voltage"] = resp[4] / 1e2
                break
            max_attempts -= 1 
        return device

    async def _get_sensor_data_chunked(
        self, mc: MiClient, device: ScooterDevice
    ) -> ScooterDevice:
        
        _LOGGER.debug("Retrieving: scooter data")
        max_attempts = MAX_ATTEMPTS
        while max_attempts > 0:        
            resp:bytes = await mc.comm(CMD_ESC_DATA)
            if resp is not None:
                resp = struct.unpack(f"<3H8xH2x3H4xL8xH4x2L", resp)
                _LOGGER.debug(resp)
                #device.sensors["scooter_error"] = resp[0]
                #device.sensors["scooter_alarm"] = resp[1]
                #device.sensors["scooter_boolean"] = resp[2]
                #device.sensors["scooter_battery_capacity"] = resp[3]
                device.sensors["scooter_remaining_mileage"] = resp[4] / 1e2
                device.sensors["scooter_predicted_mileage"] = resp[5] / 1e2
                device.sensors["scooter_total_mileage"] = resp[7]  / 1e3
                device.sensors["scooter_last_trip_mileage"] = resp[8] / 1e2
                device.sensors["scooter_total_run_time"] = resp[9] / 3600
                device.sensors["scooter_total_ride_time"] = resp[10] / 3600
                break
            max_attempts -= 1  
       
        _LOGGER.debug("Retrieving: battery data")
        max_attempts = MAX_ATTEMPTS
        while max_attempts > 0:
            resp:bytes = await mc.comm(CMD_BMS_DATA_CH1)
            if resp is not None:
                resp = struct.unpack(f"<2HL2B", resp)
                _LOGGER.debug(resp)
                device.sensors["battery_charge_full_cycles"] = resp[0]
                device.sensors["battery_charge_times"] = resp[1]
                device.sensors["battery_accumulative_charge_cap_counter"] = resp[2]
                #device.sensors["battery_overcharge_counter"] = resp[3]
                #device.sensors["battery_overdischarge_counter"] = resp[4]
                break
            max_attempts -= 1 

        max_attempts = MAX_ATTEMPTS
        while max_attempts > 0:
            resp:bytes = await mc.comm(CMD_BMS_DATA_CH2)
            if resp is not None:
                resp = struct.unpack(f"<3H1h1H2b6H", resp)
                _LOGGER.debug(resp)
                
                charging_status = (resp[0] & (BMS_BOOLMARK_CHARGE | BMS_BOOLMARK_CHARGERIN)) != 0
                device.sensors["battery_charging_status"] = "Charging" if charging_status != 0 else "Discharging"  # TODO:unplug charger
                device.sensors["battery_remaining_cap"] = resp[1]
                device.sensors["battery_level"] = resp[2]
                device.sensors["battery_current"] = resp[3] / 1e2 #10mA
                device.sensors["battery_voltage"] = resp[4] / 1e2 #10mV
                device.sensors["battery_temperature_1"] = resp[5] - 20
                device.sensors["battery_temperature_2"] = resp[6] - 20
                #device.sensors["battery_balance_status"] = resp[7]
                #device.sensors["battery_overcharge_status"] = resp[8]
                #device.sensors["battery_overdischarge_status"] = resp[9]
                #device.sensors["batteery_coloumb_couter"] = resp[10]
                #device.sensors["battery_capacity_volume"] = resp[11]
                device.sensors["battery_health"] = resp[12]
                break
            max_attempts -= 1
        
        max_attempts = MAX_ATTEMPTS
        while max_attempts > 0:    
            resp:bytes = await mc.comm(CMD_BMS_DATA_CH3)
            if resp is not None:
                resp = struct.unpack(f"<10H", resp)
                cellCnt = 0
                for cell in resp:
                    if cell != 0:
                        cellCnt += 1
                        device.sensors[f"battery_cell{cellCnt}_voltage"] = cell / 1e3
                break
            max_attempts -= 1
        return device


    async def _get_device_info(
        self, mc: MiClient, device: ScooterDevice
    ) -> ScooterDevice:
        _LOGGER.debug("Retrieving: Scooter serial number")
        resp:bytes = await mc.comm(CMD_ESC_SERIAL_NUMBER)
        if resp:
            device.raw_serial_num = resp.decode('utf-8')
            if device.decode_scooter_sn():
                _LOGGER.debug(f'Scooter serial number {device.serial_num}')

        _LOGGER.debug("Retrieving: Battery serial number")
        resp:bytes = await mc.comm(CMD_BMS_SERIAL_NUMBER)
        if resp is not None:
            device.batt_serial_num = resp.decode('utf-8')
            if device.decode_battery_sn():
                _LOGGER.debug(f'Battery serial number: {device.batt_serial_num}')

    async def _get_sensor_data(
        self, mc: MiClient, device: ScooterDevice
    ) -> ScooterDevice:

        _LOGGER.debug("Retrieving: Battery full charging cycles count")
        resp:bytes = await mc.comm(CMD_BMS_CHARGE_FULL_CYCLES)
        if resp is not None:
            resp = int.from_bytes(resp, signed=False,  byteorder='little')
            device.sensors["battery_charge_full_cycles"] = resp
            _LOGGER.debug(f'Battery full charging cycles count: {resp}')
        
        _LOGGER.debug("Retrieving: Total charge cycles count")
        resp:bytes = await mc.comm(CMD_BMS_CHARGE_COUNT)
        if resp is not None:
            resp = int.from_bytes(resp, signed=False,  byteorder='little')
            device.sensors["battery_charge_cycles"] = resp
            _LOGGER.debug(f'"Total charge cycles count: {resp}')

        _LOGGER.debug("Retrieving: Battery percentage")
        resp:bytes = await mc.comm(CMD_BATT_PERCENT)
        if resp is not None:
            resp = int.from_bytes(resp, signed=True,  byteorder='little')
            device.sensors["battery_level"] = resp
            _LOGGER.debug(f'"Battery percentage: {resp}%')
        
        _LOGGER.debug("Retrieving: voltages")
        print("Retrieving battery pack cell voltages")
        resp:bytes = await mc.comm(CMD_BMS_CELL_VOLTAGES)
        if resp is not None:
            cellCnt = 0
            cell_voltages_tuple = struct.unpack('<HHHHHHHHHH', resp)
            for voltage in cell_voltages_tuple:
                cellCnt = cellCnt+1
                
                _LOGGER.debug(f'Cell {cellCnt}: {(voltage / 1e3)} V')

        resp:bytes = await mc.comm(CMD_BATT_VOLTAGE)
        if resp is not None:
            resp = int.from_bytes(resp, signed=True,  byteorder='little')
            device.sensors["battery_voltage"] = (resp / 1e2)
            _LOGGER.debug(f'Total battery pack voltage{(resp / 1e2)} V')

        _LOGGER.debug("Retrieving: Total distance")
        resp:bytes = await mc.comm(CMD_TOTAL_MILEAGE)
        if resp is not None:
            resp = int.from_bytes(resp, signed=True,  byteorder='little')
            device.sensors["total_distance"] = (resp / 1e3)
            _LOGGER.debug(f'Total distance: {resp/1e3} km')

        _LOGGER.debug("Retrieving: Battery temperatures")
        resp:bytes = await mc.comm(CMD_BATT_TEMP)
        if resp is not None:
            temperatures_tuple = struct.unpack('<BB', resp)
            _LOGGER.debug(f'Temperature 1: {(temperatures_tuple[0] / 1e2)} °C')
            _LOGGER.debug(f'Temperature 2: {(temperatures_tuple[1] / 1e2)} °C')
            device.sensors["battery_temperature_1"] = ((temperatures_tuple[0] + 20)/ 1e2)
            device.sensors["battery_temperature_2"] = ((temperatures_tuple[1] + 20)/ 1e2)

        _LOGGER.debug("Retrieving: Battery current")
        resp:bytes = await mc.comm(CMD_BMS_CURRENT)
        if resp is not None:
            resp = int.from_bytes(resp, signed=True,  byteorder='little')
            device.sensors["battery_current"] = (resp / 1e2)
            _LOGGER.debug(f'Battery current: {resp/1e3} km')

        _LOGGER.debug("Retrieving: Scooter power")
        resp:bytes = await mc.comm(CMD_SCOOTER_POWER)
        if resp is not None:
            resp = int.from_bytes(resp, signed=True,  byteorder='little')
            device.sensors["scooter_power"] = (resp)
            _LOGGER.debug(f'Scooter power: {resp} W')

        _LOGGER.debug("Retrieving: Scooter power")
        resp:bytes = await mc.comm(CMD_BMS_STATUS)
        if resp is not None:
            resp = int.from_bytes(resp, signed=True,  byteorder='little')
            charging_st = (resp & (BMS_BOOLMARK_CHARGE | BMS_BOOLMARK_CHARGERIN)) != 0
            if charging_st :
                device.sensors["scooter_power"] = (charging_st)
            _LOGGER.debug(f'Charger in: {resp}')
            _LOGGER.debug(f'Charging: {resp}')

        return device

    async def register_device(self, ble_device: BLEDevice) -> bool:
        """Connects to the device through BLE and retrieves relevant data"""
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        _LOGGER.debug("Using Mi")
        ble = Bleak(client)
        _LOGGER.debug("Initializing ...")
        mc = MiClient(ble)
        _LOGGER.debug("Connecting ...")
        await ble.connect()
        _LOGGER.debug("Registering")
        try:
            await mc.register()
            if not mc.token:
                raise RuntimeError("Registration did not return a token")

            self._token = mc.token

            _LOGGER.debug("Logging ...")
            await mc.login()
            _LOGGER.debug("Logged ...")
            return True
        except Exception as err:
            _LOGGER.error(
                "Error logging to MiClient: %s",
                err,
            )
            raise
        finally:
            await ble.disconnect()
            
    async def if_token_exist(self) -> bool:
        """Connects to the device through BLE and retrieves relevant data"""
        return bool(self._token or self._load_legacy_token())
            

    async def try_use_token(self, ble_device: BLEDevice) -> bool:
        """Connects to the device through BLE and retrieves relevant data"""
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        _LOGGER.debug("Using Mi")
        ble = Bleak(client)
        _LOGGER.debug("Initializing ...")
        mc = MiClient(ble)
        _LOGGER.debug("Connecting ...")
        await ble.connect()
        _LOGGER.debug("Logging ...")
        try:
            self._apply_token(mc)
            await mc.login()
            _LOGGER.debug("Logged ...")
            return True
        except Exception as err:
            _LOGGER.error(
                "Error logging to MiClient: %s",
                err,
            )
            return False
        finally:
            await ble.disconnect()
        
    async def initialize_device(self, ble_device: BLEDevice) -> ScooterDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        return await self.update_device(ble_device)
    
    async def check_device(self, ble_device: BLEDevice) -> bool:
        """Connects to the device through BLE and retrieves relevant data"""
        try:
            _LOGGER.debug("Checking  device.")    
            client = await establish_connection(BleakClient, ble_device, ble_device.address)
            ble = Bleak(client)
            return await ble.connect()
            
        except Exception as err:
            _LOGGER.debug(f"Error while checking device: {err}")
            return False
        finally:
            if 'ble' in locals():
                await ble.disconnect()

    async def update_device(self, ble_device: BLEDevice) -> ScooterDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        ble = None
        try:
            device = ScooterDevice()
            device.mac_address = ble_device.address
            client = await establish_connection(BleakClient, ble_device, ble_device.address)
            ble = Bleak(client)
            _LOGGER.debug("Initializing ...")
            
            mc = MiClient(ble)
            _LOGGER.debug("Connecting ...")
            await ble.connect()
            _LOGGER.debug("Sucessfully connected.")

            _LOGGER.debug("Loading authentication token ...")
            self._apply_token(mc)
            _LOGGER.debug("Token loaded.")

            _LOGGER.debug("Trying to login ...")
            await mc.login()
            _LOGGER.debug("Succesfully logged.")
        except Exception as err:
            _LOGGER.error("Error logging to MiClient: %s", err)
            raise

        try:
            device = await self._get_initial_sensor_data(mc, device)
            device = await self._get_sensor_data_chunked(mc, device)
        finally:
            if ble is not None:
                await ble.disconnect()

        return device

    async def update_data(self) -> ScooterDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        if self._ble_device is None:
            raise RuntimeError("BLE device is not configured")

        _LOGGER.debug("Updating data.")
        return await self.update_device(self._ble_device)
            

    async def connect(self, ble_device: BLEDevice) -> ScooterBluetoothDeviceData:
        """Connects to the device through BLE and retrieves relevant data"""
        self._ble_device = ble_device
        return self   
    
