

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


import dbus


BUS = None
def get_bus():
    """Determine which bus, if any, has org.voxelpress.hardware."""
    global BUS

    if BUS:
        return BUS
    
    for bus in [dbus.SessionBus(), dbus.SystemBus()]:
        names = [str(v) for v in bus.list_names()]
        if names.count("org.voxelpress.hardware"):
            BUS = bus
            return bus

    if not BUS:
        raise RuntimeError("switchprint daemon is not currently running.")
