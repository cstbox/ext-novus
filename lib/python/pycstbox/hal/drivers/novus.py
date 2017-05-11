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

""" HAL interface classes for Novus supported products. """

import logging

import pycstbox.novus.digirail_2a as digirail_2a
from pycstbox.hal import hal_device
from pycstbox.modbus import RTUModbusHALDevice

_logger = logging.getLogger('novus')

DEFAULT_PRECISION = 3


@hal_device(device_type="novus.digirail_2a", coordinator_type="modbus")
class DigiRail_2A(RTUModbusHALDevice):
    """ HAL device modeling the Digirail 2A converter.

    The extension adds the support of polling requests and CSTBox events
    publishing on D-Bus.
    """

    def __init__(self, coord_cfg, dev_cfg):
        super(DigiRail_2A, self).__init__(coord_cfg, dev_cfg)
        self._hwdev = digirail_2a.DigiRail_2A(coord_cfg.port, dev_cfg.address)

        # cache the input type and unit
        self._output_defs = [
            (digirail_2a.INPUT_TYPE_CATEGORY_LABEL[i.input_type_category], i.unit)
            for i in self._hwdev.inputs
        ]

    def get_output_data_definition(self, output):
        return self._output_defs[int(output[-1]) - 1]

