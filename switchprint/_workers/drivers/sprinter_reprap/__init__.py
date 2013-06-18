

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
import gobject
import serial
from switchprint._workers.drivers.common import DriverBase


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


class Thermistor:
    """Represents the state of a thermistor on a Reprap."""
    
    def __init__(self, name):
        self.temperature = 0
        self.target = None
        self.name = name

    def update(self, temp, target):
        temp, target = map(float, (temp, target))
        if temp > 10:
           self.temperature = temp
        self.target = target 
        print "{0}: {1}c / {2}c".format(self.name, self.temperature, self.target)
        

class Driver(DriverBase):
    """Driver for reprap-style printers running the sprinter firmware."""

    def __init__(self):
        self.__s = None
        self.__port = None
        self.__uuid = "butts"
        self.__state = None
        self.bed_temp = Thermistor("bed")
        self.tool_temp = Thermistor("tool")

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
                if data and data[-1].strip().startswith("ok"):                    
                    extra = data.pop().strip()[2:]
                    if extra:
                        data.append(extra)
                    return map(str.strip, data)
                else:
                    time.sleep(.05)

    def change_state(self, new_state):
        """
        Changes the state of the listener event loop and thus the
        timeout delay as well.  "running" means that the printer has a
        buffer of commands that it is working through, "watching"
        means that the printer cannot safely stop monitoring itself,
        and "idle" means that the event loop is not running.
        """

        assert new_state in ["active", "watching", "idle"]
        timeout = None
        if new_state != self.__state:
            old_state = self.__state
            self.__state = new_state

            if old_state == "idle" or old_state == None:
                self.req_temp()
                self.listener()
                
    def req_temp(self):
        """
        Periodically called to request the temperature of the
        printer.
        """

        self.__write("M105")

        if self.__state != "idle":
            gobject.timeout_add(1000, self.req_temp)

    def update_temp(self, line):
        """Updates the current temperature readings."""
        parts = line.split(" ")[1:]
        pairs = zip(parts[:-2:2], parts[1:-2:2])
        for pair in pairs:
            temp_id, temp_current = pair[0].split(":")
            temp_target = pair[1][1:]

            thermistor = None
            if temp_id == "t":
                thermistor = self.tool_temp
            elif temp_id == "b":
                thermistor = self.bed_temp
            else:
                raise NotImplementedError("Uknown tool id: %s"%temp_id)
            if thermistor:
                thermistor.update(temp_current, temp_target)

    def listener(self):
        """
        The listener function is the body of the event loop that
        monitors feedback from the printer.
        """

        for line in self.__s.readlines():
            line = line.strip().lower()
            if not line:
                break

            if line.startswith("debug_"):
                continue

            if line.startswith("ok") and line.count("t:"):
                print line
                self.update_temp(line)

            if line.startswith("error"):
                # report an error...?
                raise NotImplementedError("Error handler")

            if line.startswith(("rs", "resend")):
                # checksum failed, resend line
                raise NotImplementedError("Resend command")

        delay = None
        if self.__state == "active":
            delay = .1
        elif self.__state == "watching":
            delay = .5
        if delay is not None:
            gobject.timeout_add(int(delay*1000), self.listener)
       
    def auto_detect(self, port):
        """Called by a hardware monitor durring a hardware connect
        event.  Return True if this driver claims the device.
        This function should also set self.uuid."""
        
        control_ttyhup(port, True)
        
        for baud in BAUDS[::-1]:
            try:
                self.reset()
                self.__s = serial.Serial(port, baud, timeout=0.25)
                time.sleep(1)
                post = "".join(self.__s.readlines()).strip()
                for trigger in ("sprinter", "marlin"):
                    if post.lower().count(trigger):
                        self.__port = port
                        self.__baud = baud
                        self.post = post
                        self.info = "".join(self.__write("M115", True))
                        #self.__write("M104 S100") # TEST REMOVE ME
                        #self.__write("M140 S60") # TEST REMOVE ME
                        self.change_state("active")
                        return True
            except ValueError:
                continue
            except IOError:
                continue

    def inform_reconnect(self):
        """This function is called by a worker subprocess when a
        driver is detected, but the corresponding printer object
        already exists.  In which case, this function should return a
        simple argument list which can be pushed to the already
        existing service, so that it may call the informed_reconnect
        function in it's driver instance."""
        return self.__port, self.__baud

    def informed_reconnect(self, port, baud):
        """The arguments for this function should match what is
        returned by inform_reconnect.  This causes the driver to
        disconnect from whatever device it thinks it is connected to,
        and attach to whatever ostensibly new device is described."""
        
        control_ttyhup(port, True)
        self.__port = port
        self.__baud = baud
        self.__s = serial.Serial(port, baud, timeout=0.25)
        time.sleep(1)
        self.post = "".join(self.__s.readlines()).strip()        
        self.info = "".join(self.__write("M115", True))


    #### printer control functions ###

    def debug(self, command):
        """Send a raw command to the printer and return its
        response.""" 
        return "".join(self.__write(command, True))
        

    def home(self, x_axis=False, y_axis=False, z_axis=False):
        """Moves the named axises until they trigger their
        endstops."""

        cmd = ["G28"]
        if x_axis:
            cmd.append("X0")
        if y_axis:
            cmd.append("Y0")
        if z_axis:
            cmd.append("Z0")
        self.__write(" ".join(cmd), True)

    
    def relative_mode(self):
        self.__write("G91")


    def absolute_mode(self):
        self.__write("G90")


    def move(self, x=0, y=0, z=0):
        cmd = "G0 X{0} Y{1} Z{2}".format(x, y, z)
        self.__write(cmd)


    def motors_off(self):
        self.__write("G18")
        self.__write("M84")


    def get_temperature(self):
        return self.__write("M105", True)[0]
