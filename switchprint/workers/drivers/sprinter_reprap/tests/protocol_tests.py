

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
from switchprint.workers.drivers.capabilities import FFFInfo
from ..protocol import StreamCache, SprinterProtocol


def corrupted_backlog_req_test():
    cache = StreamCache()
    # process a lot of soup, so that the backlog doesn't cover
    # everything (backlog max should be 500 lines)
    soup = "G0 X100 Y100\nGO X200 Y100\n"*2000
    cache.feed(soup)
    for i in range(1000):
        cache.nudge(erase=3)
    reference_point = cache.send_buffer[0][-1]
    got = cache.nudge(req_num=6) # something obviously out of bounds
    mess = got.strip().split("\n")
    check_point = mess[0]+"\n"
    assert reference_point == check_point

    
    

