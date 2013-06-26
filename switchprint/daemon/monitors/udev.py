

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


import os
from switchprint import workers
import gudev


class HardwareMonitor():
    """This class implements the hardware monitor for systems in which
    udev is available.  Presumably that means just Linux."""
    
    def __init__(self):
        self.__udev = gudev.Client(["tty", "usb/usb_device"])
        self.__udev.connect("uevent", self.__udev_callback, None)
        self.__scan()

    def __udev_callback(self, client, action, device, user_data):
        hw_info = device.get_property("ID_SERIAL")
        subsystem = device.get_subsystem()

        if action == "add" and subsystem == "tty":
            usb_path = device.get_parent().get_parent().get_device_file()
            tty_path = device.get_device_file()
            self.__on_connect("usbACM", usb_path, tty_path, hw_info)
                
        elif action == "remove" and subsystem == "usb":
            usb_path = device.get_device_file()
            self.__on_disconnect("usbACM", usb_path)

    def __on_connect(self, hint, usb_path, tty_path, hw_info):
        workers.create("on_connect", hint, usb_path, tty_path, hw_info)

    def __on_disconnect(self, hint, usb_path):
        workers.create("on_disconnect", hint, usb_path)

    def __scan(self):
        """Iterate over available serial ports and try to find repraps."""
        for device in self.__udev.query_by_subsystem("tty"):
            hw_info = device.get_property("ID_SERIAL")
            if hw_info:
                try:
                    usb_path = device.get_parent().get_parent().get_device_file()
                    tty_path = device.get_device_file()
                except:
                    # FIXME ... not sure what to do =)
                    continue
                self.__on_connect("usbACM", usb_path, tty_path, hw_info)
