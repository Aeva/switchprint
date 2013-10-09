

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
import pickle
from .common import *


class PrinterInterface:
    """Represents a connected printer."""

    def __init__(self, printer_uuid):
        self.__name = "org.voxelpress.hardware._"+printer_uuid.replace("-","_")
        self.__path = "/" + self.__name.replace(".", "/")
        self.__proxy = get_bus().get_object(self.__name, self.__path, introspect=False)
        self.uuid = uuid.UUID(printer_uuid)
        self.__proxy.connect_to_signal(
            "on_state_change",
            self.on_state_change)
        self.__proxy.connect_to_signal(
            "on_report",
            self.on_report)
        self.on_state_change("ready")
        self.__proxy.connect_to_signal(
            "on_pdq_print_progress",
            self.on_pdq_print_progress)
        self.__proxy.connect_to_signal(
            "on_pdq_print_complete",
            self.on_pdq_print_complete)

    def debug(self, command):
        return self.__proxy.debug(command)

    def get_class_info(self):
        """Returns the printer's class info object."""
        return pickle.loads(self.__proxy.get_class_info())

    def on_state_change(self, state):
        """Signals when the printer's status changes."""
        pass

    def on_report(self, blob):
        """Signals when there is new information availble from a printer."""
        pass

    def home(self, x_axis=False, y_axis=False, z_axis=False):
        self.__proxy.home(x_axis, y_axis, z_axis)

    def relative_mode(self):
        self.__proxy.relative_mode()

    def absolute_mode(self):
        self.__proxy.absolute_mode()

    def move(self, x, y, z):
        self.__proxy.move(x, y, z)

    def motors_off(self):
        self.__proxy.motors_off()

    def set_tool_temp(self, tool, target):
        self.__proxy.set_tool_temp(tool, target)

    def set_bed_temp(self, target):
        self.__proxy.set_bed_temp(target)

    #### FIXME: The following "pdq" method and signals were added to
    #### facilitate a demonstration and enable rudementry printing
    #### functionality.  They exist for demonstration, and should not
    #### be used for day to day printing.

    def pdq_request_print(self, path):
        self.__proxy.pdq_request_print(path)

    def on_pdq_print_progress(self, progress):
        pass

    def on_pdq_print_complete(self):
        pass
