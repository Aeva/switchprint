

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


def __parse_temp(soup, key):
    """Parses a temperature param from the soup returned by M105."""

    temp = None
    expr = key + r":[0-9.]+"
    search = re.findall(expr, soup.lower())
    if search:
        temp = float(search[0].split(":")[-1])
    return temp


def parse_tool_temp(soup):
    """Parse the tool temperature from the soup that M105 returns."""

    return __parse_temp(soup, 't')


def parse_bed_temp(soup):
    """Parse the bed temperature from the soup that M105 returns."""

    bed_temp = __parse_temp(soup, 'b')
    if bed_temp == 0:
        bed_temp = None
    return bed_temp


def parse_capabilities(soup):
    """Called by autodetect to parse the soup returned by the M115
    command, to divine meaningful information from the printer as
    reported by the firmware. """

    def clean(text):
        text = text.strip().lower()
        if text.endswith(":"):
            text = text[:-1]
        try:
            val = int(text)
        except ValueError:
            try:
                val = float(text)
            except ValueError:
                val = text
        return val

    keys = map(clean, re.findall("[A-Z_]+:", soup))
    values = map(clean, re.split("[A-Z_]+:", soup)[1:])
    infodict = dict(zip(keys, values))
    if not infodict.has_key("extruder_count"):
        infodict["extruder_count"] = 1
    return infodict
