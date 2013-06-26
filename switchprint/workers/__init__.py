

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
import subprocess


def create(event, *args):
    """Creates a worker subprocess to handle a particular event so
    they can be handled outside of the main process."""

    assert event in ("on_connect", "on_disconnect")
    script = os.path.join(os.path.split(__file__)[0], event+".py")
    _args = ["python", script] + map(str, list(args))
    subprocess.Popen(_args)
