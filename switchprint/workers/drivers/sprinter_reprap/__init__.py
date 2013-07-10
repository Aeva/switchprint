

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


import json, pickle, time
from switchprint.workers.drivers.driver_base import DriverBase
from connection import SerialConnection, ConnectionException
from monitor import SprinterMonitor


METADATA = {
    "hardware" : ["usbACM"],
    }


class Driver(DriverBase):
    """Driver for reprap-style printers running the sprinter
    firmware."""

    def __init__(self):
        self.serial = None
        self.monitor = None
        self.__signals = None

    def get_class_info(self):
        """Returns a PrinterClassInfo object, as defined in
        capabilities.py"""

        return self.serial.info

    def connect_events(self, server):
        """Called when the driver is attached to a print server, so
        that the driver may call signals on the server object."""

        self.__signals = server
        self.monitor = SprinterMonitor(self.serial, server)
        
    def auto_detect(self, port):
        """Called by a hardware monitor durring a hardware connect
        event.  Return True if this driver claims the device.
        This function should also set self.uuid."""

        try:
            self.serial = SerialConnection(port)
            self.info = pickle.dumps(self.serial.info) ### HACK
            return True
        except ConnectionException:
            return False

    def inform_reconnect(self):
        """This function is called by a worker subprocess when a
        driver is detected, but the corresponding printer object
        already exists.  In which case, this function should return a
        simple argument list which can be pushed to the already
        existing service, so that it may call the informed_reconnect
        function in it's driver instance."""
        return self.serial.connection_info()

    def informed_reconnect(self, port, baud):
        """The arguments for this function should match what is
        returned by inform_reconnect.  This causes the driver to
        disconnect from whatever device it thinks it is connected to,
        and attach to whatever ostensibly new device is described."""

        if self.serial:
            self.serial.close()
        self.serial = SerialConnection(port, baud)
        self.info = pickle.dumps(self.serial.info) ### hack
        self.connect_events(self.__signals)

    #### printer control functions ###
        

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
            
        self.monitor.request(" ".join(cmd))

    
    def relative_mode(self):
        self.monitor.request("G91")


    def absolute_mode(self):
        self.monitor.request("G90")


    def move(self, x=0, y=0, z=0):
        cmd = "G0 X{0} Y{1} Z{2}".format(x, y, z)
        self.monitor.request(cmd)


    def motors_off(self):
        self.monitor.request("M84")


    def set_tool_temp(self, tool, target):
        """Requests the given tool to be set to the specified
        temperature."""
        #FIXME maybe there should be a monitor command for this so
        #that it doesn't change the active tool?
        self.monitor.request("T{0}\nM104 S{1}".format(tool, target))
        
    def set_bed_temp(self, target):
        """Requests the print bed be set to the specified
        temperature."""

        self.monitor.request("M140 S{0}".format(target))
