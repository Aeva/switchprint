

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


import sys, os, time
import textwrap
import serial
from switchprint.workers.drivers.capabilities import FFFInfo
from gcode_common import parse_capabilities, parse_bed_temp


class ConnectionException(Exception):
    pass


class SerialConnection:
    """Consolidates code pertaining to connecting to the serial port
    and some auto detection capabilities."""

    def __init__(self, port, baud=None):
        self.__s = None
        self.__port = None
        self.__baud = None
        self.post = ""
        self.reported = {}
        self.info = FFFInfo()

        bauds = (250000, 115200, 57600, 38400, 19200, 9600, 2400)
        assert baud in bauds or baud is None

        self.__control_ttyhup(port, True)
        error = None
        if baud:
            connected = self.__setup_port(port, baud)
            if not connected:
                error = """
                Initialization Error: Unable to initialize a
                connection with manually provided parameters."""
        else:
            connected = self.__auto_detect(port, bauds)
            if not connected:
                error = """
                Initialization Error: SprinterProtocol's autodetection
                capabilities failed to initialize the printer."""
            else:
                try:
                    self.info.tools = int(self.reported["extruder_count"])
                except KeyError:
                    pass
                try:
                    self.info.heated_bed = self.reported["heated_bed"]
                except KeyError:
                    pass
        if error:
            error = textwrap.dedent(error).strip()
            error = textwrap.fill(error)
            raise ConnectionException(error)

    def close(self):
        """Close the serial port."""
        self.__s.close()

    def connection_info(self):
        """Returns False if the connection was not established,
        otherwise returns (port, baud)."""
        
        if self.__s and self.__port and self.__baud:
            return self.__port, self.__baud
        else:
            return False

    def write(self, data):
        return self.__s.write(data)

    def readlines(self):
        return self.__s.readlines()

    def inWaiting(self):
        return self.__s.inWaiting()

    def __auto_detect(self, port, bauds):
        """Try to detect the appropriate baud rate for the printer."""
        for baud in bauds:
            try:
                connected = self.__setup_port(port, baud)
                if connected:
                    return True
            except ValueError:
                continue
            except IOError:
                continue

    def __setup_port(self, port, baud):
        """Connect to the serial port and divine some information."""
        self.__s = serial.Serial(port, baud, timeout=0)
        self.__reset()
        giveup = 20 # poll the device for about five seconds before giving in
        post = ""
        while post == "" and giveup > 0:
            # wait for the device to boot
            time.sleep(.25)
            post = "\n".join(self.__s.readlines()).strip()
            giveup -= 1
        for trigger in ("sprinter", "marlin"):
            if post.lower().count(trigger):
                self.__port = port
                self.__baud = baud
                self.post = post
                soup = self.__querie("M115")[0]
                self.reported = parse_capabilities(soup)
                temp = parse_bed_temp(self.__querie("M105")[0])
                self.reported["heated_bed"] = temp is not None
                return True
        return False

    def __querie(self, command):
        self.__s.write(command+"\n")
        data = []
        while True:
            data += self.__s.readlines()
            if data and data[-1].strip().startswith("ok"):
                extra = data.pop().strip()[2:]
                if extra:
                    data.append(extra)
                return map(str.strip, data)
            else:
                time.sleep(.05)

####### FIXME: 
# The following two functions should have explanations of what they
# actually do.  They are currently cargo code.  Are they necessary?
# If so, why are they necessary?  Why is __control_ttyhup necessary
# on Linux but not elsewhere?
                
    def __reset(self):
        """Resets the serial port.  Lifted from pronterface without
        really understanding what it does."""

        if self.__s:
            self.__s.setDTR(1)
            time.sleep(0.2)
            self.__s.setDTR(0)

    def __control_ttyhup(self, port, disable_hup):
        """Controls the HUPCL.  Lifted from pronterface without really
        understanding what it does."""

        if sys.platform == "linux2":
            if disable_hup:
                os.system("stty -F %s -hup" % port)
            else:
                os.system("stty -F %s hup" % port)

