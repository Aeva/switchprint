

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

    def stream(self, data):
        """Called to stream commands to a printer.  This data is
        cached by switchprint, and streamed to the printer.  Host
        software may use this to run a print job.  When the host
        software is closed, the job may still continue."""
        raise NotImplementedError()
    
    def home(self, x_axis=True, y_axis=True, z_axis=True):
        """Moves the named axises until they trigger their
        endstops."""
        raise NotImplementedError()

    def set_zero(self):
        """Sets the current position of the printer to be the zero
        coordinate."""
        raise NotImplementedError()

    def relative_move(self, x=0, y=0, z=0):
        """Moves the printhead however many movements along each
        axis."""
        raise NotImplementedError()

    def absolute_move(self, x=None, y=None, z=None):
        """Moves the printhead to the provided coordinate.  Setting an
        axis to None assumes that axis remains unchanged."""
        raise NotImplementedError()

    def set_hotend_temp(self, temperature=0, hotend=0):
        """Sets the indicated hotend to the given temperature."""
        raise NotImplementedError()

    def set_bed_temp(self, temperature=0):
        """Sets the hot plate to the given temperature."""
        raise NotImplementedError()

    def get_temp(self):
        """Returns temperature infromation from all thermistors."""
        raise NotImplementedError()

    def get_position(self):
        """Returns the printhead's current position."""
        raise NotImplementedError()

    def get_status(self):
        """Returns the printer's state.  Eg if its printing or
        idle."""
        raise NotImplementedError()
