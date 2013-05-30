

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


import uuid
import hashlib


def checksum_uuid(text):
    return uuid.UUID(hashlib.sha1(text).hexdigest()[:32])


def assign_uuid(driver, hw_path, other_info):
    """This function deterministically generates a uuid for a given
    hardware entity.  This function is called on at least on_connect
    and on_disconnect to determine the relevant service identifier,
    and therefor must generate the same uuid for a given device each
    time it is connected."""

    printer_uuid = None
    if driver.uuid:
        printer_uuid = driver.uuid
    else:
        ### FIXME should use the device's post info when determining
        ### the uuid, but this information must be consistent (whereas
        ### it doesn't seem to show up consistently currently)
        #info_string= other_info + driver.post + driver.info
        info_string= other_info + driver.info
        printer_uuid = checksum_uuid(info_string)

    return printer_uuid


def path_from_uuid(printer_uuid):
    """Generates a DBUS object path from a uuid."""

    base_path = "/org/voxelpress/hardware/_"
    return base_path + str(printer_uuid).replace("-", "_")
    

def name_from_uuid(printer_uuid):
    """Generates a DBUS namespace from a uuid."""

    namespace = "org.voxelpress.hardware._"
    return namespace + str(printer_uuid).replace("-", "_")
    

def list_printers(bus):
    """List all currently existing Printer Servers."""

    return [str(v) for v in bus.list_names()
            if str(v).startswith("org.voxelpress.hardware.")]
