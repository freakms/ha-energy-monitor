"""Sensor platform for Energy Monitor — auto-creates cost, status, and period sensors."""
from __future__ import annotations

import logging
from datetime import timedelta

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
    """Period cost sensor (daily / monthly) with midnight reset and recorder-based init."""

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
        current = _safe_float(self.hass, self._kwh_sensor)
        delta   = max(0.0, current - (self._period_start_kwh or current))
        return {
            "verbrauch_kwh": round(delta, 4),
            "periode": self._period,
            "kwh_sensor": self._kwh_sensor,
            "period_start_kwh": self._period_start_kwh,
        }

    async def async_added_to_hass(self):
        # 1. Try to restore from last saved state (survives restarts within same period)
        last_state = await self.async_get_last_state()
        if last_state and last_state.attributes.get("period_start_kwh") is not None:
            try:
                restored = float(last_state.attributes["period_start_kwh"])
                if self._is_same_period(last_state.last_updated):
                    self._period_start_kwh = restored
                    _LOGGER.debug("%s: restored period_start_kwh=%.4f", self._attr_name, restored)
            except (ValueError, TypeError):
                pass

        # 2. No valid restore → query recorder for value at period start (midnight / 1st of month)
        if self._period_start_kwh is None:
            recorder_value = await self._get_period_start_from_recorder()
            if recorder_value is not None:
                self._period_start_kwh = recorder_value
                _LOGGER.debug("%s: recorder period_start_kwh=%.4f", self._attr_name, recorder_value)

        # 3. Fallback: start from current value (will only count from now)
        if self._period_start_kwh is None:
            self._period_start_kwh = _safe_float(self.hass, self._kwh_sensor)
            _LOGGER.debug("%s: fallback period_start_kwh=%.4f", self._attr_name, self._period_start_kwh)

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

    async def _get_period_start_from_recorder(self) -> float | None:
        """Query recorder for kWh value at midnight (daily) or 1st of month (monthly)."""
        now = dt_util.now()
        if self._period == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.history import state_changes_during_period

            instance = get_instance(self.hass)

            # Fetch states in a window around period start
            history = await instance.async_add_executor_job(
                state_changes_during_period,
                self.hass,
                period_start - timedelta(hours=1),
                period_start + timedelta(minutes=10),
                self._kwh_sensor,
                True,   # include_start_time_state
                False,  # significant_changes_only
            )

            states = history.get(self._kwh_sensor, [])
            # Pick the state closest to (but not after) period_start
            best_val = None
            best_ts = None
            for state in states:
                if state.state in ("unavailable", "unknown", ""):
                    continue
                try:
                    val = float(state.state)
                    ts = state.last_updated
                    # Prefer latest state that is <= period_start + 5 min
                    if ts <= period_start + timedelta(minutes=5):
                        if best_ts is None or ts > best_ts:
                            best_val = val
                            best_ts = ts
                except (ValueError, TypeError):
                    continue

            if best_val is not None:
                _LOGGER.debug(
                    "%s: recorder found start value %.4f at %s",
                    self._attr_name, best_val, best_ts,
                )
                return best_val

        except Exception as exc:
            _LOGGER.debug("%s: recorder query failed: %s", self._attr_name, exc)

        return None

    @callback
    def _handle_period_reset(self, now):
        """Called at midnight. Reset only when period boundary is crossed."""
        if self._period == "daily" or (self._period == "monthly" and now.day == 1):
            self._period_start_kwh = _safe_float(self.hass, self._kwh_sensor)
            _LOGGER.debug(
                "%s: period reset at %s, new start=%.4f",
                self._attr_name, now, self._period_start_kwh,
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
        return lu.year == now.year and lu.month == now.month

    async def async_update(self):
        pass
