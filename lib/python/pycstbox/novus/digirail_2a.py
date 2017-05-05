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

""" DigiRail 2A signa conditioner module low-level interface.

This modules defines a sub-class of minimalmodbus.Instrument which polls the
parameters of interest.

Depends on Jonas Berg's minimalmodbus Python library :
    https://pypi.python.org/pypi/MinimalModbus/
    Version in date of writing: 0.4
"""

import minimalmodbus
import struct
import serial
import time
from collections import namedtuple

from pycstbox.modbus import ModbusRegister
from pycstbox.log import Loggable

__author__ = 'Peter Riederer - CSTB (peter.riederer@cstb.fr)'
__copyright__ = 'Copyright (c) 2014 CSTB'
__vcs_id__ = '$Id$'
__version__ = '1.0.0'


# Input registers

REG_IN1 = ModbusRegister(14)
REG_IN2 = ModbusRegister(15)


ALL_INPUTS_SIZE = reduce(lambda sztot, sz: sztot + sz,
                         [reg.size for reg in [  #pylint: disable=E1103
                            REG_IN1,
                            REG_IN2,
                         ]])


class DIGIRAIL_2AInstrument(minimalmodbus.Instrument, Loggable):
    """ minimalmodbus.Instrument sub-class modeling the sharky.

    The supported model is the RTU RS485 one, the RS485 bus being connected
    via a USB.RS485 interface.
    """

    BAUDRATE = 19200

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

    def __init__(self, port, unit_id, outputs):
        """
        :param str port: serial port on which the RS485 interface is connected
        :param int unit_id: the address of the device
        """
        minimalmodbus.Instrument.__init__(self,
                                          port=port,
                                          slaveaddress=int(unit_id))

        self.serial.baudrate = self.BAUDRATE
        self.serial.parity = serial.PARITY_EVEN
        self.serial.stopbits = serial.STOPBITS_ONE
        self._first_poll = True

        self.full_scale1 = float(outputs['in1']['full_scale'])
        self.real_scale1 = float(outputs['in1']['real_scale'])
        self.full_scale2 = float(outputs['in2']['full_scale'])
        self.real_scale2 = float(outputs['in2']['real_scale'])

        Loggable.__init__(self, logname='digirail_2a%03d' % self.address)
        self.log_info('in1:(fs=%f, rs=%f) in2:(fs=%f, rs=%f)',
                      self.full_scale1, self.real_scale1, self.full_scale2, self.real_scale2
                      )
        self.log_info('stop bits : %d', self.serial.stopbits)

    @property
    def unit_id(self):
        """ The id of the device """
        return self.address

    def reset(self):
        """ Resets operational mode """
        pass

    def poll(self):
        """ Reads the registers data and returns the
        values as a named tuple.

        """
        time.sleep(1)
        if self._first_poll:
            self._first_poll = False
            self.log_info('first poll -> reset device')
            self.reset()

        # since the input registers are contiguous, optimise the operation by reading them in a single request
        r_in1, r_in2 = struct.unpack(
            '>hh',
            self.read_string(REG_IN1.addr, 2)
        )

        return self.OutputValues(
            in1=r_in1 / self.full_scale1 * self.real_scale1,
            in2=r_in2 / self.full_scale2 * self.real_scale2
        )
