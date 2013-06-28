

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


import time, re, types


class SprinterPacket(object):
    """
    Represents a line of gcode being sent to the printer.
    """

    def __init__(self, num, cmd, serial):
        self.__serial = serial
        cmd = cmd.strip()
        self.number = num
        self.line = "N{0} {1}".format(num, cmd) if num else cmd
        self.check = num is not None

        self.result = []
        self.status = "pending"

    def checksum(self):
        """Generates the checksum for an N-code line.  Copied from
        pronterface."""
        return reduce(lambda x, y:x^y, map(ord, self.line))

    def send(self):
        """Send the packet to the printer, and return the status of
        the packet."""

        line = self.line
        if self.check:
            line += "*%s" % self.checksum()
        self.__serial.write(line+"\n")
        return self.check_status()
            
    def check_status(self):
        """Read new data from the printer, determine if the packet
        needs to be resent or not, otherwise return status.  The
        status will be set to 'ok' when the transaction is
        complete."""

        self.result += map(str.strip, self.__serial.readlines())

        if self.result:
            for line in self.result:
                if line.startswith("Resend"):
                    request = int(line.split(":")[-1].strip())
                    assert request == self.number
                    self.result = []
                    self.status = "pending"
                    return self.send()
    
            if self.result[-1].startswith("ok"):
                self.status = "ok"
        return self.status


class SprinterProtocol(object):
    """
    Implements a mechanism in which commands may be sent to the
    printer in an orderly fashion.  Does state tracking."""

    def __init__(self, connection, callbacks):
        self.__callbacks = callbacks
        self.__serial = connection
        self.info = self.__serial.info

        self.tool = 0
        self.temps = {
            "b" : 0,
            "t" : [0],
            }
        self.targets = {
            "b" : None,
            "t" : [None],
            }

        self.line = 1
        self.interrupts = []
        self.buffer = []
        self.pending = None

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

        if interrupt:
            def closure():
                return soup
            self.interrupts.append(closure)
        else:
            self.buffer += self.__clean(soup)

    def buffer_status(self):
        """Returns either 'idle', if both buffers are empty and there
        are no pending commands, otherwise returns 'active'."""
        
        queued = len(self.buffer) + len(self.interrupts)
        if queued == 0 and self.pending is None:
            return "idle"
        else:
            return "active"

    def request_temps(self):
        """Requests a temperature report for all connected tools as
        well as the hot plate, where applicable.  Takes care of
        automatic tool changes, etc.
        """

        def interrupt():
            hold = self.tool
            count = int(self.info["extruder_count"])
            tools = [(i+self.tool) % count for i in range(count)]
            soup = []
            for tool in tools:
                if tool != hold:
                    soup.append("T%s" % tool)
                soup.append("M105")
            if len(tools) > 1:
                soup.append("T%s" % hold)
            return "\n".join(soup)
        self.interrupts.append(interrupt)

    def execute_requests(self):
        """First, execute all pending interrupts.  Then process a few
        pending requests from the buffer.
        """
        
        # first, check to see if the last command got a response:
        if self.pending is not None:
            status = self.pending.check_status()
            if status == 'pending':
                return
            else:
                self.__process_response(self.pending.result)
                self.pending = None
                self.line += 1
        
        # next, dump all pending interrupts in front of the buffer:
        while self.interrupts:
            soup = self.interrupts.pop(0)()
            self.buffer = self.__clean(soup) + self.buffer

        state = 'ok'
        hold_time = 0
        self.hold_start = time.time()
        while state == 'ok' and self.buffer and hold_time < 1:
            # finally, stream the remaining commands off the buffer
            # until something trips:
            command = self.buffer.pop(0)
            print "-->", self.line, command
            self.__update_states(command)
            packet = SprinterPacket(self.line, command, self.__serial)
            state = packet.send()
            if state == 'pending':
                self.pending = packet
                print "Sleeping..."
                return
            else:
                self.__process_response(packet.result)
                self.line += 1
                hold_time = time.time() - self.hold_start
                print hold_time

    def __clean(self, soup):
        """Parses out valid gcode from a block of text.  Returns the
        result in a list of strings"""

        commands = []
        for raw in soup.split("\n"):
            line = raw.split(";")[0].strip().upper()
            if line:
                commands.append(line)
        return commands
            
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

            if simple.startswith("resend:"):
                line_num = int(line.split(":")[-1].strip())
                self.__resend(line_num)

            elif simple.startswith("echo:"):
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
                tool_temp = re.findall(r"t:[0-9.]+", simple)
                if tool_temp:
                    self.temps["t"][self.tool] = \
                        float(tool_temp[0].split(":")[-1])
                    self.on_state_changed()

                # next check to see if the line contains the bed temp
                # note that this is usually is on the same line as the
                # tool temp
                bed_temp = re.findall(r"b:[0-9.]+", simple)
                if bed_temp and bed_temp[0] != "b:0":
                    self.temps["b"] = \
                        float(bed_temp[0].split(":")[-1])
                    self.on_state_changed()
