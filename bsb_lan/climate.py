"""Support for BSB-LAN climate devices."""
# need the same idea of the opentherm gateway
# sensors for reading info
# binary_sensor for toggle settings
# climate for the basic thermostat

import logging
from datetime import timedelta

import json

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

import voluptuous as vol

from homeassistant.components import climate
from homeassistant.components.climate import (
    PLATFORM_SCHEMA as CLIMATE_PLATFORM_SCHEMA, ClimateDevice)
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH, 
    ATTR_TARGET_TEMP_LOW, 
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    HVAC_MODE_HEAT, 
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL, 
    HVAC_MODE_OFF,
    HVAC_MODES,
    DEFAULT_MAX_TEMP, 
    DEFAULT_MIN_TEMP,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    SUPPORT_PRESET_MODE, 
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
    
    # hvac_modes, need to add it as property

from homeassistant.const import (
    CONF_AUTHENTICATION, 
    CONF_FORCE_UPDATE, 
    CONF_HEADERS, 
    CONF_NAME,
    CONF_METHOD, 
    CONF_PASSWORD, 
    CONF_HOST,
    CONF_UNIT_OF_MEASUREMENT, 
    CONF_USERNAME, CONF_TIMEOUT,
    CONF_VALUE_TEMPLATE, 
    CONF_VERIFY_SSL, 
    CONF_DEVICE_CLASS,
    HTTP_BASIC_AUTHENTICATION, 
    HTTP_DIGEST_AUTHENTICATION,
    ATTR_TEMPERATURE,
    TEMP_CELSIUS, 
    TEMP_FAHRENHEIT, 
    CONF_DEVICE, 
    CONF_VALUE_TEMPLATE, 
    STATE_ON,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.typing import ConfigType, HomeAssistantType
from homeassistant.util import Throttle

from .const import (
    ATTR_INSIDE_TEMPERATURE, 
    ATTR_OUTSIDE_TEMPERATURE, 
    ATTR_TARGET_TEMPERATURE,
    ATTR_PROTECTION_TEMPERATURE, 
    CONF_TEMP_MIN, 
    CONF_TEMP_MAX, 
    CONF_MODE_LIST,
    CONF_UNIQUE_ID,
)

# this should go in the config or other location
DEFAULT_NAME = 'BSB-LAN HVAC'
DEFAULT_METHOD = 'POST'
DEFAULT_VERIFY_SSL = False
DEFAULT_FORCE_UPDATE = False
DEFAULT_TIMEOUT = 30
DEFAULT_MIN_TEMP = 7
CONF_TEMP_MAX = 25


_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = CLIMATE_PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_AUTHENTICATION):
        vol.In([HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION]),
    vol.Optional(CONF_HEADERS): vol.Schema({cv.string: cv.string}),
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_DEVICE_CLASS): ClimateDevice,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_TEMP_MIN, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_TEMP_MAX, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_UNIQUE_ID): cv.string,
    vol.Optional(CONF_MODE_LIST,
                 default=[HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF, HVAC_MODE_HEAT, # STATE_ECO
                          ]): cv.ensure_list,
})

# not needed for now
HA_STATE_TO_BSBLAN = {
    HVAC_MODE_OFF: '0',
    HVAC_MODE_HEAT_COOL: '1',
    # STATE_ECO : '2', need to change this to a preset mode
    HVAC_MODE_HEAT: '3',
}

BSBLAN_TO_HA_STATE = {
    '0': HVAC_MODE_OFF,
    '1': HVAC_MODE_HEAT_COOL,
    # '2': STATE_ECO,
    '3': HVAC_MODE_HEAT,
}

HA_ATTR_TO_BSBLAN = {
    ATTR_INSIDE_TEMPERATURE: '8740',
    ATTR_HVAC_MODE: '700', # hvac_mode return the hvac state
    ATTR_TARGET_TEMPERATURE: '710',
    # ATTR_MAX_TEMP: '711',
    # ATTR_MIN_TEMP: '712',
    # ATTR_PROTECTION_TEMPERATURE: '714',
    ATTR_OUTSIDE_TEMPERATURE: '8700',
}


SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType,
                               async_add_entities, discovery_info=None):
    """Set up BSB-LAN climate device through configuration.yaml.
    old way of setting up the Platform. Need new way of setting up!
    """
    await _async_setup_entity(hass, config, async_add_entities)

async def _async_setup_entity(hass, config, async_add_entities,
                              config_entry=None, discovery_hash=None):
    """Set up the BSB-LAN climate devices."""

    force_update = config.get(CONF_FORCE_UPDATE)

    data = RestData(
        method=DEFAULT_METHOD,
        host=config.get(CONF_HOST),
        parameters=HA_ATTR_TO_BSBLAN,
        timeout=DEFAULT_TIMEOUT,
        auth=[config.get(CONF_USERNAME), config.get(CONF_PASSWORD)]
    )
    data.update()
    if data.setup_error is True:
        _LOGGER.error("can't connect to BSBLan")
        return

    async_add_entities([BSBlanClimate(hass, config, data, force_update)],True)


class BSBlanClimate(ClimateDevice):
    """Implementation of a BSB-LAN sensor."""

    def __init__(self, hass, config, rest_data, force_update):
        """Initialize the BSB-LAN sensor."""
        self._config = config
        self._unique_id = config.get(CONF_UNIQUE_ID)

        self.hass = hass
        self._rest_data = rest_data
        self._state = None
        self._unit_of_measurement = rest_data.unit_of_measurement
        self._device_class = rest_data.device_class
        # self._attributes = None
        self._force_update = force_update

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._config[CONF_NAME]

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        pass

    @property
    def supported_features(self):
        """Return the list of supported features."""
        support = 0
        
        if (self._rest_data.target_temp is not None):
            support |= SUPPORT_TARGET_TEMPERATURE
        
        if (self._rest_data.target_temp_range is not None):
            support |= SUPPORT_TARGET_TEMPERATURE_RANGE
    
        if (self._rest_data.current_operation is not None):
            support |= ATTR_HVAC_MODE

        _LOGGER.debug("support: %s", support)
        return support

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._rest_data.current_temp

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._rest_data.unit_of_measurement

    # @property
    # def target_temperature_low(self):
    #     """Return the low target temperature we try to reach."""
    #     return self._rest_data.target_temp_low

    # @property
    # def target_temperature_high(self):
    #     """Return the high target temperature we try to reach."""
    #     return self._rest_data.target_temp_high

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._rest_data.current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._config[CONF_MODE_LIST]

    async def async_set_operation_mode(self, operation_mode):
        """Set HVAC mode."""
        self._rest_data._set({ATTR_HVAC_MODE: operation_mode})
    
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._rest_data.target_temp

    # @property
    # def target_temperature_step(self):
    #     """Return the supported step of target temperature."""
    #     return 0.5

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        _LOGGER.debug("kwargs is: %s", kwargs)
        self._rest_data._set(kwargs)

    @property
    def device_class(self):
        """Return the class of this sensor."""
        self._device_class = self._rest_data.device_class
        return self._device_class

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self._rest_data.value is not None

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    @Throttle(SCAN_INTERVAL)
    async def async_update(self):
        """Get the latest data from REST API and update the state."""
        _LOGGER.info("update sensors BSBLan")
        self._rest_data.update()

    # @property
    # def device_state_attributes(self):
    #     """Return the state attributes."""
    #     return self._attributes

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._config[CONF_TEMP_MIN]

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._config[CONF_TEMP_MAX]


