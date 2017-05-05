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

import pycstbox.hal.device as haldev
import pycstbox.digirail_2a.digirail_2a as digirail_2a
from pycstbox.hal import hal_device

_logger = logging.getLogger(__file__)

DEFAULT_PRECISION = 3


@hal_device(device_type="novus.digirail_2a", coordinator_type="modbus")
class DIGIRAIL_2A(haldev.PolledDevice):
    """ HAL device modeling the Digirail 2A converter.

    The extension adds the support of polling requests and CSTBox events
    publishing on D-Bus.
    """

    def __init__(self, coord, cfg):
        super(DIGIRAIL_2A, self).__init__(coord, cfg)
        self._hwdev = digirail_2a.DIGIRAIL_2AInstrument(coord.port, cfg.address, cfg.outputs)
