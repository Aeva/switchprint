

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


import re
import time
from threading import Thread
from ..protocol import SprinterPacket, SprinterProtocol


class MockConnection():
    """
    Creates a mock connection object for testing the implementation of
    the communication protocol.  "lineset" is a list of lists,
    indicating what should be added to the readlines buffer after each
    write call.  If "lineset" is None, then this will append ['ok\n']
    into the buffer instead.
    """

    def __init__(self, lineset=None):
        self.info = {
            "extruder-count" : 2,
            }
        self.hits = 0
        self.lineset = lineset
        self.buffer = []

    def write(self, data):
        """
        This mock connection object uses a regular expression to
        verify that what is written to the connection is something
        resembling valid gcode, complete with checksum.  It does not
        check to see if the checksum or line number is correct.
        """

        if not data.startswith("M110"):
            ncode = r'N[0-9]+'
            cmd = r'( [GMT][0-9]{1,3})'
            params = r'( [A-Z][0-9]{1,3})*'
            checksum = r'\*[0-9]{1,3}'
            pattern = r'^' + ncode + cmd + params + checksum + r'$'
            print "##########", data
            assert re.match(pattern, data)
            assert data.endswith("\n")

        self.hits += 1
        if self.lineset is None:
            self.buffer += ["ok\n"]
        elif self.lineset:
            self.buffer += self.lineset.pop(0)

    def readlines(self):
        """
        Returns the current readlines buffer.  Also resets the current
        readlines buffer.
        """

        ret = self.buffer
        self.buffer = []
        return ret




def packet_resend_test():
    """Verify that a packet object behaves correctly when a resend
    request occurs."""

    lineset = [
        ['Error:checksum mismatch, Last Line:0\n', 
         'Resend:1\n', 'ok\n'],
        ['ok T:29.5 /5.0 B:29.5 /5.0\n']]
    con = MockConnection(lineset)

    # create packet
    packet = SprinterPacket(1, "M105", con)

    # assert default state
    assert packet.status == "pending"

    packet.send()
    # verify that the resend occured automatically
    assert con.hits == 2

    # assert that everything is going to be ok
    assert packet.status == "ok"




def buffer_run_test():
    """Run a bunch of commands through the protocol object and see if
    it returns."""

    con = MockConnection()
    proto = SprinterProtocol(con, None)

    soup = """
M105
M105
M105
M105
M105
G28 X0 Y0 Z0
G0 X30 Y30
G0 X10 Y10
G0 X20 Y0
M105
M110 N0
M105
M110 N100
G28 X0 Y0 Z0
G0 X100 Y100
M105
M105
G28 X0 Y0 Z0
"""
    
    def buffer_run():
        proto.request(soup)        
        while proto.buffer_status() == "active":
            proto.execute_requests()

    test_thread = Thread(target = buffer_run)
    test_thread.run()
    time.sleep(.5)
    
    assert not test_thread.is_alive()
