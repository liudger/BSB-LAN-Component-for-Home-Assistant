"""Support for BSB-LAN sensors."""
from datetime import timedelta
import logging
import json

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA, DEVICE_CLASSES_SCHEMA)
from homeassistant.const import (
    CONF_AUTHENTICATION, CONF_FORCE_UPDATE, CONF_HEADERS, CONF_NAME,
    CONF_METHOD, CONF_PASSWORD, CONF_PAYLOAD, CONF_HOST,
    CONF_UNIT_OF_MEASUREMENT, CONF_USERNAME, CONF_TIMEOUT,
    CONF_VALUE_TEMPLATE, CONF_VERIFY_SSL, CONF_DEVICE_CLASS,
    HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_METHOD = 'POST'
DEFAULT_NAME = 'BSB-LAN Sensor'
DEFAULT_VERIFY_SSL = False
DEFAULT_FORCE_UPDATE = False
DEFAULT_TIMEOUT = 120

SCAN_INTERVAL = timedelta(seconds=120)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_AUTHENTICATION):
        vol.In([HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION]),
    vol.Optional(CONF_HEADERS): vol.Schema({cv.string: cv.string}),
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_PAYLOAD): cv.ensure_list_csv,
    vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the BSB-LAN sensor."""
    # need to implement some kind of security in next release
    # username = config.get(CONF_USERNAME)
    # password = config.get(CONF_PASSWORD)
    force_update = config.get(CONF_FORCE_UPDATE)
    interval = config.get(SCAN_INTERVAL)

    sensors = []
    for parameter in config.get(CONF_PAYLOAD):
        payload_construct = {}
        payload_construct['Parameter'] = parameter
        _LOGGER.info(payload_construct)
        data = RestData(
            method=DEFAULT_METHOD,
            resource='http://'+config.get(CONF_HOST)+"/JQ",
            payload_construct=payload_construct,
            parameter=parameter,
            timeout=DEFAULT_TIMEOUT
        )
        if data.setup_error is True:
            _LOGGER.error("can't connect to BSBLan")
            return
        # Must update the sensor now (including fetching the rest resource) to
        # ensure it's updating its state.
        sensors.append(BSBlanSensor(data, interval, force_update))
    add_entities(sensors, True)


class BSBlanSensor(Entity):
    """Implementation of a BSB-LAN sensor."""

    def __init__(self, rest_data, interval, force_update):
        """Initialize the BSB-LAN sensor."""
        self._hass = None
        self._rest_data = rest_data
        self._name = None
        self._state = None
        self._unit_of_measurement = rest_data.unit_of_measurement
        self._device_class = rest_data.device_class
        self._attributes = None
        self._force_update = force_update

    @property
    def name(self):
        """Return the name of the sensor."""
        self._name = self._rest_data.name
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        self._unit_of_measurement = self._rest_data.unit_of_measurement
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the class of this sensor."""
        self._device_class = self._rest_data.device_class
        return self._device_class

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self._rest_data.data is not None

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Get the latest data from REST API and update the state."""
        _LOGGER.info("update sensors BSBLan")
        self._rest_data.update()
        
        self._state = self._rest_data.data
        self._name = self._rest_data.name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes


class RestData():
    """Class for handling the data retrieval."""
    
    def __init__(self, method, resource, payload_construct, parameter, timeout):
        """Initialize the data object."""
        try:
            self._request = requests.Request(
                method, resource, json=payload_construct).prepare()
        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data: %s from %s failed with %s",
                          self._request, self._request.url, ex)
            self.setup_error = True
            return

        self._timeout = timeout
        self.setup_error = False
        self.data = None
        self.parameter = parameter
        self.name = None
        self.state = None
        self.unit_of_measurement = None
        self.device_class = None
        self.attributes = None

    def update(self):
        """Get the latest data from BSB-LAN request service with post method."""
        import objectpath
        
        _LOGGER.info("Updating from %s", self._request.url)
        try:
            with requests.Session() as sess:
                response = sess.send(
                    self._request, timeout=self._timeout).json()

            _LOGGER.info("New response %s", response) 
            response_tree = objectpath.Tree(response[self.parameter])
            value = tuple(response_tree.execute('$..value'))
            name = tuple(response_tree.execute('$..name'))
            unit = tuple(response_tree.execute('$..unit'))
            data_type = tuple(response_tree.execute('$..dataType'))
            description = tuple(response_tree.execute('$..desc'))

            self.data = value[0]
            self.name = name[0]

            # "DataType" (0 = Zahl, 1 = ENUM, 2 = Wochentag, 3 = Stunde/Minute, 4 = Datum/Uhrzeit, 5 = Tag/Monat, 6 = String)
            if data_type[0] == 0:
                if unit[0] == '&deg;C':
                    self.unit_of_measurement = '°C'
                    self.device_class = 'temperture'
            elif data_type[0] == 1:
                self.data = description[0]
            elif data_type[0] == 6:
                self.data = "temp string"

                
            _LOGGER.info("New value %s from %s", self.data, self.name) 

        except requests.exceptions.RequestException as ex:
            _LOGGER.error("Error fetching data: %s from %s failed with %s",
                          self._request, self._request.url, ex)
            
