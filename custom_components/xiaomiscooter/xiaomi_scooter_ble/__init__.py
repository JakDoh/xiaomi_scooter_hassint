from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = [
	"ScooterBluetoothDeviceData",
	"ScooterClient",
	"ScooterDevice",
	"ScooterSession",
]

if TYPE_CHECKING:
	from .client import ScooterBluetoothDeviceData, ScooterClient
	from .models import ScooterDevice
	from .session import ScooterSession


def __getattr__(name: str) -> Any:
	if name in {"ScooterBluetoothDeviceData", "ScooterClient"}:
		from .client import ScooterBluetoothDeviceData, ScooterClient

		return {
			"ScooterBluetoothDeviceData": ScooterBluetoothDeviceData,
			"ScooterClient": ScooterClient,
		}[name]
	if name == "ScooterDevice":
		from .models import ScooterDevice

		return ScooterDevice
	if name == "ScooterSession":
		from .session import ScooterSession

		return ScooterSession
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
	return sorted(__all__)
