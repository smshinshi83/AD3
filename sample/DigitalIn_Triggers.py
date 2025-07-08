"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-10-15

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import math
import time
import sys
import numpy
from dwfconstants import *


if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")


version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, 0) # run


def myfunc():
    
    hdwf = c_int()
    sts = c_byte()
    
    print("Opening first device")
    if dwf.FDwfDeviceOpen(-1, byref(hdwf)) == 0: return False

    # the device will only be configured when FDwf###Configure is called
    dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 
    
    dwf.FDwfDeviceParamSet(hdwf, DwfParamFrequency, int(125e6)) # 125MHz
    
    hzDI = c_double()
    dwf.FDwfDigitalInInternalClockInfo(hdwf, byref(hzDI))
    print("DigitanIn base freq: "+str(hzDI.value/1e6)+"MHz")
    #sample rate = system frequency / divider
    dwf.FDwfDigitalInDividerSet(hdwf, 1)

    # 16 bit per sample format
    dwf.FDwfDigitalInSampleFormatSet(hdwf, 16)
    # set number of sample to acquire
    cSamples = 4096 # up to 32us
    rgSamples = (c_uint16*cSamples)()
    dwf.FDwfDigitalInBufferSizeSet(hdwf, cSamples)
    dwf.FDwfDigitalInTriggerSourceSet(hdwf, trigsrcDetectorDigitalIn)
    dwf.FDwfDigitalInTriggerPositionSet(hdwf, cSamples)
    dwf.FDwfDigitalInTriggerSet(hdwf, 0, 0, 1<<0, 0) # DIO0 rising edge

    # begin acquisition
    if dwf.FDwfDigitalInConfigure(hdwf, 0, 1) == 0: return False

    print("Press Ctrl+C to stop")
    try:
        while True:
            while True:
                if dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts)) == 0: return False
                if sts.value == DwfStateDone.value :
                    break

            dwf.FDwfDigitalInStatusData(hdwf, rgSamples, 2*cSamples)
            for i in range(cSamples):
                if rgSamples[i] & (1<<1): # DIO1 high
                    print(f"DIO 0 rise to DIO 1 delay {1e6*i/hzDI.value}us")
                    break
                if i == cSamples-1:
                    print(f"DIO 0 rise to DIO 1 delay > {1e6*i/hzDI.value}us")
                    

    except KeyboardInterrupt:
        pass
        
    return True;
    
if myfunc() == False :
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

dwf.FDwfDeviceCloseAll()



