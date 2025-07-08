import ctypes
import sys
import os
import time
from dwfconstants import *

# detect OS platform
if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))


dwf.FDwfParamSet(DwfParamDigitalVoltage, 1800) # mV 1.8V
dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown


print("Opening first device")
hdwf = c_int()
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

# 0 = device will be configured only when calling FDwf###Configure
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0)

hzPlay = 100e3

nPlay = 16
bitsPerSamp = 4
# for 4 bits it will output 0 1 2 3 4 ...
rgbPlay = (c_ubyte*int(nPlay/2))(0x10, 0x32, 0x54, 0x76, 0x98, 0xBA, 0xDC, 0xFE) 

dwf.FDwfDigitalOutPlayRateSet(hdwf, c_double(hzPlay))
dwf.FDwfDigitalOutRepeatSet(hdwf, 1)
dwf.FDwfDigitalOutRunSet(hdwf, c_double(nPlay/hzPlay)) # run length

for i in range(0, bitsPerSamp):
    dwf.FDwfDigitalOutEnableSet(hdwf, i, 1)
    dwf.FDwfDigitalOutTypeSet(hdwf, i, DwfDigitalOutTypePlay) 
    dwf.FDwfDigitalOutIdleSet(hdwf, i, DwfDigitalOutIdleLow)

dwf.FDwfDigitalOutPlayDataSet(hdwf, byref(rgbPlay), bitsPerSamp, int(nPlay))
dwf.FDwfDigitalOutConfigure(hdwf, 1)

dwf.FDwfDeviceCloseAll()
