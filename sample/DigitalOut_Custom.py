"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-08-21

   Requires:                       
       Python 2.7, 3
   Description:
   Generates a custom pattern
"""

from ctypes import *
from dwfconstants import *
import sys
import time
import numpy
import matplotlib.pyplot as plt


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

# continue running after device close
dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

print("Opening first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 


pin = 0
hzRate = 1e6
data_py = [1,1,0,0,0,0,1,1,0,0,1,0,1,0,1,0,1,0]
cBits = len(data_py)

# digital-in
hzDI = c_double()
dwf.FDwfDigitalInInternalClockInfo(hdwf, byref(hzDI))
print("DigitanIn base freq: "+str(hzDI.value/1e6)+"MHz")
#sample rate = system frequency / divider
dwf.FDwfDigitalInDividerSet(hdwf, int(hzDI.value/hzRate))
# 8 bit per sample format
dwf.FDwfDigitalInSampleFormatSet(hdwf, 16)
# set number of sample to acquire
rgwSamples = (c_int16*cBits)()
dwf.FDwfDigitalInBufferSizeSet(hdwf, cBits)
dwf.FDwfDigitalInTriggerSourceSet(hdwf, trigsrcDigitalOut) # trigsrcDetectorDigitalIn
dwf.FDwfDigitalInTriggerPositionSet(hdwf, cBits)
dwf.FDwfDigitalInInputOrderSet(hdwf, 1) # for Digital Discovery LSbits from: DIO24-39 DIN0-23
dwf.FDwfDigitalInConfigure(hdwf, 0, 1)


# digital-out
hzSys = c_double()
dwf.FDwfDigitalOutInternalClockInfo(hdwf, byref(hzSys))
print("DigitanOut base freq: "+str(hzSys.value/1e6)+"MHz")
# how many bytes we need to fit this many bits, (+7)/8
rgbdata = (c_ubyte*((cBits+7)>>3))(0) 
# array to bits in byte array
for i in range(cBits):
    if data_py[i] != 0:
        rgbdata[i>>3] |= 1<<(i&7)
        
# generate pattern
dwf.FDwfDigitalOutEnableSet(hdwf, pin, 1)
dwf.FDwfDigitalOutIdleSet(hdwf, pin, DwfDigitalOutIdleZet)
dwf.FDwfDigitalOutTypeSet(hdwf, pin, DwfDigitalOutTypeCustom)
# 100kHz sample rate
dwf.FDwfDigitalOutDividerSet(hdwf, pin, int(hzSys.value/hzRate)) # set sample rate
dwf.FDwfDigitalOutDataSet(hdwf, pin, byref(rgbdata), cBits)
dwf.FDwfDigitalOutRepeatSet(hdwf, 1)
dwf.FDwfDigitalOutRunSet(hdwf, c_double(cBits/hzRate))
dwf.FDwfDigitalOutConfigure(hdwf, 1)


while True:
    sts = c_int()
    dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts))
    print("Status:", str(sts.value))
    if sts.value == DwfStateDone.value : 
        break
print("   done")


dwf.FDwfDigitalInStatusData(hdwf, rgwSamples, 2*cBits)
dwf.FDwfDeviceCloseAll()

plt.plot(numpy.fromiter(rgwSamples, dtype = numpy.uint16))
plt.show()








