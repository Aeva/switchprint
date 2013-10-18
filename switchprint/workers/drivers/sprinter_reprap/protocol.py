

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


import time, types
from gcode_common import parse_bed_temp, parse_tool_temp, clean


class StreamCache(object):
    """Stores pending GCODE instructions.  Differenciates betweent sent
    and unsent commands, allowing for interjections to be added to the
    stream."""

    def __init__(self):
        self.interrupts = []
        self.send_buffer = []
        self.pending = []
        self.__linenum = 0
        self.__magic_number = 4 # how many commands should be sent at once

    def feed(self, soup, interrupt=False):
        """Take a list of commands, a string of commands, etc, and add it to
        the queue to be sent."""

        pending = [i for i in soup.strip().split("\n")] if type(soup) == str \
                  else soup if type(soup) in (tuple, list) else None
        assert pending is not None
        for command in pending:
            if interrupt:
                self.interrupts.append(command)
            else:
                self.pending.append(command)

    def __wrap(self, line):
        """Adds the line number and checksum to give gcode soup."""
        self.__linenum += 1
        numbered = "N{0} {1}".format(self.__linenum, line.strip())
        checksum = reduce(lambda x, y:x^y, map(ord, numbered))
        return self.__linenum, numbered + "*{0}\n".format(checksum)

    def __send_prep(self, line_buffer, count):
        """Take 'count' lines from 'line_buffer', add line numbers to them,
        and dump them into self.send_buffer.  Returns the number of
        items actually added to the send buffer."""

        take = len(line_buffer) if len(line_buffer) < count else count
        for i in range(take):
            self.send_buffer.append(self.__wrap(line_buffer.pop(0)))
        return take

    def get_appetite(self):
        """Returns the number of statements pending to be sent."""
        return len(self.pending)

    def get_idle(self):
        """Returns true if the Cache is totally empty with no pending
        commands, and with the send buffer clear.  Otherwise, return
        True if there is work to be done."""
        
        pending = len(self.send_buffer) + \
                  len(self.interrupts) + \
                  len(self.pending)
        return pending == 0

    def nudge(self, req_num=None, erase=None):

        """If 'req_num' is defined, it will drop all items in the sent cache
        preceding the indicated line number.  If 'erase' is defined,
        it will simply erase that many entries from the beginning of
        the sent cache.  If req_num is defined, erase will not be honored.

        This command returns the next set of commands to be sent to
        the printer."""
        
        if type(req_num) is int and len(self.send_buffer) > 0:
            # This block cuts everything up to the given line number
            # out of the cache of sent lines.  It may have the side
            # effect of clearing the cache entirely.

            first_num = self.send_buffer[0][0]
            end_num = self.send_buffer[-1][0]
            if req_num > end_num:
                self.send_buffer = []
            elif req_num < first_num:
                raise RuntimeError(
                    "Line requested that is no longer in the queue!!")
            else:
                # yes, this overrides the erase argument
                erase = req_num - first_num
                            
        if type(erase) is int and erase > 0:
            # Erase the first part of the sent cache.
            self.send_buffer = self.send_buffer[erase:]

        grab_count = self.__magic_number - len(self.send_buffer)
        if grab_count > 0:
            grab_count -= self.__send_prep(self.interrupts, grab_count)
            if grab_count > 0:
                self.__send_prep(self.pending, grab_count)

        if self.send_buffer:
            return "".join([i[1] for i in self.send_buffer])
        else:
            return None


