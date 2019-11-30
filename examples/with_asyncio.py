#!/usr/bin/env python
# coding=utf-8
"""Retrieve GPS data with asyncio."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import asyncio
import serial
import serial.aio
import pynmea2


class Output(asyncio.Protocol):
    def connection_made(self, transport):
        """Initialize sentence buffer when the connection is made."""
        self.transport = transport
        print('port opened', transport)
        transport.serial.rts = False
        # to store/concatenate received data to make one sentence
        self.stored_buffer = ""

    def data_received(self, data):
        """Parse GPS sentence when the retrieved data makes one sentence."""
        try:
            str_data = data.decode()
        except UnicodeDecodeError:
            str_data = ""
        # detect line ending \r\n
        str_data = str_data.replace("\r", "")
        split_endings = str_data.rsplit("\n", 1)
        if len(split_endings) == 1:
            # no line endings. just concatenate data.
            self.stored_buffer += str_data
            return
        # the retrieved data contains the end of line
        self.stored_buffer += split_endings[0]
        # parse the GPS sentence
        try:
            msg = pynmea2.parse(self.stored_buffer)
            if msg.sentence_type == "GGA":
                print(msg.num_sats, msg.latitude, msg.longitude)
        except pynmea2.nmea.ParseError:
            pass
        finally:
            # start of new line
            self.stored_buffer = split_endings[1]

    def connection_lost(self, exc):
        print('port closed')
        asyncio.get_event_loop().stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    coro = serial.aio.create_serial_connection(loop, Output, '/dev/ttyAMA0', baudrate=9600)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
