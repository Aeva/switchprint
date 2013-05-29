

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


import sys
from switchprint._workers import drivers


def on_connect(bus_type, handler, *event_args):
    print "Connect event"
    print "Handler:", handler
    num = 0
    for arg in event_args:
        print "Arg {0}: {1}".format(num, arg)
        num += 1

    for driver_name, driver_data in drivers.find("hardware", handler).items():
        driver = driver_data["driver"]()
        if handler == "usbACM":
            device_path, serial_port, device_info = event_args
            if driver.auto_detect(serial_port):
                print "Device enumerated!"


if __name__ == "__main__":
    on_connect(*sys.argv[1:])
