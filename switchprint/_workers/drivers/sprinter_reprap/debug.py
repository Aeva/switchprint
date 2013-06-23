
import time
from connection import SerialConnection
from protocol import SprinterPacket, SprinterProtocol

HOME = "G28 X0 Y0 Z0"
TEMP = "M105"

SERIAL = SerialConnection("/dev/ttyACM0")
#LINE = 1
#
#def communicate(cmd):
#    global LINE
#    p = SprinterPacket(LINE, cmd, SERIAL)
#    status = p.send()
#    while status != 'ok':
#        time.sleep(.1)
#        status = p.check_status()
#    LINE += 1
#    return p.result

proto = SprinterProtocol(SERIAL)

test = """
M105
M105
M105
M105
M105
G28 X0 Y0 Z0
G0 X30 Y30
G0 X10 Y10
GO X20 Y0
M105
M110 N0
M105
M110 N100
G28 X0 Y0 Z0
GO X100 Y100
M105
M105
G28 X0 Y0 Z0
"""
proto.request(test)
while proto.buffer_status() == "active":
    proto.execute_requests()
    time.sleep(.1)


#import pdb; pdb.set_trace()
