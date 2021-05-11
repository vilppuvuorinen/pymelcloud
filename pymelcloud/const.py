"""Constants for pymelcloud."""

DEVICE_TYPE_ATA = "ata"
DEVICE_TYPE_ATW = "atw"
DEVICE_TYPE_ERV = "erv"
DEVICE_TYPE_UNKNOWN = "unknown"

ACCESS_LEVEL = {
    "GUEST": 3,
    "OWNER": 4,
}

DEVICE_TYPE_LOOKUP = {
    0: DEVICE_TYPE_ATA,
    1: DEVICE_TYPE_ATW,
    3: DEVICE_TYPE_ERV,
}

UNIT_TEMP_CELSIUS = "celsius"
UNIT_TEMP_FAHRENHEIT = "fahrenheit"
