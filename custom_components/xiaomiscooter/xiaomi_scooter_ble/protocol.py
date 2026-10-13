from __future__ import annotations

import struct
from typing import Any

ESC = "55AA 03 20 01"
BMS = "55AA 03 22 01"

CMD_ESC_DATA_INITIAL = f"{ESC} 10 16"
CMD_ESC_DATA = f"{ESC} 1B 36"
CMD_ESC_DATA_EXT1 = f"{ESC} 70 1C"
CMD_ESC_DATA_EXT2 = f"{ESC} B0 20"

CMD_BMS_DATA_INITIAL = f"{BMS} 10 16"
CMD_BMS_DATA_CH1 = f"{BMS} 1B 0A"
CMD_BMS_DATA_CH2 = f"{BMS} 30 18"
CMD_BMS_DATA_CH3 = f"{BMS} 40 14"

CMD_SCOOTER_POWER = f"{BMS} BD 02"
CMD_BOOLEAN_STATE = f"{BMS} B2 02"
CMD_SPEED = f"{ESC} 26 02"
CMD_OPER_MODE = f"{ESC} 75 02"
CMD_ESC_SERIAL_NUMBER = f"{ESC} 10 0e"
CMD_REMAIN_MILEAGE = f"{ESC} 24 02"
CMD_PREDICTED_MILEAGE = f"{ESC} 25 02"
CMD_TOTAL_MILEAGE = f"{ESC} 29 04"
CMD_TRIP_MILEAGE = f"{ESC} 2F 02"
CMD_CURRENT_MILEAGE = f"{ESC} 2F 02"
CMD_TOT_OPER_TIME = f"{ESC} 32 04"
CMD_TOT_RIDE_TIME = f"{ESC} 34 04"
CMD_TRIP_OPER_TIME = f"{ESC} 3A 04"
CMD_TRIP_RIDE_TIME = f"{ESC} 3B 04"
CMD_BATT_PERCENT = f"{ESC} 22 02"
CMD_BATT_VOLTAGE = f"{ESC} 48 02"
CMD_BATT_CURRENT = f"{ESC} 50 02"
CMD_BATT_TEMP = f"{ESC} 3f 04"
CMD_ESC_SUPPLY_VOLTAGE = f"{ESC} 47 02"
CMD_MOSFET_TEMP = f"{ESC} 41 02"
CMD_FRAME_TEMP1 = f"{ESC} BB 02"
CMD_FRAME_TEMP2 = f"{ESC} 3E 02"
CMD_BMS_SERIAL_NUMBER = f"{BMS} 10 0E"
CMD_BMS_STATUS = f"{BMS} 30 02"
CMD_BMS_CELL_VOLTAGES = f"{BMS} 40 14"
CMD_BMS_TEMPERATURES = f"{BMS} 35 04"
CMD_BMS_CURRENT = f"{BMS} 33 02"
CMD_BMS_VOLTAGE = f"{BMS} 34 02"
CMD_BMS_BALANCE_ST = f"{BMS} 36 02"
CMD_BMS_FIRMWARE_VERSION = f"{BMS} 17 02"
CMD_BMS_FACTORY_CAPACITY = f"{BMS} 18 02"
CMD_BMS_MANUFACTURE_DATE = f"{BMS} 20 02"
CMD_BMS_CHARGE_FULL_CYCLES = f"{BMS} 1B 02"
CMD_BMS_CHARGE_COUNT = f"{BMS} 1C 02"
CMD_BMS_HEALTH = f"{BMS} 3B 02"

BMS_BOOLMARK_PASSWORD = 0x0001
BMS_BOOLMARK_ACT = 0x0002
BMS_BOOLMARK_CHG_PROTECT = 0x0004
BMS_BOOLMARK_CMOS = 0x0008
BMS_BOOLMARK_WRITE_CMD = 0x0010
BMS_BOOLMARK_DISCHARGE = 0x0020
BMS_BOOLMARK_CHARGE = 0x0040
BMS_BOOLMARK_CHARGERIN = 0x0080
BMS_BOOLMARK_DISOVER = 0x0100
BMS_BOOLMARK_CHGOVER = 0x0200
BMS_BOOLMARK_VOERTEMP = 0x0400
BMS_BOOLMARK_TEST_MODE = 0x0800

