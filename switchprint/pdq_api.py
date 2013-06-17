

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
import dbus
from switchprint._workers import common as _common
from switchprint.common import get_bus


def get_printers():
    bus = get_bus()
    printers = {}
    for namespace in _common.list_printers():
        printer_uuid = uuid.UUID(namespace.split(".")[-1][1:].replace("_", "-"))
        object_path = "/" + namespace.replace(".", "/")
        proxy = bus.get_object(namespace, object_path)
        printers[printer_uuid] = PrinterInterface(printer_uuid, proxy)
    return printers
                      

class PrinterInterface:
    def __init__(self, printer_uuid, dbus_proxy):
        self.uuid = printer_uuid
        self.proxy = dbus_proxy

    def debug(self, command):
        return self.proxy.debug(str(command))

    def home(self, x_axis=True, y_axis=True, z_axis=True):
        self.proxy.home(x_axis, y_axis, z_axis)

    def relative_mode(self):
        self.proxy.relative_mode()

    def absolute_mode(self):
        self.proxy.absolute_mode()

    def move(self, x, y, z):
        self.proxy.move(x, y, z)


if __name__ == "__main__":
    import pdb; pdb.set_trace()
