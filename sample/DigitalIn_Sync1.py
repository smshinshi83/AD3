"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2025-04-23

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import math
import sys
import time

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_byte()

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

print("Configuring Digital Out / In...")

# generate counter
for i in range(0, 16):
    dwf.FDwfDigitalOutEnableSet(hdwf, i, 1)
    dwf.FDwfDigitalOutDividerSet(hdwf, i, 1<<i)
    dwf.FDwfDigitalOutCounterSet(hdwf, i, 50, 50)
dwf.FDwfDigitalOutCounterInitSet(hdwf, 0, 0, 74) # shift LSbit used for clock

dwf.FDwfDigitalOutConfigure(hdwf, 0)

# set number of sample to acquire
nSamples = 1000
rg64Samples = (c_uint64*nSamples)()

# for sync mode set divider to -1 
dwf.FDwfDigitalInDividerSet(hdwf, -1)
# 16bit per sample format
dwf.FDwfDigitalInSampleFormatSet(hdwf, 64)
# for Digital Discovery bit order: DIO24:39; with 32 bit sampling [DIO24:39 + DIN0:15]
dwf.FDwfDigitalInInputOrderSet(hdwf, 1)
# number of samples 
dwf.FDwfDigitalInBuffersSet(hdwf, nSamples)
dwf.FDwfDigitalInTriggerPositionSet(hdwf, nSamples)
# in sync mode the trigger is used for sampling condition
# trigger detector mask:      low & high & ( rising | falling )
dwf.FDwfDigitalInTriggerSet(hdwf, 0, 0, 1<<0, 1<<0) # DIO-0 rising or falling edge


# begin acquisition
dwf.FDwfDigitalInConfigure(hdwf, 0, 1)

# start pattern
dwf.FDwfDigitalOutConfigure(hdwf, 1)


print("Waiting for acquisition...")
while True:
    dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts))
    if sts.value == stsDone.value :
        break
    time.sleep(0.01)
print("   done")

# get samples
dwf.FDwfDigitalInStatusData(hdwf, byref(rg64Samples), 8*nSamples) # 64bit samples 8 bytes *

dwf.FDwfDeviceClose(hdwf)

f = open("record.csv", "w")
for v in rg64Samples:
    f.write("%s\n" % v)
f.close()