SCOOTER_SN_MAP = {
    "13678": ("M365", "White", "China version", "Ninebot"),
    "13679": ("M365", "Black", "China version", "Ninebot"),
    "16057": ("M187", None, None, None),
    "16133": ("M365", "Black", "European version", "Ninebot"),
    "21074": ("M365", "Black", "European version", "Ninebot"),
    "16132": ("M365", "White", "European version", "Ninebot"),
    "21073": ("M365", "White", "European version", "Ninebot"),
    "16349": ("M365", "Black", "American version", "Ninebot"),
    "16348": ("M365", "White", "American version", "Ninebot"),
    "18832": ("M365 Pro", None, "Chinese version", "Ninebot"),
    "21886": ("M365 Pro", None, "European version", "Ninebot"),
    "30371": ("Mi Electric Scooter Pro 2", None, "Mercedes Edition", "Ninebot"),
    "26354": ("Mi Electric Scooter Pro 2", None, "European version", "Ninebot"),
    "25699": ("Mi Electric Scooter 1S", None, None, "Ninebot"),
    "25702": ("Mi Electric Scooter Lite", None, "German version", "Ninebot"),
    "25600": ("Mi Electric Scooter Lite", None, "Global version", "Ninebot"),
    "30807": ("Mi Electric Scooter 3", "Black/Blue", None, "Ninebot"),
    "30806": ("Mi Electric Scooter 3", "White/Orange", None, "Ninebot"),
    "46442": ("Mi Electric Scooter 4", None, "German version", "Brightway (Navee)"),
    "46443": ("Mi Electric Scooter 4", None, "European version", "Brightway (Navee)"),
    "46441": ("Mi Electric Scooter 4", None, "Global version", "Brightway (Navee)"),
    "46440": ("Mi Electric Scooter 4", None, "Italian version", "Brightway (Navee)"),
    "46416": ("Mi Electric Scooter 4 Lite", None, "German version", "Brightway (Navee)"),
    "46419": ("Mi Electric Scooter 4 Lite", None, "European version", "Brightway (Navee)"),
    "46415": ("Mi Electric Scooter 4 Lite", None, "Global version", "Brightway (Navee)"),
    "46418": ("Mi Electric Scooter 4 Lite", None, "French version", "Brightway (Navee)"),
    "46417": ("Mi Electric Scooter 4 Lite", None, "Italian version", "Brightway (Navee)"),
    "40595": ("Mi Electric Scooter 4 Ultra", None, "German version", "Brightway (Navee)"),
    "37829": ("Mi Electric Scooter 4 Ultra", None, "Global version", "Brightway (Navee)"),
    "40594": ("Mi Electric Scooter 4 Ultra", None, "French version", "Brightway (Navee)"),
    "45482": ("Mi Electric Scooter 4 Go", None, "Global version", "Ninebot"),
    "45480": ("Mi Electric Scooter 4 Go", None, "French version", "Ninebot"),
    "45481": ("Mi Electric Scooter 4 Go", None, "Italian version", "Ninebot"),
    "35802": ("Mi Electric Scooter 4 Pro", None, "Global version", "Ninebot"),
    "38191": ("Mi Electric Scooter 4 Pro", None, "Global version", "Ninebot"),
    "35803": ("Mi Electric Scooter 4 Pro", None, "British version", "Ninebot"),
    "35804": ("Mi Electric Scooter 4 Pro", None, "French version", "Ninebot"),
    "35806": ("Mi Electric Scooter 4 Pro", None, "German version", "Ninebot"),
    "41839": ("Mi Electric Scooter 4 Pro", None, "Italian version", "Ninebot"),
}

