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

dwf.FDwfDigitalOutConfigure(hdwf, 0)

# set number of sample to acquire
nSamples = 100000
rg64Samples = (c_uint64*nSamples)()
cAvailable = c_int()
cLost = c_int()
cCorrupt = c_int()
cSamples = 0
fLost = 0
fCorrupted = 0

# record mode
dwf.FDwfDigitalInAcquisitionModeSet(hdwf, acqmodeRecord)
# for sync mode set divider to -1 
dwf.FDwfDigitalInDividerSet(hdwf, -1)
# 16bit per sample format
dwf.FDwfDigitalInSampleFormatSet(hdwf, 64)
# for Digital Discovery bit order: DIO24:39; with 32 bit sampling [DIO24:39 + DIN0:15]
dwf.FDwfDigitalInInputOrderSet(hdwf, 1)
# number of samples 
dwf.FDwfDigitalInTriggerPositionSet(hdwf, nSamples)
# in sync mode the trigger is used for sampling condition
# trigger detector mask:      low & high & ( rising | falling )
dwf.FDwfDigitalInTriggerSet(hdwf, 0, 0, 1<<0, 1<<0) # DIO-0 rising or falling edge

# specially for Digital Discovery high-speed sampling we ca use sampling delay relative to edge
dwf.FDwfDigitalInTriggerCountSet(hdwf, 1, 1) # count 1 restart 1
dwf.FDwfDigitalInTriggerLengthSet(hdwf, c_double(20e-9), c_double(-1.0), 0) # minimum 10ns (20-10ns) delay, maximum -1, sync 0 normal


# begin acquisition
dwf.FDwfDigitalInConfigure(hdwf, 0, 1)

# start pattern
dwf.FDwfDigitalOutConfigure(hdwf, 1)

print("Starting sync record...")

while cSamples < nSamples:
    dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts))
    if cSamples == 0 and (sts == DwfStateConfig or sts == DwfStatePrefill or sts == DwfStateArmed) :
        # acquisition not yet started.
        continue

    dwf.FDwfDigitalInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupt))

    cSamples += cLost.value
    
    if cLost.value :
        fLost = 1
    if cCorrupt.value :
        fCorrupt = 1

    if cAvailable.value==0 :
        continue

    if cSamples+cAvailable.value > nSamples :
        cAvailable.value = nSamples-cSamples
    
    # get samples
    dwf.FDwfDigitalInStatusData(hdwf, byref(rg64Samples, 8*cSamples), 8*cAvailable.value) # 64bit samples 8 bytes *
    cSamples += cAvailable.value

dwf.FDwfDeviceClose(hdwf)

print("   done")
if fLost:
    print("Samples were lost! Reduce sample rate")
if cCorrupt:
    print("Samples could be corrupt! Reduce sample rate")

f = open("record.csv", "w")
for v in rg64Samples:
    f.write("%s\n" % v)
f.close()
