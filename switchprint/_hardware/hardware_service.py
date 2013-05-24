

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


import uuid
import gobject, dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop


class HardwareService(dbus.service.Object):
    """This class provides basic functionality for hardware detection
    services to use to respond to hardware events.  This also provides
    the dbus functionality representing a printer, by wrapping the
    driver object.  Thus, when a device enumerates successfully, this
    object 'becomes' a dbus.service.Object."""

    def __init__(self, bus_type):
        self.namespace = "org.voxelpress.hardware"
        self.base_path = "/org/voxelpress/hardware"

        if bus_type == "session":
            self.bus = dbus.SessionBus()
        elif bus_type == "system":
            self.bus = dbus.SystemBus()

    def register(self, driver):
        """This function registers the HardwareService - which should
        normally be ran as a subprocess - as dbus service.  This
        function is called automatically when a driver successfully
        recognizes the hardware.

        This function also activates an event loop, and thus blocks
        indefinitely."""

        uuid = (driver.uuid or uuid.uuid4()).replace("-", "_")
        object_path = self.base_path+"/"+uuid
        bus_name = dbus.service.BusName(self.namespace, bus=self.bus)
        dbus.service.Object.__init__(self, bus_name, object_path)

        main_loop = gobject.MainLoop()
        DBusGMainLoop(set_as_default=True)
        main_loop.run()