BATTERY_SN_MAP = {
    "3JBG": "Mi Electric Scooter Pro 2 batteryReinforced soldering & welds. First version (V1)",
    "3JCG": "Mi Electric Scooter Pro 2 battery. Reinforced welds on the cells. Second version (V2)",
    "3JEE": "Mi Electric Scooter Pro 2 battery. Reinforced soldering & welds. Third version (V3)",
    "3GBG": "Mi Electric Scooter Lite battery. Non-reinforced welds and soldering.",
    "4XFG": "Mi Electric Scooter Pro 2 battery. Reinforced soldering & welds.",
    "BFAG": "Mi Electric Scooter Pro 2 battery.",
    "BFFG": "Mi Electric Scooter Pro 2 battery. EVE cells, limited charge.",
    "4XBG": "Mi Electric Scooter Pro 1 battery (EU version). Reinforced soldering & welds.",
    "4XCG": "Mi Electric Scooter Pro 1 battery (EU version). Reinforced soldering & welds.",
    "4XAA": "Mi Electric Scooter Pro 1 battery (CN version). Reinforced soldering & welds.",
    "2JEG": "Mi Electric Scooter 1S battery (EU version) with resistors on the BMS.",
    "2JAE": "Mi Electric Scooter 1S battery with major changes to the BMS and rails (late 2020).",
    "2JBE": "Mi Electric Scooter 1S battery.",
    "2JAG": "M365 battery with EVE cells, CN version.",
    "2JCG": "M365 battery with EVE cells, EU version.",
    "0JEG": "M365 1S battery with LG M26 cells.",
}


def _decode_ascii(data: bytes) -> str:
    return data.decode("utf-8").rstrip("\x00")


def decode_initial_scooter_data(data: bytes) -> dict[str, Any]:
    raw_serial_num, version = struct.unpack("<14s6x1H", data)
    return {
        "raw_serial_num": _decode_ascii(raw_serial_num),
        "version": version,
    }


def decode_initial_battery_data(data: bytes) -> dict[str, Any]:
    batt_serial_num, firmware_ver, designed_capacity, full_charge_capacity, nominal_voltage = struct.unpack(
        "<14s4H",
        data,
    )
    return {
        "batt_serial_num": _decode_ascii(batt_serial_num),
        "battery_firmware_ver": firmware_ver,
        "battery_designed_capacity": designed_capacity,
        "battery_full_charge_capacity": full_charge_capacity,
        "battery_nominal_voltage": nominal_voltage / 1e2,
    }


def decode_runtime_scooter_data(data: bytes) -> dict[str, float]:
    values = struct.unpack("<3H8xH2x3H4xL8xH4x2L", data)
    return {
        "scooter_remaining_mileage": values[4] / 1e2,
        "scooter_predicted_mileage": values[5] / 1e2,
        "scooter_total_mileage": values[7] / 1e3,
        "scooter_last_trip_mileage": values[8] / 1e2,
        "scooter_total_run_time": values[9] / 3600,
        "scooter_total_ride_time": values[10] / 3600,
    }


def decode_runtime_battery_data_ch1(data: bytes) -> dict[str, int]:
    charge_full_cycles, charge_times, accumulative_charge_cap_counter, _, _ = struct.unpack("<2HL2B", data)
    return {
        "battery_charge_full_cycles": charge_full_cycles,
        "battery_charge_times": charge_times,
        "battery_accumulative_charge_cap_counter": accumulative_charge_cap_counter,
    }


def decode_runtime_battery_data_ch2(data: bytes) -> dict[str, str | float | int]:
    values = struct.unpack("<3H1h1H2b6H", data)
    charging_status = (values[0] & (BMS_BOOLMARK_CHARGE | BMS_BOOLMARK_CHARGERIN)) != 0
    return {
        "battery_charging_status": "Charging" if charging_status else "Discharging",
        "battery_remaining_cap": values[1],
        "battery_level": values[2],
        "battery_current": values[3] / 1e2,
        "battery_voltage": values[4] / 1e2,
        "battery_temperature_1": values[5] - 20,
        "battery_temperature_2": values[6] - 20,
        "battery_health": values[12],
    }