class RestData():
    """Class for handling the data retrieval."""
    
    def __init__(self, method, host, parameters, timeout, auth):
        """Initialize the data object."""
        self.method = method
        self.host = host
        self._parameters = parameters
        self._timeout = timeout
        self.auth = auth
        self.setup_error = False
        self.data = None
        self.state = None
        self.unit_of_measurement = None
        self.device_class = 'temperature'
        self.attributes = None
        self.current_temp = None
        self.target_temp = None
        self.value = None
        self.current_operation = None
        self.target_temp_range = None
        self.proc_temp = None

    # maybe rewrite this so it's not requesting all parameters
    # some params could have less uptodate values
    # initial update should pull all than only temperture on regular interval
    # use key so (attr) so specific param could be updated when interface changes them.

    @callback
    def update(self):
        """Get the latest data from BSB-LAN request service with post method."""
        import objectpath
        
        parameters = self._parameters
        host = self.host
        method = self.method
        authorize = self.auth

        try:
            for attr, parameter in parameters.items():
                # _LOGGER.debug("print key: %s", attr)
                payload_dict = {}
                payload_dict['Parameter'] = str(parameter)
                # authenication auth=('user', 'pass')
                if authorize is not None: # check if auth is enebled
                    request = requests.Request(
                        method, 'http://'+host+'/JQ', json=payload_dict, auth=authorize).prepare()
                else:
                    request = requests.Request(
                        method, 'http://'+host+'/JQ', json=payload_dict).prepare()

                with requests.Session() as sess:
                    response = sess.send(
                        request, timeout=self._timeout).json()

                _LOGGER.debug("New response %s", response) 
                response_tree = objectpath.Tree(response[parameter])
                value = tuple(response_tree.execute('$..value'))
                # name = tuple(response_tree.execute('$..name'))
                unit = tuple(response_tree.execute('$..unit'))
                # desc = tuple(response_tree.execute('$..desc'))
                # data_type = tuple(response_tree.execute('$..dataType'))
                
                # bsb_attr = HA_ATTR_TO_BSBLAN.get(key)

                if attr == 'inside_temperature':
                    self.current_temp = float(value[0])
                    self.value = value[0]
                    if unit[0] == '&deg;C':
                        self.unit_of_measurement = TEMP_CELSIUS
                    else:
                        self.unit_of_measurement = TEMP_FAHRENHEIT

                elif attr == 'target_temperature':
                    self.target_temp = float(value[0])

                # elif attr == 'max_temp':
                #     self.target_temp_high = float(value[0])
                
                # elif attr == 'min_temp':
                #     self.target_temp_low = float(value[0])

                elif attr == 'protection_temperature':
                    self.proc_temp = float(value[0])
                    # _LOGGER.debug("low temp: %s", self.proc_temp)

                elif attr == 'operation_mode':

                    ha_mode = BSBLAN_TO_HA_STATE.get(value[0])
                    self.current_operation = ha_mode

        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data: %s from %s failed with %s",
                        request, request.url, ex)
            self.setup_error = True
            return

    def _set(self, settings):
        """Set device settings using REST."""

        
        host = self.host
        method = self.method
        values = {}

        # get values
        for attr in [ATTR_TEMPERATURE, ATTR_HVAC_MODE]:
            value = settings.get(attr)
            if value is None:
                continue
            
            bsblan_attr =  HA_ATTR_TO_BSBLAN.get(attr)
            if bsblan_attr is not None:
                if attr == ATTR_HVAC_MODE:
                    _LOGGER.debug("print values ha attr: %s ", value)
                    values[bsblan_attr] = HA_STATE_TO_BSBLAN[value]
            
            # get operation mode and match with which temperture to set

            # sets default temperature
            elif attr == ATTR_TEMPERATURE:
                try:
                    values['710'] = str(value)
                except ValueError:
                    _LOGGER.error("Invalid temperature %s", value)

        if values:
            """
            How send works and what to expext it returns
            http://<IP-Adresse>/JS
            Send: "Parameter", "Value" (nur numerisch), "Type" (0 = INF, 1 = SET) 
            Receive: "Parameter", "Status" (0 = Failure, 1 = OK, 2 = Parameter read-only) 
            _LOGGER.debug("we got something to set: %s", values)
            """
            try:
                for key, value in values.items():
                    payload_dict = {
                        'Parameter' : str(key),
                        'Value' : value,
                        'Type' : '1'
                        }
                    _LOGGER.debug("payload: %s", payload_dict)

                    request = requests.Request(
                        method, 'http://'+host+'/JS', json=payload_dict).prepare()
                    _LOGGER.debug("request is: %s", request)
                    with requests.Session() as sess:
                        response = sess.send(
                            request, timeout=self._timeout).json()

                    _LOGGER.debug("New response %s", response)
                    self.update()

            except requests.exceptions.RequestException as ex:
                _LOGGER.error("Error fetching data: %s from %s failed with %s",
                            request, request.url, ex)
                self.setup_error = True
                return

