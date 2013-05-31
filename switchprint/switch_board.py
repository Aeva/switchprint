

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


from .common import *
from .printer_interface import PrinterInterface


class SwitchBoard:
    """Represents the main switchprint server.  Subclass this or just
    override the on_new_printer method to be notified when a new
    printer is attached."""

    def __init__(self, PrinterClass=PrinterInterface):
        self.__PrinterClass = PrinterClass
        self.__proxy = get_bus().get_object(
            "org.voxelpress.hardware", "/org/voxelpress/hardware")
        self.__printers = {}
        for printer_uuid in self.__proxy.get_printers():
            self.__new_printer_handler(str(printer_uuid))
        def new_printer_callback(printer_uuid):
            self.__new_printer_handler(printer_uuid)
        self.__proxy.connect_to_signal(
            "new_printer_notification",
            new_printer_callback)

    def __new_printer_handler(self, printer_uuid):
        """Used internally."""
        if not self.__printers.has_key(printer_uuid):
            printer = self.__PrinterClass(printer_uuid)
            self.__printers[printer_uuid] = printer
            self.on_new_printer(printer)
             
    def on_new_printer(self, printer):
        """Override this method to be notified of the presence of a
        new printer."""
        print "New Printer Available:", printer.uuid
