

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
from .common import *


class PrinterInterface:
    """Represents a connected printer."""

    def __init__(self, printer_uuid):
        self.__name = "org.voxelpress.hardware._"+printer_uuid.replace("-","_")
        self.__path = "/" + self.__name.replace(".", "/")
        self.__proxy = get_bus().get_object(self.__name, self.__path)
        self.uuid = uuid.UUID(printer_uuid)

    def home(self, x_axis=True, y_axis=True, z_axis=True):
        self.__proxy.home(x_axis, y_axis, z_axis)

    def relative_mode(self):
        self.__proxy.relative_mode()

    def absolute_mode(self):
        self.__proxy.absolute_mode()

    def move(self, x, y, z):
        self.__proxy.move(x, y, z)
