"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-09-27

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import math
import sys
import matplotlib.pyplot as plt
import numpy


if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_ubyte()

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

# generate counter
dwf.FDwfDigitalOutEnableSet(hdwf, c_int(i), c_int(1))
dwf.FDwfDigitalOutDividerSet(hdwf, c_int(i), c_int(1<<i))
dwf.FDwfDigitalOutCounterSet(hdwf, c_int(i), c_int(1000), c_int(1000))

dwf.FDwfDigitalOutConfigure(hdwf, c_int(1))

# set number of sample to acquire
nSamples = 100000
rgSamples = (c_uint64*nSamples)()
cAvailable = c_int()
cLost = c_int()
cCorrupted = c_int()
fLost = 0
fCorrupted = 0
hzDI = c_double()
fA = 0

dwf.FDwfDigitalInInternalClockInfo(hdwf, byref(hzDI))
dwf.FDwfDigitalInAcquisitionModeSet(hdwf, acqmodeRecord)
dwf.FDwfDigitalInDividerSet(hdwf, int(hzDI.value/100e6))
# Digital Discovery supports compression with 64bit sampling
dwf.FDwfDigitalInSampleFormatSet(hdwf, 64) 
dwf.FDwfDigitalInTriggerPositionSet(hdwf, -1) # continuous record
# for Digital Discovery bit order: DIO24:39 + DIN0:23
dwf.FDwfDigitalInInputOrderSet(hdwf, 1)
# begin acquisition
dwf.FDwfDigitalInConfigure(hdwf, 0, 1)

while True:
    dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts))
    dwf.FDwfDigitalInStatusCompress(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupted))
    
    if cLost.value :
        fLost = 1
    if cCorrupted.value :
        fCorrupted = 1
    if cAvailable.value > nSamples:
        fLost = 1
        cAvailable.value = nSamples
        
    
    dwf.FDwfDigitalInStatusCompressed(hdwf, byref(rgSamples), 8*cAvailable.value))
    for i in range(0, cAvailable.value, 2):
        if rgSamples[i]&1 == fA

    if sts.value == DwfStateDone.value :
        break

dwf.FDwfDeviceClose(hdwf)

if iSample != 0 :
    rgwSamples = rgwSamples[iSample:]+rgwSamples[:iSample]

print("  done")
if fLost:
    print("Samples were lost! Reduce sample rate")
if fCorrupted:
    print("Samples could be corrupted! Reduce sample rate")

f = open("record.csv", "w")
for v in rgwSamples:
    f.write("%s\n" % v)
f.close()

plt.plot(numpy.fromiter(rgwSamples, dtype = numpy.uint16))
plt.show()
