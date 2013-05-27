

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
from hardware_service import HardwareService


class HardwareSubprocess(HardwareService):
    """Subprocess for responding to hardware events, so as not to
    stall the main thread."""
    
    def __init__(self, bus_type, state, hint, usb_path, tty_path=None, hw_info=None):
        HardwareService.__init__(self, bus_type, ["usbACM"])
        
        if state == "connect":
            print "A device was connected:"
            print hint, usb_path, tty_path, hw_info

        elif state == "disconnect":
            print "A device was disconnected:"
            print hint, usb_path, tty_path, hw_info


if __name__ == "__main__":
    # this should only happen because this was launched as a
    # subprocess.

    hws = HardwareSubprocess(*sys.argv[1:])
    
    
