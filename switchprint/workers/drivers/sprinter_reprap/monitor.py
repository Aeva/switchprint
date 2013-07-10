

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


import time, json
import gobject
from protocol import SprinterProtocol


class Timeout(object):
    def __init__(self, callback):
        self.__callback = callback
        self.__id = None
        self.dest = None # when the next timeout is estimated to fire
        
    def __trigger(self):
        """Wrapps the callback."""
        self.clear()
        self.__callback()
         
    def set(self, seconds):
        """Sets a timeout."""
        delay = int(1000*seconds)
        if self.__id is not None:
            # If there is currently a pending timeout, but the one
            # we're trying to set would fire sooner, cancel the
            # original timeout so this one can be set.
            if time.time() + delay < self.dest:
                self.clear()
        if self.__id is None:
            # If there is no currently set timeout, then schedule one.
            self.__id = gobject.timeout_add(delay, self.__trigger)
            self.dest = time.time() + delay

    def clear(self):
        """Clears any pending timeout."""
        if self.__id is not None:
            gobject.source_remove(self.__id)
            self.__id = None


class SprinterMonitor(object):
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
        self.proto = SprinterProtocol(serial, self)

        # 'idle', 'job_done', 'printing', 'paused, 'error'
        self.printer_state = 'idle'
        # 'active', 'hot', 'cool', 'idle'
        self.monitor_state = 'active'

        self.monitor_timer = Timeout(self.monitor_event_loop)
        self.report_timer = Timeout(self.report_status)
        self.temp_timer = Timeout(self.query_temp)

        self.proto.request_temps()
        self.__cue_monitor()
        self.query_temp()

    def get_max_temp_state(self):
        """The max temp returned is the highest of the set of all
        temperature states and temperature targets. If this number is
        less than or equal to 30, then "max_temp" will be set to None,
        indicating that the system is in fully cooled state and may be
        ignored.
        """
        
        readings = [self.proto.temps["b"]] + self.proto.temps["t"]
        targets = [self.proto.targets["b"]] + self.proto.targets["t"]
        targets = [i for i in targets if i is not None]
        union = readings + targets
        union.sort()
        max_temp = union.pop()
        
        # FIXME rather than an arbitrary definition of room
        # temperature or whatever '30' is supposed to represent, None
        # should be returned only after the change in temperature over
        # the last three minutes was less than a degree or something
        # like that AND its low enough that it won't likely start your
        # house on fire or cause burns to anyone who touches the hot
        # bits.

        return max_temp if max_temp > 30 else None

    def on_state_changed(self):
        """Called by the wrapped SprinterProtocol when its state has
        changed.  Currently, this is called when either a tool or the
        bed's target temperature is set, or when any tool or the bed's
        temperature is reported."""

        self.report_timer.set(1)

    def report_status(self):
        """Generate a report of the temperature and tool states, and
        push that info to the host via dbus signal."""

        status = {
            "thermistors" : {
                "tools": [],
                "bed" : (0, None),
                },
            "printer_state" : self.printer_state,
            }
        
        status["thermistors"]["bed"] = (
            self.proto.temps["b"], self.proto.targets["b"])
        for state in zip(self.proto.temps["t"], 
                         self.proto.targets["t"]):
            status["thermistors"]["tools"].append(state)
        self.__signals.on_report(json.dumps(status))

    def __change_monitor_state(self, new_state):
        """Changes the state of the monitor, and possibly initiates a
        timeout."""

        assert new_state in ['active', 'hot', 'cool', 'idle']
        if new_state != self.monitor_state:
            print "Monitor state is now", new_state
            old_state = self.monitor_state
            self.monitor_state = new_state
            if new_state in ['active', 'hot', 'cool']:
                self.temp_timer.set(1)
                
    def request(self, soup):
        """Takes a block of text, cleans it, and then adds it into the
        command queue.  Inferres where in the queue it should go from
        context."""

        if self.printer_state == "idle":
            self.proto.request(soup)

        elif self.printer_state in ("paused", "error"):
            self.proto.request(soup, interrupt=True)

        self.__change_monitor_state("active")
        self.__cue_monitor()
        
    def print_file(self, fileob):
        """Streams gcode from a file object to the printer."""
        raise NotImplementedError()

    def query_temp(self):
        """Periodically is called to query for temperature changes."""
        
        self.proto.request_temps()
        delay = None
        if self.monitor_state == "active":
            if self.printer_state == "printing":
                delay = 5
            else:
                delay = 2
        elif self.monitor_state == "hot":
            delay = 2
        elif self.monitor_state == "cool":
            delay = 5
        if delay is not None:
            self.temp_timer.set(delay)
        
    def __cue_monitor(self):
        """Schedules a monitor timeout, if one is not already
        scheduled.  The delay is determined by the printer's state."""
        
        seconds = .5
        if self.monitor_state == "active":
            seconds = .1
        elif self.monitor_state == "cool":
            seconds = 5
        self.monitor_timer.set(seconds)
        
    def monitor_event_loop(self):
        """Called periodically depending on the monitor status."""

        self.proto.execute_requests()
        
        if self.proto.buffer_status() == "active":
            self.__change_monitor_state("active")
            self.__cue_monitor()
        else:
            if self.monitor_state == "active":
                self.__change_monitor_state("hot")
                self.__cue_monitor()
            else:
                max_temp = self.get_max_temp_state()
                if not max_temp:
                    self.__change_monitor_state("idle")
                else:
                    if max_temp < 50:
                        self.__change_monitor_state("cool")
                    self.__cue_monitor()
            
            
