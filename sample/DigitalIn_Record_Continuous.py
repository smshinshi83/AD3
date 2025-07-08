"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-09-04

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

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) # the instruments will only be configured when FDwf###Configure is called

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

print("Configuring Digital Out / In...")

# generate counter on the first 8 DIOs
for i in range(0, 8):
    dwf.FDwfDigitalOutEnableSet(hdwf, i, 1)
    dwf.FDwfDigitalOutDividerSet(hdwf, i, 1<<(i+3))
    dwf.FDwfDigitalOutCounterSet(hdwf, i, 22222, 22222)

dwf.FDwfDigitalOutConfigure(hdwf, 1)

# set number of sample to acquire
nSamples = 1000000
rgbSamples = (c_uint8*nSamples)()
iSample = 0
hzDI = c_double()

dwf.FDwfDigitalInInternalClockInfo(hdwf, byref(hzDI))
print("DigitanIn base freq: "+str(hzDI.value))

# in record mode samples after trigger are acquired only
dwf.FDwfDigitalInAcquisitionModeSet(hdwf, acqmodeRecord)
# sample rate = system frequency / divider 
dwf.FDwfDigitalInDividerSet(hdwf, int(hzDI.value/1000e3))
# 8bit per sample format
dwf.FDwfDigitalInSampleFormatSet(hdwf, 8)
# number of samples after trigger
dwf.FDwfDigitalInTriggerPositionSet(hdwf, 0)
# for Digital Discovery bit order: DIO24:31
dwf.FDwfDigitalInInputOrderSet(hdwf, 1)
# begin acquisition
dwf.FDwfDigitalInConfigure(hdwf, 0, 1)

cDiv = c_int(0)
dwf.FDwfDigitalInDividerGet(hdwf, byref(cDiv))
print(f"DigitanIn rate: {hzDI.value/cDiv.value/1e6}MHz {cDiv.value}")



plt.axis([0, len(rgbSamples), 0, 255])
plt.ion()
hl, = plt.plot([], [])
hl.set_xdata(range(0, len(rgbSamples)))

try:
    while True:
        sts = c_ubyte(0)
        cAvailable = c_int(0)
        cLost = c_int(0)
        cCorrupted = c_int(0)
        if dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts)) != 1:
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            print(szerr.value)
            break

        dwf.FDwfDigitalInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cCorrupted))
        
        if cLost.value :
            print("Samples were lost! Reduce sample rate")
        if cCorrupted.value :
            print("Samples could be corrupted! Reduce sample rate")

        # here we are using circular sample buffer
        iSample1 = 0
        cSample1 = cAvailable.value
        cSample2 = 0
        if cSample1 > nSamples: # more samples available than our allocated buffer size
            iSample1 = cSample1 - nSamples
            cSample1 = nSamples
        if iSample + cSample1 > nSamples: # buffer wrap
            cSample2 = iSample + cSample1 - nSamples
            cSample1 -= cSample2
        
        dwf.FDwfDigitalInStatusData2(hdwf, byref(rgbSamples, iSample), iSample1, cSample1)
        iSample += cSample1
        if cSample2 != 0:
            dwf.FDwfDigitalInStatusData2(hdwf, byref(rgbSamples), iSample1+cSample1, cSample2)
            iSample += cSample2
        iSample %= nSamples

        hl.set_ydata(rgbSamples)
        plt.draw()
        plt.pause(0.001)
        if plt.fignum_exists(num=1) != True :
            break

except KeyboardInterrupt:
    pass

dwf.FDwfDeviceClose(hdwf)
