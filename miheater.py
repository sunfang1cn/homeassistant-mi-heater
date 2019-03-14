"""
    Support for Xiaomi wifi-enabled home heaters via miio.
    author: sunfang1cn@gmail.com
"""
import logging

import voluptuous as vol


try:
    from homeassistant.components.climate import (ClimateDevice, DOMAIN, PLATFORM_SCHEMA, STATE_HEAT,STATE_COOL,SUPPORT_TARGET_TEMPERATURE,SUPPORT_ON_OFF, SUPPORT_OPERATION_MODE)
finally:
    from homeassistant.components.climate.const import (ClimateDevice, DOMAIN, PLATFORM_SCHEMA, STATE_HEAT,STATE_COOL,SUPPORT_TARGET_TEMPERATURE,SUPPORT_ON_OFF, SUPPORT_OPERATION_MODE)

    
from homeassistant.const import (
    ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, CONF_TOKEN,
    STATE_ON, STATE_OFF, TEMP_CELSIUS)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import PlatformNotReady


_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['python-miio>=0.3.1']
SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE |
                 SUPPORT_ON_OFF)
SERVICE_SET_ROOM_TEMP = 'miheater_set_room_temperature'
MIN_TEMP = 16
MAX_TEMP = 32
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
})

SET_ROOM_TEMP_SCHEMA = vol.Schema({
    vol.Optional('temperature'): cv.positive_int
})



def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Xiaomi heaters."""
    from miio import Device, DeviceException

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)

    _LOGGER.info("Initializing Xiaomi heaters with host %s (token %s...)", host, token[:5])

    devices = []
    unique_id = None

    try:
        device = Device(host, token)

        device_info = device.info()
        model = device_info.model
        unique_id = "{}-{}".format(model, device_info.mac_address)
        _LOGGER.info("%s %s %s detected",
                     model,
                     device_info.firmware_version,
                     device_info.hardware_version)
        miHeater = MiHeater(device, name, unique_id, hass)
        devices.append(miHeater)
        add_devices(devices)
        async def set_room_temp(service):
            """Set room temp."""
            temperature = service.data.get('temperature')
            await miHeater.async_set_temperature(temperature)

        hass.services.async_register(DOMAIN, SERVICE_SET_ROOM_TEMP,
                                     set_room_temp, schema=SET_ROOM_TEMP_SCHEMA)
    except DeviceException:
        _LOGGER.exception('Fail to setup Xiaomi heater')
        raise PlatformNotReady



class MiHeater(ClimateDevice):
    from miio import DeviceException

    """Representation of a MiHeater device."""

    def __init__(self, device, name, unique_id, _hass):
        """Initialize the heater."""
        self._device = device
        self._name = name
        self._state = None
        self.entity_id = generate_entity_id('climate.{}', unique_id, hass=_hass)
        self.getAttrData()
    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS
    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._state['target_temperature'][0]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._state['current_temperature'][0]

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1
    def getAttrData(self):
        try:
            data = {}
            data['power'] = self._device.send('get_prop', ['power'])
            data['humidity'] = self._device.send('get_prop', ['relative_humidity'])
            data['target_temperature'] = self._device.send('get_prop', ['target_temperature'])
            data['current_temperature'] = self._device.send('get_prop', ['temperature'])
            self._state = data
        except DeviceException:
            _LOGGER.exception('Fail to get_prop from Xiaomi heater')
            self._state = None
            raise PlatformNotReady

    @property
    def device_state_attributes(self):
        return self._state

    @property
    def is_on(self):
        """Return true if heater is on."""
        return self._state['power'][0] == 'on'

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return MIN_TEMP

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return MAX_TEMP

    @property
    def current_operation(self):
        """Return current operation."""
        return STATE_HEAT if self._state['power'][0] == 'on' else STATE_OFF

    @property
    def operation_list(self):
        """List of available operation modes."""
        return [STATE_HEAT, STATE_OFF]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._device.send('set_target_temperature', [int(temperature)])


    async def async_turn_on(self):
        """Turn Mill unit on."""
        self._device.send('set_power', ['on'])

    async def async_turn_off(self):
        """Turn Mill unit off."""
        self._device.send('set_power', ['off'])


    async def async_update(self):
        """Retrieve latest state."""
        self.getAttrData()

    async def async_set_operation_mode(self, operation_mode):
        """Set operation mode."""
        if operation_mode == STATE_HEAT or operation_mode == STATE_COOL:
            await self.async_turn_on()
        elif operation_mode == STATE_OFF:
            await self.async_turn_off()
        else:
            _LOGGER.error("Unrecognized operation mode: %s", operation_mode)
