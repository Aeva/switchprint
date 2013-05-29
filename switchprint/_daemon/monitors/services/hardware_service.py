

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


import uuid, hashlib
import gobject, dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from switchprint._workers import drivers


def checksum_uuid(text):
    return uuid.UUID(hashlib.sha1(text).hexdigest()[:32])


class HardwareService(dbus.service.Object):
    """This class provides basic functionality for hardware detection
    services to use to respond to hardware events.  This also provides
    the dbus functionality representing a printer, by wrapping the
    driver object.  Thus, when a device enumerates successfully, this
    object 'becomes' a dbus.service.Object."""

    def __init__(self, bus_type, hardware_types):
        self.namespace = "org.voxelpress.hardware"
        self.base_path = "/org/voxelpress/hardware"

        if bus_type == "session":
            self.bus = dbus.SessionBus()
        elif bus_type == "system":
            self.bus = dbus.SystemBus()

        self.drivers = {}
        for hardware_type in hardware_types:
            for name, driver in drivers.find("hardware", hardware_type).items():
                self.drivers[name] = driver

    def register(self, driver, hw_path, other_info):
        """This function registers the HardwareService - which should
        normally be ran as a subprocess - as dbus service.  This
        function is called automatically when a driver successfully
        recognizes the hardware.

        This function also activates an event loop, and thus blocks
        indefinitely."""

        printer_uuid = None
        if driver.uuid:
            printer_uuid = driver.uuid
        else:
            info_string= other_info + driver.post + driver.info
            printer_uuid = checksum_uuid(info_string)

        object_path = self.base_path+"/"+str(printer_uuid).replace("-", "_")
        bus_name = dbus.service.BusName(self.namespace, bus=self.bus)

        print "Printer connected:", printer_uuid

        main_loop = gobject.MainLoop()
        DBusGMainLoop(set_as_default=True)
        #dbus.service.Object.__init__(self, bus_name, object_path)
        #main_loop.run()
