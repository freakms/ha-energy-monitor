"""Sensor platform for Energy Monitor — auto-creates cost, status, and period sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    DEVICE_TYPES,
    CONF_DEVICE_TYPE,
    CONF_DEVICE_NAME,
    CONF_KWH_SENSOR,
    CONF_WATT_SENSOR,
    CONF_PRICE_ENTITY,
    CONF_CREATE_DAILY,
    CONF_CREATE_MONTHLY,
    CONF_TRACK_STATUS,
    CONF_STATUS_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = {**entry.data, **entry.options}

    device_type  = data.get(CONF_DEVICE_TYPE, "custom")
    device_name  = data.get(CONF_DEVICE_NAME, "Gerät")
    kwh_sensor   = data[CONF_KWH_SENSOR]
    watt_sensor  = data.get(CONF_WATT_SENSOR)
    price_entity = data.get(CONF_PRICE_ENTITY, "input_number.strompreis")
    track_status = data.get(CONF_TRACK_STATUS, False)
    threshold_w  = float(data.get(CONF_STATUS_THRESHOLD, 10))

    device_info = DEVICE_TYPES.get(device_type, DEVICE_TYPES["custom"])
    slug = slugify(device_name)

    entities: list[SensorEntity] = []

    entities.append(
        EnergyKostenSensor(
            hass=hass,
            entry_id=entry.entry_id,
            slug=slug,
            device_name=device_name,
            device_info=device_info,
            kwh_sensor=kwh_sensor,
            price_entity=price_entity,
        )
    )

    if watt_sensor and track_status:
        entities.append(
            EnergyStatusSensor(
                hass=hass,
                entry_id=entry.entry_id,
                slug=slug,
                device_name=device_name,
                device_info=device_info,
                watt_sensor=watt_sensor,
                threshold_w=threshold_w,
            )
        )

    if data.get(CONF_CREATE_DAILY, True):
        entities.append(
            EnergyPeriodKostenSensor(
                hass=hass,
                entry_id=entry.entry_id,
                slug=slug,
                device_name=device_name,
                device_info=device_info,
                kwh_sensor=kwh_sensor,
                price_entity=price_entity,
                period="daily",
            )
        )

    if data.get(CONF_CREATE_MONTHLY, True):
        entities.append(
            EnergyPeriodKostenSensor(
                hass=hass,
                entry_id=entry.entry_id,
                slug=slug,
                device_name=device_name,
                device_info=device_info,
                kwh_sensor=kwh_sensor,
                price_entity=price_entity,
                period="monthly",
            )
        )

    async_add_entities(entities, update_before_add=True)


def _safe_float(hass: HomeAssistant, entity_id: str) -> float:
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unavailable", "unknown", ""):
        return 0.0
    try:
        return float(state.state)
    except (ValueError, TypeError):
        return 0.0


class EnergyKostenSensor(SensorEntity):
    """Total running cost sensor: kWh * price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "€"
    _attr_suggested_display_precision = 2

    def __init__(self, hass, entry_id, slug, device_name, device_info, kwh_sensor, price_entity):
        self.hass = hass
        self._kwh_sensor   = kwh_sensor
        self._price_entity = price_entity
        self._attr_name    = f"{device_name} Energiekosten"
        self._attr_unique_id = f"{entry_id}_kosten"
        self._attr_icon    = device_info["icon"]
        self._attr_extra_state_attributes = {
            "kwh_sensor": kwh_sensor,
            "price_entity": price_entity,
            "device": device_name,
        }

    @property
    def native_value(self):
        kwh   = _safe_float(self.hass, self._kwh_sensor)
        price = _safe_float(self.hass, self._price_entity)
        return round(kwh * price, 4)

    async def async_added_to_hass(self):
        @callback
        def _handle_state_change(event):
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._kwh_sensor, self._price_entity],
                _handle_state_change,
            )
        )

    async def async_update(self):
        pass


