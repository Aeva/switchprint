

# This file is part of Switchprint.
#
# Switchprint is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Switchprint is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Switchprint.  If not, see <http://www.gnu.org/licenses/>.


import sys, os
import serial, time
from switchprint._drivers.common import DriverBase


METADATA = {
    "hardware" : ["usbACM"],
    }


BAUDS = (2400, 9600, 19200, 38400, 57600, 115200, 250000)


#lifted from pronterface without knowing what it does
def control_ttyhup(port, disable_hup):
    """Controls the HUPCL"""
    if sys.platform == "linux2":
        if disable_hup:
            os.system("stty -F %s -hup" % port)
        else:
            os.system("stty -F %s hup" % port)


class Driver(DriverBase):
    """Driver for reprap-style printers running the sprinter firmware."""

    def __init__(self):
        self.__s = None
        self.__port = None
        self.__uuid = "butts"

    def reset(self):
        if self.__s:
            #lifted from pronterface without knowing what it does
            self.__s.setDTR(1)
            time.sleep(0.2)
            self.__s.setDTR(0)

    def __write(self, command, block=False):
        self.__s.write(command+"\n")
        if block:
            data = []
            while True:
                data += self.__s.readlines()
                if data and data[-1].strip() == "ok":
                    data.pop()
                    return map(str.strip, data)
                else:
                    time.sleep(.05)
       
    def auto_detect(self, port):
        """Called by a hardware monitor durring a hardware connect
        event.  Return True if this driver claims the device.
        This function should also set self.uuid."""
        
        control_ttyhup(port, True)
        
        for baud in BAUDS[::-1]:
            try:
                self.reset()
                self.__s = serial.Serial(port, baud, timeout = 0.25)
                time.sleep(1)
                post = "".join(self.__s.readlines()).strip()
                for trigger in ("sprinter", "marlin"):
                    if post.lower().count(trigger):
                        self.__baud = baud
                        self.post = post
                        self.info = "".join(self.__write("M115", True))
                        return True
            except ValueError:
                continue
