"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-09-13

   Requires:           
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import sys
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

dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

print("Opening first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

dwf.FDwfDeviceAutoConfigureSet(hdwf, 0)# 0 = the device will be configured only when calling FDwf###Configure

# dwf.FDwfDigitalIODriveSet(hdwf, 0, c_double(0.008), 2) # 8mA, 2=Fast

print("Generating pattern...")

hzPlay = 100e6

# for infinite playback fill the entire 256MiByte memory
nPlay = 256*1024*1024
rgbPlay = (c_uint8*int(nPlay))()

for i in range(len(rgbPlay)):
    rgbPlay[i] = c_uint8(i)

print("Configuring Digital Out...")

print("Samples:"+str(nPlay)+" Rate:"+str(hzPlay)+"Hz "+" Period:"+str(nPlay/hzPlay)+"s")
dwf.FDwfDigitalOutPlayRateSet(hdwf, c_double(hzPlay)) # play sample rate

if nPlay < 256*1024*1024 : # use wait if length is less than the 256MiB
    dwf.FDwfDigitalOutRunSet(hdwf, c_double(nPlay/hzPlay))
    dwf.FDwfDigitalOutWaitSet(hdwf, c_double(1e-6))
    dwf.FDwfDigitalOutRepeatSet(hdwf, 0) 

for i in range(8):
    dwf.FDwfDigitalOutEnableSet(hdwf, i, 1) # enable
    dwf.FDwfDigitalOutTypeSet(hdwf, i, DwfDigitalOutTypePlay)
    dwf.FDwfDigitalOutIdleSet(hdwf, i, DwfDigitalOutIdleLow)

#dwf.FDwfDigitalOutConfigure(hdwf, 0) # stop

# set play data array of 8 bit samples
if dwf.FDwfDigitalOutPlayDataSet(hdwf, byref(rgbPlay), c_uint(8), int(nPlay)) == 0:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

print("Starting Digital Out...")
if dwf.FDwfDigitalOutConfigure(hdwf, 1) == 0:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

dwf.FDwfDeviceCloseAll()
print("done")
