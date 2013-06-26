

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


import gobject
from protocol import SprinterProtocol



class SprinterMonitor:
    """Implements a gobject-based threadless eventloop, which hooks
    into SprinterProtocol to facilitate highlevel communication with
    the printer, as well as pushing the printer's state to the
    host.

    It may be safely assumed that when this class is instanced, the
    printer is in a live state, and everything else is connected
    already."""

    def __init__(self, serial, server):
        self.__serial = serial
        self.__signals = server
        self.info = serial.info

        # 'idle', 'job_done', 'printing', 'paused, 'error'
        self.printer_state = 'idle'
        # 'active', 'hot', 'idle'
        self.monitor_state = 'active'

        self.proto = SprinterProtocol(serial, None)

        self.x = 0
        self.y = 0
        self.z = 0

        self.bed_temp = 0
        self.tool_temps = [0] * self.info["extruder_count"]

        self.__monitor_timeout = None

    def __cue_monitor(self):
        """Schedules a monitor timeout, if one is not already
        scheduled.  The delay is determined by the printer's state."""
        
        seconds = .1 # FIXME determine delay from context

        delay = int(1000*seconds)
        if self.__monitor_timeout is None:
            tid = gobject.timeout_add(delay, self.monitor_event_loop)
            self.__monitor_timeout = tid

    def __clear_monitor(self):
        """Clears the monitor timeout."""
        gobject.source_remove(self.__monitor_timeout)
        self.__monitor_timeout = None

    def __change_monitor_state(self, new_state):
        """Changes the state of the monitor, and possibly initiates a
        timeout."""

        assert new_state in ['active', 'hot', 'idle']
        if new_state != self.monitor_state:
            old_state = self.monitor_state
            self.monitor_state = new_state

        if new_state in ['active', 'hot']:
            self.__cue_monitor()
                
    def request(self, soup):
        """Takes a block of text, cleans it, and then adds it into the
        command queue.  Inferres where in the queue it should go from
        context."""

        if self.printer_state == "idle":
            self.proto.request(soup)

        elif self.printer_state in ("paused", "error"):
            self.proto.request(soup, interrupt=True)

        self.__change_monitor_state("active")
        
    def print_file(self, fileob):
        """Streams gcode from a file object to the printer."""
        raise NotImplementedError()

    def monitor_event_loop(self):
        """Called periodically depending on the monitor status."""

        self.__clear_monitor()
        self.proto.execute_requests()
        #if proto.buffer_status() == "active":
        #    pass
        self.__cue_monitor()
