#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pycstbox.novus.digirail_2a import DigiRail_2A, INPUT_TYPE_TEMPERATURE
import serial
from pycstbox.minimalmodbus import register_serial_port

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'


PORT = '/dev/ttyUSB0'
MODBUS_ID = 1
BAUD_RATE = 19200

register_serial_port(PORT, baudrate=BAUD_RATE, parity=serial.PARITY_EVEN)


def test_read():
    dev = DigiRail_2A(port='/dev/ttyUSB0', unit_id=1)

    assert all((inp.input_type_category == INPUT_TYPE_TEMPERATURE for inp in dev.inputs))
    assert all((inp.unit == 'degC' for inp in dev.inputs))

    output = dev.poll()
    assert output
    dev.logger.info('readings: %s', output)
    assert 0 < output.in1 < 50
    assert 0 < output.in2 < 50
