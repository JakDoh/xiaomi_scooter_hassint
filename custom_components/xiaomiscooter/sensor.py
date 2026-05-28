"""Support for airthings ble sensors."""
from __future__ import annotations

import logging

from .xiaomi_scooter_ble import ScooterDevice

from homeassistant import config_entries
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfLength,
    UnitOfTime,
)
from homeassistant.helpers.entity_registry import async_get
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSORS_MAPPING_TEMPLATE: dict[str, SensorEntityDescription] = {
    
    # device.sensors["SCT_BTPASSWORD"] = resp[1]
    # device.sensors["SCT_FW_VER"] = resp[2]
    # device.sensors["SCT_ERROR"] = resp[3]
    # device.sensors["SCT_ALARM"] = resp[4]
    # device.sensors["SCT_BOOL"] = resp[5]
    # device.sensors["SCT_WORKMODE"] = resp[6]
    # device.sensors["SCT_BAT_CAP"] = resp[7]
    # device.sensors["SCT_REMAIN_MIL"] = resp[8]
    # device.sensors["SCT_PRDE_MIL"] = resp[9]
    # device.sensors["SCT_TOTAL_MIL"] = resp[10]
    # device.sensors["SCT_TRIP_MIL"] = resp[11]
    # device.sensors["SCT_TOTAL_RUN_TIME"] = resp[12]
    # device.sensors["SCT_TOTAL_RIDE_TIME"] = resp[13]
    # device.sensors["BAT_SW_VER"] = resp[1]
    # device.sensors["BAT_CAPACITY"] = resp[2]
    # device.sensors["BAT_TOTAL_CAPACITY"] = resp[3]
    # device.sensors["BAT_DESIGN_VOLTAGE"] = resp[4]
    # device.sensors["BAT_CYCLE_TIMES"] = resp[5]
    # device.sensors["BAT_CHARGE_TIMES"] = resp[6]
    # device.sensors["BAT_CHARGE_CAP"] = resp[7]
    # device.sensors["BAT_OVER_CHARGE_TIMES"] = resp[8]
    # device.sensors["BAT_OVER_DISCHARGE_TIMES"] = resp[9]
    # device.sensors["BAT_FUN_BOOLEAN"] = resp[0]
    # device.sensors["BAT_REMAINING_CAP"] = resp[1]
    # device.sensors["BAT_REMAINING_CAP_PERCENT"] = resp[2]
    # device.sensors["BAT_CURRENT_CUR"] = resp[3]
    # device.sensors["BAT_VOLTAGE_CUR"] = resp[4]
    # device.sensors["BAT_TEMP_CUR_1"] = resp[5]-20
    # device.sensors["BAT_TEMP_CUR_2"] = resp[6]-20
    # device.sensors["BAT_BALANCE_STATUS"] = resp[7]
    # device.sensors["BAT_ODIS_STATE"] = resp[8]
    # device.sensors["BAT_OCHG_STATE"] = resp[9]
    # device.sensors["BAT_CAP_COULOC"] = resp[10]
    # device.sensors["BAT_CAP_VOL"] = resp[11]
    # device.sensors["battery_health"] = resp[12]

    "battery_nominal_voltage": SensorEntityDescription(
        key="battery_nominal_voltage",
        translation_key="battery_nominal_voltage",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:sine-wave",
    ),
    "battery_voltage": SensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        suggested_display_precision=2,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
    ),

    "battery_level": SensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    
    "battery_current": SensorEntityDescription(
        key="battery_current",
        translation_key="battery_current",
        suggested_display_precision=2,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),

    "battery_temperature_1": SensorEntityDescription(
        key="battery_temperature_1",
        translation_key="battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    "battery_temperature_2": SensorEntityDescription(
        key="battery_temperature_2",
        translation_key="battery_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    "battery_overcharge_times": SensorEntityDescription(
        key="battery_overcharge_times",
        translation_key="battery_overcharge_times",
        native_unit_of_measurement="time/s",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-sync-outline",
    ),
    "battery_overdischarge_times": SensorEntityDescription(
        key="battery_overdischarge_times",
        translation_key="battery_overdischarge_times",
        native_unit_of_measurement="time/s",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-sync-outline",
    ),
    "battery_charge_times": SensorEntityDescription(
        key="battery_charge_times",
        translation_key="battery_charge_times",
        native_unit_of_measurement="time/s",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-sync-outline",
    ),
    "battery_charge_full_cycles": SensorEntityDescription(
        key="battery_charge_full_cycles",
        translation_key="battery_charge_full_cycles",
        native_unit_of_measurement="cycle/s",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-sync-outline",
    ),
    "battery_health": SensorEntityDescription(
        key="battery_health",
        translation_key="battery_health",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart-outline",
    ),
    "battery_balance_status": SensorEntityDescription(
        key="battery_balance_status",
        translation_key="battery_balance_status",
        icon="mdi:battery",
    ),
    "scooter_total_mileage": SensorEntityDescription(
        key="scooter_total_mileage",
        translation_key="scooter_total_mileage",
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:vector-line", #mdi:counter
    ),
    "scooter_last_trip_mileage": SensorEntityDescription(
        key="scooter_last_trip_mileage",
        translation_key="scooter_last_trip_mileage",
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:counter" #mdi:counter
    ),
    "battery_charging_status": SensorEntityDescription(
        key="battery_charging_status",
        translation_key="battery_charging_status",
        device_class=SensorDeviceClass.ENUM	,
        options=["Charging", "Discharging"],
        icon="mdi:ev-station", #mdi:counter
    ),
    "battery_designed_capacity": SensorEntityDescription(
        key="battery_designed_capacity",
        translation_key="battery_designed_capacity",
        native_unit_of_measurement="mAh",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:battery-heart-outline",
    ),
    "scooter_firmware_ver": SensorEntityDescription(
        key="scooter_firmware_ver",
        translation_key="scooter_firmware_ver",
        icon="mdi:label", 
    ),
    "scooter_remaining_mileage": SensorEntityDescription(
        key="scooter_remaining_mileage",
        translation_key="scooter_remaining_mileage",
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-radius" #mdi:counter
    ),
    "scooter_predicted_mileage": SensorEntityDescription(
        key="scooter_predicted_mileage",
        translation_key="scooter_predicted_mileage",
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:counter" #mdi:counter
    ),
    "scooter_total_run_time": SensorEntityDescription(
        key="scooter_total_run_time",
        translation_key="scooter_total_run_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-outline", 
    ),
    "scooter_total_ride_time": SensorEntityDescription(
        key="scooter_total_ride_time",
        translation_key="scooter_total_ride_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-play-outline", 
    ),
    
    "battery_overcharge_status": SensorEntityDescription(
        key="battery_overcharge_status",
        translation_key="battery_overcharge_status",
        icon="mdi:label", 
    ),
    "battery_overdischarge_status": SensorEntityDescription(
        key="battery_overdischarge_status",
        translation_key="battery_overdischarge_status",
        icon="mdi:label", 
    ),
    "battery_remaining_cap": SensorEntityDescription(
        key="battery_remaining_cap",
        translation_key="battery_remaining_cap",
        native_unit_of_measurement="mAh",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart-outline",
    ),
    "battery_full_charge_capacity": SensorEntityDescription(
        key="battery_full_charge_capacity",
        translation_key="battery_full_charge_capacity",
        native_unit_of_measurement="mAh",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart-outline",
    ),
    "battery_cell1_voltage": SensorEntityDescription(
        key="battery_cell1_voltage",
        translation_key="battery_cell1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell2_voltage": SensorEntityDescription(
        key="battery_cell2_voltage",
        translation_key="battery_cell2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell3_voltage": SensorEntityDescription(
        key="battery_cell3_voltage",
        translation_key="battery_cell3_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell4_voltage": SensorEntityDescription(
        key="battery_cell4_voltage",
        translation_key="battery_cell4_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell5_voltage": SensorEntityDescription(
        key="battery_cell5_voltage",
        translation_key="battery_cell5_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell6_voltage": SensorEntityDescription(
        key="battery_cell6_voltage",
        translation_key="battery_cell6_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell7_voltage": SensorEntityDescription(
        key="battery_cell7_voltage",
        translation_key="battery_cell7_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell8_voltage": SensorEntityDescription(
        key="battery_cell8_voltage",
        translation_key="battery_cell8_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell9_voltage": SensorEntityDescription(
        key="battery_cell9_voltage",
        translation_key="battery_cell9_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),
    "battery_cell10_voltage": SensorEntityDescription(
        key="battery_cell10_voltage",
        translation_key="battery_cell10_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sine-wave",
    ),

}


def _stable_unique_id(scooter: ScooterDevice, key: str) -> str:
    base_id = (scooter.mac_address or scooter.name).replace(":", "").lower()
    return f"{base_id}_{key}"


def _legacy_unique_id(scooter: ScooterDevice, key: str) -> str:
    return f"{scooter.name}_{key}"


def _device_identifiers(scooter: ScooterDevice) -> set[tuple[str, str]]:
    identifiers = {(DOMAIN, scooter.mac_address or scooter.name)}
    if scooter.name:
        identifiers.add((DOMAIN, scooter.name))
    return identifiers



async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    entity_registry = async_get(hass)

    async def migrate_entity_if_needed(old_unique_id: str, new_unique_id: str) -> None:
        if old_unique_id == new_unique_id:
            return

        try:
            entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, old_unique_id)
            if entity_id is None:
                return

            if entity_registry.async_get_entity_id("sensor", DOMAIN, new_unique_id):
                entity_registry.async_remove(entity_id)
                _LOGGER.debug("Removed duplicate legacy sensor entity %s", entity_id)
                return

            entity_registry.async_update_entity(entity_id, new_unique_id=new_unique_id)
            _LOGGER.debug("Migrated sensor entity %s to %s", entity_id, new_unique_id)
        except Exception as err:
            _LOGGER.debug(f"Unexpected error during entity migration, {err=}, {type(err)=}")
            raise

    """Set up the Xiaomi Scooter BLE sensors."""
    is_metric = hass.config.units is METRIC_SYSTEM

    coordinator: DataUpdateCoordinator[ScooterDevice] = hass.data[DOMAIN][entry.entry_id]

    sensors_mapping = SENSORS_MAPPING_TEMPLATE.copy()

    entities = []
    _LOGGER.debug("Got sensors: %s", coordinator.data.sensors)
    for sensor_type, sensor_value in coordinator.data.sensors.items():
        if sensor_type not in sensors_mapping:
            _LOGGER.debug(
                "Unknown sensor type detected: %s, %s",
                sensor_type,
                sensor_value,
            )
            continue

        new_unique_id = _stable_unique_id(coordinator.data, sensors_mapping[sensor_type].key)
        await migrate_entity_if_needed(
            _legacy_unique_id(coordinator.data, sensors_mapping[sensor_type].key),
            new_unique_id,
        )
        entities.append(
            ScooterSensor(coordinator, coordinator.data, sensors_mapping[sensor_type])
        )

    async_add_entities(entities)


class ScooterSensor(
    CoordinatorEntity[DataUpdateCoordinator[ScooterDevice]], SensorEntity
):
    """Xiaomi Scooter BLE sensors for the device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[ScooterDevice],
        scooter: ScooterDevice,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Populate the scooter entity with relevant data."""
        super().__init__(coordinator)
        self.entity_description = entity_description

        self._attr_unique_id = _stable_unique_id(scooter, entity_description.key)
        self._attr_device_info = DeviceInfo(
            connections={
                (
                    CONNECTION_BLUETOOTH,
                    scooter.mac_address,
                )
            },
            identifiers=_device_identifiers(scooter),
            name=scooter.name,
            manufacturer=scooter.manufacturer,
            model=scooter.model,
            sw_version=scooter.version,
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.coordinator.data.sensors[self.entity_description.key]
