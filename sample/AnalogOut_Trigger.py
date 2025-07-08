"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-08-07

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import time
from dwfconstants import *
import sys

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

#open device
print("Opening first device...")
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 

hzFreq = 1000
aoChannel = 0 # W1
dwf.FDwfAnalogOutNodeEnableSet(hdwf, aoChannel, AnalogOutNodeCarrier, 1)
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, aoChannel, AnalogOutNodeCarrier, funcSine)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, aoChannel, AnalogOutNodeCarrier, c_double(hzFreq))
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, aoChannel, AnalogOutNodeCarrier, c_double(1.5))
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, aoChannel, AnalogOutNodeCarrier, c_double(1.5))

if True: # TriggerIO 1
    dwf.FDwfAnalogOutTriggerSourceSet(hdwf, aoChannel, trigsrcExternal1)
else: # AnalogIn Channel 1
    dwf.FDwfAnalogOutTriggerSourceSet(hdwf, aoChannel, trigsrcDetectorAnalogIn)
    dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn)
    dwf.FDwfAnalogInTriggerTypeSet(hdwf, trigtypeEdge)
    dwf.FDwfAnalogInTriggerChannelSet(hdwf, 0) # Scope Channel 1
    dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(2.0)) # V
    dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeRise) 
    dwf.FDwfAnalogInConfigure(hdwf, 1, 0)

dwf.FDwfAnalogOutWaitSet(hdwf, aoChannel, c_double(0.0))
dwf.FDwfAnalogOutRunSet(hdwf, aoChannel, c_double(1.0/hzFreq)) # one period
dwf.FDwfAnalogOutRepeatSet(hdwf, aoChannel, 0) # infinite
dwf.FDwfAnalogOutRepeatTriggerSet(hdwf, aoChannel, 1)
if dwf.FDwfAnalogOutConfigure(hdwf, aoChannel, 1) == 0:
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

print("AWG armed")

dwf.FDwfDeviceClose(hdwf)
