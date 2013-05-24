

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


import os, sys
import gobject
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop


class SwitchBoard(dbus.service.Object):
    """The SwitchBoard class implements the dbus daemon for SwitchBoard."""
    
    def __init__(self, bus_type):
        self.__bus_type = bus_type
        if bus_type == "system":
            self.__bus = dbus.SystemBus()
        else:
            self.__bus = dbus.SessionBus()

        bus_name = dbus.service.BusName(
            "org.voxelpress.hardware", bus=self.__bus)
        dbus.service.Object.__init__(
            self, bus_name, "/org/voxelpress/hardware")
        

def daemon():
    """
    Creates the switchprint daemon.
    """

    bus_type = "session"
    
    if sys.platform == "linux2":
        if os.getuid() == 0:
            bustype = "system"
        elif not os.getgroups().count(20):
            # group 20 is 'dialout', which is required to access serial devices
            print """
FATAL ERROR:

When running switchprint as a non-root user, it is neccessary that the
user be in the 'dialout' group.  To add this user to the dialout, run
the following command:

$ sudo usermod -a -G dialout {0}
""".format(os.getlogin())
            exit(0)


    # TODO: daemonize this
    main_loop = gobject.MainLoop()
    DBusGMainLoop(set_as_default=True)
    switchboard = SwitchBoard(bus_type)
    main_loop.run()
