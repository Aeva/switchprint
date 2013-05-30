

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


class DriverBase:
    """Abstract base class for drivers to inherit from.  What is
    currently shown here is almost certainly not going to be the final
    api."""

    uuid = None

    def auto_detect(self, *args, **kargs):
        """Called by a hardware monitor durring a hardware connect
        event.  Return True if this driver claims the device.
        This function should also set self.uuid."""
        raise NotImplementedError()

    def inform_reconnect(self):
        """This function is called by a worker subprocess when a
        driver is detected, but the corresponding printer object
        already exists.  In which case, this function should return a
        simple argument list which can be pushed to the already
        existing service, so that it may call the informed_reconnect
        function in it's driver instance."""
        raise NotImplementedError()

    def informed_reconnect(self, *args):
        """The arguments for this function should match what is
        returned by inform_reconnect.  This causes the driver to
        disconnect from whatever device it thinks it is connected to,
        and attach to whatever ostensibly new device is described."""
        raise NotImplementedError()

    def debug(self, command):
        """Send a raw command to the printer and return its
        response."""
        raise NotImplementedError()
    
    def home(self, x_axis=True, y_axis=True, z_axis=True):
        """Moves the named axises until they trigger their
        endstops."""
        raise NotImplementedError()
