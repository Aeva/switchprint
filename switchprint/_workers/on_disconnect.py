

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


def on_disconnect(bus_type, handler, *event_args):
    print "Disconnect event"
    print "Handler:", handler
    num = 0
    for arg in event_args:
        print "Arg {0}: {1}".format(num, arg)
        num += 1

if __name__ == "__main__":
    on_disconnect(*sys.argv[1:])
