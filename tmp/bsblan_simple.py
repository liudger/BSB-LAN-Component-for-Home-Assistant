"""this component provide basic communication to BSB-LAN."""
# import logging

import requests
import objectpath

# _LOGGER = logging.getLogger(__name__)
# # get info from config

# from homeassistant.const import TEMP_CELSIUS
# from homeassistant.helpers.entity import Entity

# from . import DOMAIN

# DEFAULT_NAME = 'BSB HVAC'

# def setup_platform(hass, config, add_devices, discovery_info=None):
#     """Setup the BSB platform."""
#     # We only want this platform to be set up via discovery.
#     if discovery_info is None:
#         return
#     add_devices([BSBLAN()])


# class BSBLAN(Entity):
#     """Representation of BSB-LAN interface."""

#     def __init__(self):
#         """Initialize the platform."""
#         self._state = None

#     @property
#     def name(self):
#         """Return the name of."""
#         return DEFAULT_NAME

#     @property
#     def state(self):
#         """Return the state of the sensor."""
#         return self._state

#     @property
#     def unit_of_measurement(self):
#         """Return the unit of measurement."""
#         return TEMP_CELSIUS

#     def update(self):
#         """Fetch new state data for the sensor.
#         This is the only method that should fetch new data for Home Assistant.
#         """
#         self._state = self.hass.data[DOMAIN]['temperature']

# def get_simple_keys(data):
#     result = []
#     for key in data.keys():
#         if type(data[key]) != dict:
#             result.append(key)
#         else:
#             result += get_simple_keys(data[key])
#     return result


def get_data():
    """Get data BSB-LAN platform."""




    # JQ used for query
    # JS sets params

    # get url from config add /JQ or /JS
    # url = config.get(CONF_URL)
    url = 'http://10.0.1.60/JQ'
    # username = config.get(CONF_USERNAME)
    # password = config.get(CONF_PASSWORD)
    post_fields = {'Parameter':'710'}

    r = requests.post(url, json=post_fields)
    print(r.status_code, r.reason)
    response_data = r.json()
    print (response_data)
    # print(r.text)
    response_tree = objectpath.Tree(response_data['710'])
    result = tuple(response_tree.execute('$..value'))
    print (result[0])
    # for item in response_data:
    #     print (item.get('8830').get('value'))
    # print(get_simple_keys(response_data['8830']))

# def set_param():
#     """Set param via BSB-LAN"""

get_data()