class EnergyStatusSensor(SensorEntity):
    """Binary-style sensor: device is running if watt > threshold."""

    def __init__(self, hass, entry_id, slug, device_name, device_info, watt_sensor, threshold_w):
        self.hass = hass
        self._watt_sensor  = watt_sensor
        self._threshold_w  = threshold_w
        self._attr_name    = f"{device_name} Betriebsstatus"
        self._attr_unique_id = f"{entry_id}_status"
        self._attr_icon    = device_info["icon"]

    @property
    def native_value(self):
        watt = _safe_float(self.hass, self._watt_sensor)
        return "läuft" if watt >= self._threshold_w else "aus"

    @property
    def extra_state_attributes(self):
        watt = _safe_float(self.hass, self._watt_sensor)
        return {
            "aktuelle_leistung_w": round(watt, 1),
            "schwellwert_w": self._threshold_w,
            "watt_sensor": self._watt_sensor,
        }

    async def async_added_to_hass(self):
        @callback
        def _handle_state_change(event):
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._watt_sensor],
                _handle_state_change,
            )
        )

    async def async_update(self):
        pass


class EnergyPeriodKostenSensor(SensorEntity, RestoreEntity):
    """Period cost sensor (daily / monthly) with midnight reset and state restore."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "€"
    _attr_suggested_display_precision = 2

    def __init__(self, hass, entry_id, slug, device_name, device_info, kwh_sensor, price_entity, period):
        self.hass = hass
        self._kwh_sensor      = kwh_sensor
        self._price_entity    = price_entity
        self._period          = period
        period_label          = "Heute" if period == "daily" else "Monat"
        self._attr_name       = f"{device_name} Kosten {period_label}"
        self._attr_unique_id  = f"{entry_id}_kosten_{period}"
        self._attr_icon       = device_info["icon"]
        self._period_start_kwh: float | None = None

    @property
    def native_value(self):
        if self._period_start_kwh is None:
            return 0.0
        current = _safe_float(self.hass, self._kwh_sensor)
        price   = _safe_float(self.hass, self._price_entity)
        delta   = max(0.0, current - self._period_start_kwh)
        return round(delta * price, 4)

    @property
    def extra_state_attributes(self):
        current = _safe_float(self.hass, self._kwh_sensor) if self._period_start_kwh is not None else 0.0
        delta   = max(0.0, current - (self._period_start_kwh or current))
        return {
            "verbrauch_kwh": round(delta, 4),
            "periode": self._period,
            "kwh_sensor": self._kwh_sensor,
            # persisted so we can restore it after HA restart
            "period_start_kwh": self._period_start_kwh,
        }

    async def async_added_to_hass(self):
        # Restore period_start_kwh from last known state so a restart doesn't reset the counter
        last_state = await self.async_get_last_state()
        if last_state and last_state.attributes.get("period_start_kwh") is not None:
            try:
                restored = float(last_state.attributes["period_start_kwh"])
                # Only restore if the restored start is still within the current period
                if self._is_same_period(last_state.last_updated):
                    self._period_start_kwh = restored
                    _LOGGER.debug(
                        "%s: restored period_start_kwh=%.4f", self._attr_name, restored
                    )
            except (ValueError, TypeError):
                pass

        # If no valid restore, initialise from the sensor's current value
        if self._period_start_kwh is None:
            current = _safe_float(self.hass, self._kwh_sensor)
            if current:
                self._period_start_kwh = current

        # React to kWh / price changes
        @callback
        def _handle_state_change(event):
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._kwh_sensor, self._price_entity],
                _handle_state_change,
            )
        )

        # Reset at midnight every day
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._handle_period_reset, hour=0, minute=0, second=0
            )
        )

    @callback
    def _handle_period_reset(self, now):
        """Called at midnight. Reset only when the period boundary is crossed."""
        if self._period == "daily" or (self._period == "monthly" and now.day == 1):
            self._period_start_kwh = _safe_float(self.hass, self._kwh_sensor)
            _LOGGER.debug(
                "%s: period reset at %s, start=%.4f", self._attr_name, now, self._period_start_kwh
            )
            self.async_write_ha_state()

    def _is_same_period(self, last_updated) -> bool:
        """Return True if last_updated is within the current period."""
        now = dt_util.now()
        if last_updated is None:
            return False
        lu = dt_util.as_local(last_updated)
        if self._period == "daily":
            return lu.date() == now.date()
        # monthly
        return lu.year == now.year and lu.month == now.month

    async def async_update(self):
        pass
