

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


import gobject
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop

import monitors
from switchprint._workers.common import list_printers
from switchprint import common


class SwitchBoard(dbus.service.Object):
    """The SwitchBoard class implements the dbus daemon for SwitchBoard."""
    
    def __init__(self):
        self.__bus = common.get_bus()
        bus_name = dbus.service.BusName(
            "org.voxelpress.hardware", bus=self.__bus)
        dbus.service.Object.__init__(
            self, bus_name, "/org/voxelpress/hardware")

    @dbus.service.method("org.voxelpress.hardware", in_signature='s')
    def worker_new_printer(self, printer_uuid):
        """Called by a worker subprocess when it creates a new
        PrintServer instance."""
        self.new_printer_notification(printer_uuid)
        
    @dbus.service.signal(dbus_interface='org.voxelpress.hardware', signature='s')
    def new_printer_notification(self, printer_uuid):
        """Signals when a new printer is available."""
        pass

    @dbus.service.method("org.voxelpress.hardware", out_signature='as')
    def get_printers(self):
        """Called by a worker subprocess when it creates a new
        PrintServer instance."""
        printers = []
        for namespace in list_printers():
            printers.append(namespace.split(".")[-1][1:].replace("_", "-"))
        return dbus.Array(printers)
        

def start_daemon():
    """
    Creates the switchprint daemon.
    """
    # TODO: daemonize this
    main_loop = gobject.MainLoop()
    DBusGMainLoop(set_as_default=True)

    common.bootstrap()

    switchboard = SwitchBoard()
    hardwaremon = monitors.HardwareMonitor()
    main_loop.run()