class SprinterProtocol(object):
    """
    Implements a mechanism in which commands may be sent to the
    printer in an orderly fashion.  Does state tracking."""

    def __init__(self, connection, callbacks):
        self.__callbacks = callbacks
        self.__serial = connection
        self.cache = StreamCache()

        self.tool = 0
        self.temps = {
            "b" : 0,
            "t" : [0],
            }
        self.targets = {
            "b" : None,
            "t" : [None],
            }

        self.hold_start = None

    def __get_callback(self, name):
        """Returns named callback function if available, otherwise
        returns None."""

        found = None
        if self.__callbacks is not None:
            try:
                callback = self.__callbacks.__getattribute__(name)
                if type(callback) in (types.FunctionType, types.MethodType):
                    found = callback
            except AttributeError:
                pass
        return found
        
    def on_state_changed(self):
        """Calls self.__callbacks.on_state_changed, if applicable."""
        
        callback = self.__get_callback("on_state_changed")
        if callback:
            callback()

    def request(self, soup, interrupt=False):
        """Takes a block of text, cleans it, and then adds it to the
        command queue.  If the interrupt argument is true, the soup
        will be added to the interrupt queue, to be cleaned later."""

        cache_idle = self.cache.get_idle()
        self.cache.feed(soup, interrupt)
        if cache_idle:
            self.__advance(cache_idle)

    def get_appetite(self):
        """Returns the number of statements pending to be sent."""
        return self.cache.get_appetite()

    def buffer_status(self):
        """Returns either 'idle', if both buffers are empty and there
        are no pending commands, otherwise returns 'active'."""

        return "idle" if self.cache.get_idle() else "active"

    def request_temps(self):
        """Requests a temperature report for all connected tools as
        well as the hot plate, where applicable.  Takes care of
        automatic tool changes, etc.
        """
        ####### FIXME verify that this actually works still?
        def interrupt():
            hold = self.tool
            count = self.__serial.info.tools
            tools = [(i+self.tool) % count for i in range(count)]
            soup = []
            for tool in tools:
                if tool != hold:
                    soup.append("T%s" % tool)
                soup.append("M105")
            if len(tools) > 1:
                soup.append("T%s" % hold)
            return "\n".join(soup)
        self.request(interrupt())

    def __advance(self, force=True):
        """Facilitates flow control with printer based on error message
        feedback."""

        ready = self.__serial.inWaiting() > 0
        cut = 0
        request = None
        if ready:
            results = self.__serial.readlines()
            cut = 0
            for result in results:
                if result.startswith("ok"):
                    cut += 1
                elif result.startswith("Resend"):
                    request = int(result.split(":")[-1].strip())
                    cut = None
                    break
            # also call process results for state-related events
            self.__process_response(results)

        if ready or force:
            next_block = self.cache.nudge(request, cut)
            if next_block:
                self.__serial.write(next_block)

    def execute_requests(self, timeout=1):
        """Facilitates flow control automatically.  If 'timeout' is zero, this
        will block until the stream is idle again.  Timeout should be
        given in seconds.
        """

        mark = time.time()
        dt = 0
        while timeout is not None or not self.cache.get_idle():
            self.__advance()

            dt = time.time()-mark
            if dt > timeout:
                break
            else:
                time.sleep(.1)
            
    def __update_states(self, command):
        """Updates internal states when applicable to a command,
        before it is sent."""

        parts = command.strip().split(" ")
        first = parts.pop(0)
        num = None
        cmd = None
        params = []
        if first[0] == "N":
            num = first
            cmd = parts.pop(0)
        else:
            cmd = first
        params = parts

        # to the best of my knowledge, the printer reports tool
        # changes, so we don't need to keep track of when we send a
        # toolchange command.

        # line reset command
        if cmd == "M110":
            self.line = int(params[0][1:]) # parse number from param eg from N333

        # change target temperature
        if cmd == "M104":
            while len(self.targets["t"]) < self.tool+1:
                self.targets["t"].append(None)
            target = [float(i[1:]) for i in params if i.startswith("S")][0]
            if target <= 18:
                # if target temperature is less than approximately 65 fahrenheit,
                # assume that we're turning the tool off
                target = None
            self.targets["t"][self.tool] = target
            self.on_state_changed()
            
        # change target bed temperature
        if cmd == "M140":
            target = [float(i[1:]) for i in params if i.startswith("S")][0]
            if target <= 18:
                # if target temperature is less than approximately 65 fahrenheit,
                # assume that we're turning the tool off
                target = None
            self.targets['b'] = target
            self.on_state_changed()
    
    def __process_response(self, response):
        """Read from the socket and call events where appropriate."""

        for line in response:
            simple = line.lower().strip()

            if simple.startswith("echo:"):
                if simple.count("active extruder:"):
                    # check to see if we changed tools
                    self.tool = int(simple.split(":")[-1].strip())
                    # update the temperature readings to make space
                    # for new tools
                    while len(self.temps["t"]) < self.tool+1:
                        self.temps["t"].append(0)

            elif line.startswith("Error"):
                pass

            elif line.startswith("DEBUG_"):
                pass

            else:
                # check for a state report

                # first check to see if the line contains the tool temp
                tool_temp = parse_tool_temp(simple)
                if tool_temp:
                    self.temps["t"][self.tool] = tool_temp
                    self.on_state_changed()

                # next check to see if the line contains the bed temp
                # note that this is usually is on the same line as the
                # tool temp
                bed_temp = parse_bed_temp(simple)
                if bed_temp:
                    self.temps["b"] = bed_temp
                    self.on_state_changed()
