

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


import os, glob
#__import__("switchprint._drivers.sprinter_reprap", fromlist=["Driver"])


def all_drivers():
    """Returns a dictionary of available drivers and their metadata."""

    driver_dir = os.path.split(__file__)[0]
    search = glob.glob(os.path.join(driver_dir, "*", "__init__.py"))
    drivers = {}
    
    for found in search:
        driver_path = os.path.split(found)[0]
        driver_name = os.path.split(driver_path)[1]
        imported = __import__("switchprint._drivers."+driver_name,
                          fromlist=["Driver", "METADATA"])
        drivers[driver_name] = imported.METADATA
        drivers[driver_name]["driver"] = imported.Driver

    return drivers


def find(key, value):
    """Search for drivers based on their metadata dictionary."""

    drivers = all_drivers()
    found = {}
    for name, meta in drivers.items():
        if meta.has_key(key):
            if meta[key] == value or meta[key].count(value):
                found[name] = meta
    
    return found
