

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


import os, sys, re
from subprocess import check_output
import dbus


__ENV = {
    "bus" : None,
    "config" : None,
    "active" : False,
}


def get_bus():
    """Returns the bus object for org.voxelpress.hardware."""

    global __ENV
    if __ENV["bus"]:
        return __ENV["bus"]

    for bus in [dbus.SystemBus(), dbus.SessionBus()]:
        search = [str(v) for v in bus.list_names()]
        if search.count("org.voxelpress.hardware"):
            __ENV["bus"] = bus
            __ENV["active"] = True
            return bus
    return None


def __populate_etc(config_path):
    """Populate the configuration directory."""
    os.mkdir(config_path)


def bootstrap():
    """Determines environmental information that will be useful for
    the switchprint daemon."""

    def barf(msg):
        msg = "\nFATALERROR:\n\n%s\n" % msg.strip()
        raise RuntimeError(msg)

    global __ENV
    get_bus()
    if __ENV["active"]:
        barf("The switchprint daemon is already running.")
    
    if sys.platform == "linux2":
        dialout_group = check_output(("getent", "group", "dialout"))
        dialout_group = int(re.findall(r'\d+', dialout_group)[0])

        if os.getuid() == 0:
            __ENV["bus"] = dbus.SystemBus()
            __ENV["config"] = "/etc/voxelpress"
        elif not os.getgroups().count(dialout_group):
            # required to access serial devices
            barf("""
When running switchprint as a non-root user, it is neccessary that the
user be in the 'dialout' group.  To add this user to the dialout, run
the following command:

$ sudo usermod -a -G dialout {0}

After running this command, you will need to log out and log back in
again for the change to take effect. """.format(os.getlogin()))
            
    if not __ENV["bus"]:
        __ENV["bus"] = dbus.SessionBus()
        
    if not __ENV["config"]:
        __ENV["config"] = os.path.expanduser("~/.voxelpress")
    
    if not os.path.isdir(__ENV["config"]):
            __populate_etc(__ENV["config"])
