

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


class PrinterClassInfo(object):
    """PrinterClassInfo is to be subclassed for different types of
    printers.  These classes are used by the driver to report the
    divined information about the printers they control.  These
    describe things common within a class of printers, eg a Lulzbot
    TAZ, a Makerbot Replicator, an Ultimaker should all use the
    FFFInfo."""

    def __init__(self):
        self.printer_type = "Generic 3D Printer"
        self.volume = [0, 0, 0]


class FFFInfo(PrinterType):
    """This PrinteClassInfo subclass describes common capabilities to
    FFF printers."""

    def __init__(self):
        PrinterClassInfo(self)
        self.printer_type = "FFF 3D Printer"
        self.tools = 1
        self.heated_bed = False


class SLAInfo(PrinterType):
    def __init__(self):
        raise NotImplementedError()


class DLPInfo(PrinterType):
    def __init__(self):
        raise NotImplementedError()
