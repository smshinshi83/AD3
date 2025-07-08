"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-08-05

   Requires:                       
       Python 3
   Generate pulses on trigger
"""

from ctypes import *
from dwfconstants import *
import sys

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_byte()

dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

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


# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 

# set 1.8V digital IO voltage for devices which support 
dwf.FDwfDeviceParamSet(hdwf, DwfParamDigitalVoltage, 1800) # mV


iChannel = 0

dwf.FDwfDigitalOutEnableSet(hdwf, iChannel, 1)
dwf.FDwfDigitalOutTypeSet(hdwf, iChannel, DwfDigitalOutTypePulse)
dwf.FDwfDigitalOutIdleSet(hdwf, iChannel, DwfDigitalOutIdleZet)
dwf.FDwfDigitalOutCounterSet(hdwf, iChannel, 0, 0)
dwf.FDwfDigitalOutRunSet(hdwf, c_double(0.0011)) # seconds to run
dwf.FDwfDigitalOutRepeatSet(hdwf, 1)

print("Enter 0/1 to drive low/high for 1.1ms other to exit")
while True:
    i = input()
    if i=='0':
        dwf.FDwfDigitalOutCounterInitSet(hdwf, iChannel, 0, 0) 
    elif i=='1':
        dwf.FDwfDigitalOutCounterInitSet(hdwf, iChannel, 1, 0) 
    else:
        quit()
    
    if dwf.FDwfDigitalOutConfigure(hdwf, 1) == 0:
        print("failed to open device")
        szerr = create_string_buffer(512)
        dwf.FDwfGetLastErrorMsg(szerr)
        print(str(szerr.value))
        quit()

dwf.FDwfDeviceCloseAll()
