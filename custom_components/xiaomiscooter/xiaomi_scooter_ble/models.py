from __future__ import annotations

import dataclasses

from .protocol import BATTERY_SN_MAP, SCOOTER_SN_MAP


@dataclasses.dataclass
class ScooterDevice:
    """Response data with information about the device."""

    name: str = ""
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

    @property
    def friendly_name(self) -> str:
        if self.serial_num:
            return f"MiScooter_{self.serial_num}"
        return self.name or self.mac_address

    def decode_scooter_sn(self) -> bool:
        if not self.raw_serial_num:
            return False

        sn_split = self.raw_serial_num.split("/")
        if len(sn_split) < 2:
            return False

        self.model, self.color, self.version, self.manufacturer = SCOOTER_SN_MAP.get(
            sn_split[0],
            ("Unknown", "Unknown", "Unknown", "Unknown"),
        )
        self.serial_num = sn_split[1]
        self.name = f"MiScooter_{self.serial_num}"
        return True

    def decode_battery_sn(self) -> bool:
        if not self.batt_serial_num:
            return False

        self.batt_model = BATTERY_SN_MAP.get(self.batt_serial_num[:4], "Unknown")
        return True


__all__ = ["ScooterDevice"]