def decode_runtime_battery_cell_data(data: bytes) -> dict[str, float]:
    sensors: dict[str, float] = {}
    # Pevné přiřazení indexu 1 až 10 bez ohledu na nulové hodnoty
    for idx, cell_voltage in enumerate(struct.unpack("<10H", data), start=1):
        if cell_voltage > 0:
            sensors[f"battery_cell{idx}_voltage"] = cell_voltage / 1e3
    return sensors


__all__ = [
    "BATTERY_SN_MAP",
    "BMS_BOOLMARK_ACT",
    "BMS_BOOLMARK_CHARGE",
    "BMS_BOOLMARK_CHARGERIN",
    "BMS_BOOLMARK_CHGOVER",
    "BMS_BOOLMARK_CHG_PROTECT",
    "BMS_BOOLMARK_CMOS",
    "BMS_BOOLMARK_DISCHARGE",
    "BMS_BOOLMARK_DISOVER",
    "BMS_BOOLMARK_PASSWORD",
    "BMS_BOOLMARK_TEST_MODE",
    "BMS_BOOLMARK_VOERTEMP",
    "BMS_BOOLMARK_WRITE_CMD",
    "CMD_BATT_CURRENT",
    "CMD_BATT_PERCENT",
    "CMD_BATT_TEMP",
    "CMD_BATT_VOLTAGE",
    "CMD_BMS_BALANCE_ST",
    "CMD_BMS_CELL_VOLTAGES",
    "CMD_BMS_CHARGE_COUNT",
    "CMD_BMS_CHARGE_FULL_CYCLES",
    "CMD_BMS_CURRENT",
    "CMD_BMS_DATA_CH1",
    "CMD_BMS_DATA_CH2",
    "CMD_BMS_DATA_CH3",
    "CMD_BMS_DATA_INITIAL",
    "CMD_BMS_FACTORY_CAPACITY",
    "CMD_BMS_FIRMWARE_VERSION",
    "CMD_BMS_HEALTH",
    "CMD_BMS_MANUFACTURE_DATE",
    "CMD_BMS_SERIAL_NUMBER",
    "CMD_BMS_STATUS",
    "CMD_BMS_TEMPERATURES",
    "CMD_BMS_VOLTAGE",
    "CMD_BOOLEAN_STATE",
    "CMD_CURRENT_MILEAGE",
    "CMD_ESC_DATA",
    "CMD_ESC_DATA_EXT1",
    "CMD_ESC_DATA_EXT2",
    "CMD_ESC_DATA_INITIAL",
    "CMD_ESC_SERIAL_NUMBER",
    "CMD_ESC_SUPPLY_VOLTAGE",
    "CMD_FRAME_TEMP1",
    "CMD_FRAME_TEMP2",
    "CMD_MOSFET_TEMP",
    "CMD_OPER_MODE",
    "CMD_PREDICTED_MILEAGE",
    "CMD_REMAIN_MILEAGE",
    "CMD_SCOOTER_POWER",
    "CMD_SPEED",
    "CMD_TOT_OPER_TIME",
    "CMD_TOT_RIDE_TIME",
    "CMD_TOTAL_MILEAGE",
    "CMD_TRIP_MILEAGE",
    "CMD_TRIP_OPER_TIME",
    "CMD_TRIP_RIDE_TIME",
    "SCOOTER_SN_MAP",
    "decode_initial_battery_data",
    "decode_initial_scooter_data",
    "decode_runtime_battery_cell_data",
    "decode_runtime_battery_data_ch1",
    "decode_runtime_battery_data_ch2",
    "decode_runtime_scooter_data",
]