"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2025-04-02

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import time
import sys

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_byte()
IsEnabled = c_int()
vpp = c_double()
vpn = c_double()
wlim = c_double()

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

# set up analog IO channel nodes
#dwf.FDwfAnalogIOChannelNodeSet(hdwf, 3, 0, c_double(2.5)) # limit 2.5W, default 0 is auto
# enable positive supply
dwf.FDwfAnalogIOChannelNodeSet(hdwf, 0, 0, c_double(1)) 
# set voltage to 5 V
dwf.FDwfAnalogIOChannelNodeSet(hdwf, 0, 1, c_double(5.0)) 
# enable negative supply
dwf.FDwfAnalogIOChannelNodeSet(hdwf, 1, 0, c_double(1)) 
# set voltage to -5 V
dwf.FDwfAnalogIOChannelNodeSet(hdwf, 1, 1, c_double(-5.0)) 
# master enable
dwf.FDwfAnalogIOEnableSet(hdwf, 1)

for i in range(1, 11):
    # wait 1 second between readings
    time.sleep(1)
    # fetch analogIO status from device
    if dwf.FDwfAnalogIOStatus(hdwf) == 0:
        break

    # voltage readback
    dwf.FDwfAnalogIOChannelNodeStatus(hdwf, 0, 1, byref(vpp))
    dwf.FDwfAnalogIOChannelNodeStatus(hdwf, 1, 1, byref(vpn))
    dwf.FDwfAnalogIOChannelNodeStatus(hdwf, 3, 0, byref(wlim))
    
    print("Power Limit: " + str(round(wlim.value,3)) + " W")
    print("Positive Supply: " + str(round(vpp.value,3)) + " V")
    print("Negative Supply: " + str(round(vpn.value,3)) + " V")

dwf.FDwfDeviceClose(hdwf)
