

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


import os, sys, glob, json
import subprocess


class Driver:
    def __init__(self, namespace, manifest_path):
        with open(manifest_path) as manifest_file:
            manifest = json.load(manifest_file)
        self.hardware = manifest["hardware"]
        
    def launch(self):
        pass
        

def register(hw_type):
    driver_path = os.path.split(__file__)[0]
    manifests = glob.glob(os.path.join(driver_path, "*", "manifest.json"))
    drivers = {}
    for manifest in manifests:
        driver_path = os.path.split(manifest)[0]
        namespace = os.path.split(driver_path)[1]

        driver = Driver(namespace, manifest)
        if driver.hardware.count(hw_type):
            drivers[namespace] = driver

    return drivers
