#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of CSTBox.
#
# CSTBox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CSTBox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with CSTBox.  If not, see <http://www.gnu.org/licenses/>.

""" DigiRail 2A signal conditioner module low-level interface.

This modules defines a sub-class of RTUModbusHWDevice which polls the
parameters of interest.
"""

import struct
from collections import namedtuple

from pycstbox.modbus import ModbusRegister, RTUModbusHWDevice

from pycstbox.hal import HalError

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'
__copyright__ = 'Copyright (c) 2017 CSTB'


INPUT_TYPE_TEMPERATURE, INPUT_TYPE_VOLTAGE, INPUT_TYPE_CURRENT = range(3)

DISABLED_INPUT_TYPE = -1
TEMPERATURE_INPUT_TYPE_CODES = tuple(range(9))
VOLTAGE_INPUT_TYPE_CODES = tuple(range(9, 18))
CURRENT_INPUT_TYPE_CODES = tuple(range(18, 20))

INPUT_TYPE_LABEL = {
    -1: 'disabled',
    0: 'TC type J',
    1: 'TC type K',
    2: 'TC type T',
    3: 'TC type E',
    4: 'TC type N',
    5: 'TC type R',
    6: 'TC type S',
    7: 'TC type B',
    8: 'Pt100',
    9: '50mV',
    10: '20mV',
    11: '-10/20mV',
    12: '5V',
    13: '10V',
    18: '0/20mA',
    19: '4/20mA',
}

TEMPERATURE_UNIT = ['degC', 'degF']

SCALE_DIVISORS = {
    INPUT_TYPE_TEMPERATURE: 10.,
    INPUT_TYPE_VOLTAGE: 1000.,
    INPUT_TYPE_CURRENT: 1.
}

INPUT_TYPE_CATEGORY_LABEL = {
    INPUT_TYPE_TEMPERATURE: 'temperature',
    INPUT_TYPE_VOLTAGE: 'voltage',
    INPUT_TYPE_CURRENT: 'current'
}


class DRInput(object):
    """ DigiRail input modeling class """
    def __init__(self, input_type, input_unit):
        """
        :param int input_type: the code of the input type
        :param int input_unit: the unit code of the input
        """
        self._input_type = input_type
        if input_type in TEMPERATURE_INPUT_TYPE_CODES:
            self._input_type_category = INPUT_TYPE_TEMPERATURE
        elif input_type in VOLTAGE_INPUT_TYPE_CODES:
            self._input_type_category = INPUT_TYPE_VOLTAGE
        elif input_type in CURRENT_INPUT_TYPE_CODES:
            self._input_type_category = INPUT_TYPE_CURRENT
        else:
            self._input_type_category = None

        if self._input_type_category == INPUT_TYPE_TEMPERATURE:
            self._unit = TEMPERATURE_UNIT[input_unit]
        elif self._input_type_category == INPUT_TYPE_VOLTAGE:
            self._unit = 'V'
        elif self._input_type_category == INPUT_TYPE_CURRENT:
            self._unit = 'mA'

    @property
    def input_type(self):
        return self._input_type

    @property
    def input_type_category(self):
        return self._input_type_category

    @property
    def enabled(self):
        return self._input_type_category is not None

    @property
    def unit(self):
        return self._unit

    def physical_value(self, reg_value):
        """ Converts the register raw value into the physical value of the measure,
        expressed in the input unit.
        
        :return: the value or None if the input is disabled
        :rtype: float
        :raise RunTime
        """
        if self.enabled:
            return float(reg_value) / SCALE_DIVISORS[self._input_type_category]
        else:
            return None

    def __str__(self):
        return '%s (%s)' % (INPUT_TYPE_LABEL[self.input_type], self.unit)


class DigiRail_2A(RTUModbusHWDevice):
    """ DigiRail-2A A/D converter HW device

    The supported model is the RTU RS485 one, the RS485 bus being connected
    via a USB.RS485 interface.
    """

    DEFAULT_BAUDRATE = 19200

    # registers
    # - configuration
    REG_MODBUS_ADDR = ModbusRegister(3)
    REG_INPUT_TYPE_1 = ModbusRegister(21)
    REG_INPUT_TYPE_2 = ModbusRegister(22)
    REG_MEAS_UNIT_1 = ModbusRegister(26)
    REG_MEAS_UNIT_2 = ModbusRegister(27)

    # - data
    REG_PV_ENG_1 = ModbusRegister(14)
    REG_PV_ENG_2 = ModbusRegister(15)

    #: the compiled sequence of collected registers
    COLLECTED_REGS = [REG_PV_ENG_1, REG_PV_ENG_2]

    _TOTAL_INPUT_SIZE = reduce(lambda accum, size: accum + size, [r.size for r in COLLECTED_REGS])

    # Definition of the type of the poll() method result

    # VERY IMPORTANT :
    # The name of its items MUST match the name of the outputs described
    # in the metadata stored in devcfg.d directory, since the notification
    # events generation process is based on this.
    # (see pycstbox.hyal.device.PolledDevice.poll() method for details)
    OutputValues = namedtuple('OutputValues', [
        'in1',         # input 1
        'in2',         # input 2
    ])

    def __init__(self, port, unit_id):
        """
        :param str port: serial port on which the RS485 interface is connected
        :param int unit_id: the address of the device
        """
        super(DigiRail_2A, self).__init__(port=port, unit_id=int(unit_id), logname='dr2a')

        self._logger.info('reading inputs configuration from device...')
        input_types = self.unpack_registers(start_register=self.REG_INPUT_TYPE_1, reg_count=2, unpack_format='>hh')
        input_units = self.unpack_registers(start_register=self.REG_MEAS_UNIT_1, reg_count=2, unpack_format='>hh')

        self._logger.info('creating corresponding model instances...')
        self.inputs = [DRInput(input_type, input_unit) for input_type, input_unit in zip(input_types, input_units)]
        for n, input in enumerate(self.inputs):
            self._logger.info('... [%d] %s', n + 1, input)

    @property
    def unit_id(self):
        """ The id of the device """
        return self.address

    def poll(self):
        """ Reads the registers data and returns the
        values as a named tuple.

        """
        # since the input registers are contiguous, optimise the operation by reading them in a single request
        return self.OutputValues(**dict(
            zip(
                self.OutputValues._fields,
                [inp.physical_value(rv) for inp, rv in zip(
                    self.inputs, self.unpack_registers(self.REG_PV_ENG_1, reg_count=2, unpack_format=">hh")
                )]
            )
        ))

    def input_unit(self, channel_num):
        try:
            return self.inputs[channel_num - 1].unit
        except KeyError:
            raise ValueError('invalid channel number (%s)' % channel_num)

    def is_enabled(self, channel_num):
        try:
            return self.inputs[channel_num - 1].enabled
        except KeyError:
            raise ValueError('invalid channel number (%s)' % channel_num)


class Digirail2AException(Exception):
    """ Root class for device related exceptions. """


class NotConfiguredInput(Digirail2AException):
    """ Raised when an input is queried before its configuration has been acquired from the device. """


class DisabledInput(Digirail2AException):
    """ Raised when a disabled input is queried for its value, unit,... """
