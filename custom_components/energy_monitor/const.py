"""Constants for Energy Monitor integration."""

DOMAIN = "energy_monitor"
PLATFORMS = ["sensor"]

DEVICE_TYPES = {
    "washer":      {"name": "Waschmaschine",    "icon": "mdi:washing-machine",   "mdi": "washing-machine"},
    "dryer":       {"name": "Wäschetrockner",   "icon": "mdi:tumble-dryer",      "mdi": "tumble-dryer"},
    "dishwasher":  {"name": "Geschirrspüler",   "icon": "mdi:dishwasher",        "mdi": "dishwasher"},
    "fridge":      {"name": "Kühlschrank",       "icon": "mdi:fridge",            "mdi": "fridge"},
    "freezer":     {"name": "Gefrierschrank",    "icon": "mdi:fridge-outline",    "mdi": "fridge-outline"},
    "tv":          {"name": "Fernseher",         "icon": "mdi:television",        "mdi": "television"},
    "server":      {"name": "Server / NAS",      "icon": "mdi:server",            "mdi": "server"},
    "pc":          {"name": "PC / Desktop",      "icon": "mdi:desktop-tower",     "mdi": "desktop-tower"},
    "router":      {"name": "Router / Switch",   "icon": "mdi:router-network",    "mdi": "router-network"},
    "heatpump":    {"name": "Wärmepumpe",        "icon": "mdi:heat-pump",         "mdi": "heat-pump"},
    "ac":          {"name": "Klimaanlage",       "icon": "mdi:air-conditioner",   "mdi": "air-conditioner"},
    "oven":        {"name": "Backofen",          "icon": "mdi:stove",             "mdi": "stove"},
    "microwave":   {"name": "Mikrowelle",        "icon": "mdi:microwave",         "mdi": "microwave"},
    "boiler":      {"name": "Boiler / Warmwasser","icon": "mdi:water-boiler",     "mdi": "water-boiler"},
    "ev_charger":  {"name": "Wallbox / E-Auto",  "icon": "mdi:ev-station",        "mdi": "ev-station"},
    "light":       {"name": "Beleuchtung",       "icon": "mdi:lightbulb-group",   "mdi": "lightbulb-group"},
    "pump":        {"name": "Pumpe",             "icon": "mdi:pump",              "mdi": "pump"},
    "custom":      {"name": "Eigenes Gerät",     "icon": "mdi:lightning-bolt",    "mdi": "lightning-bolt"},
}

# Config entry keys
CONF_DEVICE_TYPE    = "device_type"
CONF_DEVICE_NAME    = "device_name"
CONF_KWH_SENSOR     = "kwh_sensor"
CONF_WATT_SENSOR    = "watt_sensor"
CONF_PRICE_ENTITY   = "price_entity"
CONF_CREATE_DAILY   = "create_daily_meter"
CONF_CREATE_MONTHLY = "create_monthly_meter"
CONF_TRACK_STATUS   = "track_status"
CONF_STATUS_THRESHOLD = "status_threshold_w"
