"""Config flow for Energy Monitor."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

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


class EnergyMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Energy Monitor."""

    VERSION = 1
    _data: dict = {}

    async def async_step_user(self, user_input=None):
        """Step 1: Choose device type."""
        if user_input is not None:
            self._data.update(user_input)
            device_type = user_input[CONF_DEVICE_TYPE]
            default_name = DEVICE_TYPES[device_type]["name"]
            self._data.setdefault(CONF_DEVICE_NAME, default_name)
            return await self.async_step_sensors()

        device_options = {k: v["name"] for k, v in DEVICE_TYPES.items()}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_TYPE, default="custom"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": k, "label": v["name"]}
                            for k, v in DEVICE_TYPES.items()
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required(CONF_DEVICE_NAME): selector.TextSelector(),
            }),
            description_placeholders={"info": "Gerät auswählen und Namen vergeben"},
        )

    async def async_step_sensors(self, user_input=None):
        """Step 2: Select sensors."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_options()

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema({
                vol.Required(CONF_KWH_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class=["energy"],
                        multiple=False,
                    )
                ),
                vol.Optional(CONF_WATT_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class=["power"],
                        multiple=False,
                    )
                ),
                vol.Required(CONF_PRICE_ENTITY, default="input_number.strompreis"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["input_number", "sensor"],
                        multiple=False,
                    )
                ),
            }),
            errors=errors,
            description_placeholders={
                "info": "kWh-Sensor ist der Integralsensor oder Verbrauchszähler. Watt-Sensor optional für Echtzeitanzeige."
            },
        )

    async def async_step_options(self, user_input=None):
        """Step 3: Optional features."""
        if user_input is not None:
            self._data.update(user_input)
            name = self._data[CONF_DEVICE_NAME]
            return self.async_create_entry(title=name, data=self._data)

        watt_available = bool(self._data.get(CONF_WATT_SENSOR))

        schema_dict = {
            vol.Optional(CONF_CREATE_DAILY, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_CREATE_MONTHLY, default=True): selector.BooleanSelector(),
        }
        if watt_available:
            schema_dict[vol.Optional(CONF_TRACK_STATUS, default=True)] = selector.BooleanSelector()
            schema_dict[vol.Optional(CONF_STATUS_THRESHOLD, default=10)] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=500, step=1, unit_of_measurement="W")
            )

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "info": "Automatisch Utility Meter Helper anlegen? Betriebsstatus-Sensor erkennt ob das Gerät läuft."
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EnergyMonitorOptionsFlow(config_entry)


class EnergyMonitorOptionsFlow(config_entries.OptionsFlow):
    """Options flow — edit an existing device."""

    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self._entry.data, **self._entry.options}

        schema_dict = {
            vol.Required(CONF_DEVICE_NAME, default=data.get(CONF_DEVICE_NAME, "")): selector.TextSelector(),
            vol.Required(CONF_KWH_SENSOR, default=data.get(CONF_KWH_SENSOR, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=False)
            ),
            vol.Optional(CONF_WATT_SENSOR, default=data.get(CONF_WATT_SENSOR, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=False)
            ),
            vol.Required(CONF_PRICE_ENTITY, default=data.get(CONF_PRICE_ENTITY, "input_number.strompreis")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["input_number", "sensor"], multiple=False)
            ),
            vol.Optional(CONF_CREATE_DAILY, default=data.get(CONF_CREATE_DAILY, True)): selector.BooleanSelector(),
            vol.Optional(CONF_CREATE_MONTHLY, default=data.get(CONF_CREATE_MONTHLY, True)): selector.BooleanSelector(),
            vol.Optional(CONF_TRACK_STATUS, default=data.get(CONF_TRACK_STATUS, False)): selector.BooleanSelector(),
            vol.Optional(CONF_STATUS_THRESHOLD, default=data.get(CONF_STATUS_THRESHOLD, 10)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=500, step=1, unit_of_measurement="W")
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
