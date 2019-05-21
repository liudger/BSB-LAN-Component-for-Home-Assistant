"""Constants for BSB-LAN."""
from homeassistant.const import CONF_ICON, CONF_NAME, CONF_TYPE

ATTR_TARGET_TEMPERATURE = 'target_temperature'
ATTR_INSIDE_TEMPERATURE = 'inside_temperature'
ATTR_OUTSIDE_TEMPERATURE = 'outside_temperature'
ATTR_PROTECTION_TEMPERATURE = 'protection_temperature'

CONF_TEMP_MAX = 'max_temp'
CONF_TEMP_MIN = 'min_temp'
CONF_MODE_LIST = 'modes'

CONF_UNIQUE_ID = 'unique_id'

SENSOR_TYPE_TEMPERATURE = 'temperature'

SENSOR_TYPES = {
    ATTR_INSIDE_TEMPERATURE: {
        CONF_NAME: 'Inside Temperature',
        CONF_ICON: 'mdi:thermometer',
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE
    },
    ATTR_OUTSIDE_TEMPERATURE: {
        CONF_NAME: 'Outside Temperature',
        CONF_ICON: 'mdi:thermometer',
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE
    }
}