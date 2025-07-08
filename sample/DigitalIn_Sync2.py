"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-10-28

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import math
import sys

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
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

print("Configuring Digital Out / In...")

# DIO-0 (DD DIO-24) 1MHz
dwf.FDwfDigitalOutEnableSet(hdwf, 0, 1)
dwf.FDwfDigitalOutDividerSet(hdwf, 0, 50)
dwf.FDwfDigitalOutCounterSet(hdwf, 0, 1, 1)

# DIO-1 (DD DIO-25) high
dwf.FDwfDigitalOutEnableSet(hdwf, 1, 1)
dwf.FDwfDigitalOutCounterInitSet(hdwf, 1, 1, 0)
dwf.FDwfDigitalOutCounterSet(hdwf, 1, 0, 0)

dwf.FDwfDigitalOutConfigure(hdwf, 1)

# set number of sample to acquire
nSamples = 100000
rgSamples = (c_uint64*nSamples)()
cAvailable = c_int()
cLost = c_int()
cCorrupted = c_int()
cSamples = 0
fLost = 0
fCorrupted = 0

# record mode
dwf.FDwfDigitalInAcquisitionModeSet(hdwf, acqmodeRecord)
# for sync mode set divider to -1 
dwf.FDwfDigitalInDividerSet(hdwf, -1)
# 64bit per sample format
dwf.FDwfDigitalInSampleFormatSet(hdwf, 64)
# number of samples 
dwf.FDwfDigitalInTriggerPositionSet(hdwf, nSamples)
# in sync mode the trigger is used for sampling condition
# trigger detector mask:          low &     hight & ( rising | falling )
dwf.FDwfDigitalInTriggerSet(hdwf, 0, 0, 1, 0) # DIO-0 (DD DIN-0) rising edge

# begin acquisition
dwf.FDwfDigitalInConfigure(hdwf, 0, 1)

print("Starting sync record...")

while cSamples < nSamples:
    dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts))
    if cSamples == 0 and (sts == DwfStateConfig or sts == DwfStatePrefill or sts == DwfStateArmed) :
        # acquisition not yet started.
        continue

    dwf.FDwfDigitalInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupted))

    cSamples += cLost.value
    
    if cLost.value :
        fLost = 1
    if cCorrupted.value :
        fCorrupted = 1

    if cAvailable.value==0 :
        continue

    if cSamples+cAvailable.value > nSamples :
        cAvailable = c_int(nSamples-cSamples)
    
    # get samples
    dwf.FDwfDigitalInStatusData(hdwf, byref(rgSamples, 8*cSamples), c_int(8*cAvailable.value))
    cSamples += cAvailable.value

dwf.FDwfDeviceClose(hdwf)

print("   done")
if fLost:
    print("Samples were lost! Reduce sample rate")
if cCorrupted:
    print("Samples could be corrupted! Reduce sample rate")

f = open("record.csv", "w")
for v in rgSamples:
    f.write(hex(v))
    f.write("\n")
f.close()
