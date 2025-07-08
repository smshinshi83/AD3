"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2025-02-03

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import math
import time
import matplotlib.pyplot as plt
import sys
from dwfconstants import *


if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_byte()
hzAcq = 100e6
cSamples = 4096
rgdAnalog = (c_double*cSamples)()
rgwDigital = (c_uint16*cSamples)()

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

#open device
print("Opening first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == 0:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    print("failed to open device")
    quit()

dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) # 0 = the device will only be configured when FDwf###Configure is called


print("Generating signal on DIO 0")
# generate on DIO-0 25khz pulse (100MHz/10000/(7+3)), 30% duty (7low 3high)
dwf.FDwfDigitalOutEnableSet(hdwf, 0, 1)
dwf.FDwfDigitalOutDividerSet(hdwf, 0, 100)
dwf.FDwfDigitalOutCounterSet(hdwf, 0, 7, 3)
dwf.FDwfDigitalOutConfigure(hdwf, 1)


# For synchronous analog/digital acquisition set DigitalInTriggerSource to AnalogIn, start DigitalIn then AnalogIn
hzDI = c_double()
dwf.FDwfDigitalInInternalClockInfo(hdwf, byref(hzDI))
#sample rate = system frequency / divider
dwf.FDwfDigitalInDividerSet(hdwf, int(round(hzDI.value/hzAcq)))
# configure DigitalIn
dwf.FDwfDigitalInTriggerSourceSet(hdwf, trigsrcAnalogIn)
# 16bit per sample format
dwf.FDwfDigitalInSampleFormatSet(hdwf, 16)
# set number of sample to acquire
dwf.FDwfDigitalInBufferSizeSet(hdwf, int(cSamples))
#dwf.FDwfDigitalInTriggerPrefillSet(hdwf, int(cSamples/2)) # needed for WF 3.23.38 and earlier
dwf.FDwfDigitalInTriggerPositionSet(hdwf, int(cSamples/2)) # trigger position in middle of buffer
dwf.FDwfDigitalInConfigure(hdwf, 1, 0)

# configure AnalogIn
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(hzAcq))
dwf.FDwfAnalogInBufferSizeSet(hdwf, int(cSamples)) 
dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(0.0)) # trigger position in middle of buffer
dwf.FDwfAnalogInChannelEnableSet(hdwf, 0, 1) # C1
dwf.FDwfAnalogInChannelOffsetSet(hdwf, 0, c_double(0.0))
dwf.FDwfAnalogInChannelRangeSet(hdwf, 0, c_double(5.0))

if 1:
    #trigger on digital signal
    dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorDigitalIn)
    dwf.FDwfDigitalInTriggerSet(hdwf, 0, 0, 1, 0) # DIO-0 rising edge
else:
    # trigger on analog signal
    dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) 
    dwf.FDwfAnalogInTriggerTypeSet(hdwf, 0) # trigtypeEdge
    dwf.FDwfAnalogInTriggerChannelSet(hdwf, 0) # first channel
    dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(1.5)) # 1.5V
    dwf.FDwfAnalogInTriggerConditionSet(hdwf, 0)  # trigcondRisingPositive
    
dwf.FDwfAnalogInConfigure(hdwf, 1, 0)


# wait for the offset to settle after adjustment or on first open
# time.sleep(0.1)

# start DigitalIn and AnalogIn
dwf.FDwfDigitalInConfigure(hdwf, 1, 1)
dwf.FDwfAnalogInConfigure(hdwf, 1, 1)

while True:
    if dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts)) == 0:
        szerr = create_string_buffer(512)
        dwf.FDwfGetLastErrorMsg(szerr)
        print(str(szerr.value))
        quit()
    if sts.value == DwfStateDone.value : break
    
while True:
    if dwf.FDwfAnalogInStatus(hdwf, 1, byref(sts)) == 0:
        szerr = create_string_buffer(512)
        dwf.FDwfGetLastErrorMsg(szerr)
        print(str(szerr.value))
        quit()
    if sts.value == DwfStateDone.value : break

# read data
dwf.FDwfDigitalInStatusData(hdwf, rgwDigital, int(sizeof(c_uint16)*cSamples)) 
dwf.FDwfAnalogInStatusData(hdwf, 0, rgdAnalog, int(cSamples)) # get channel 1 data


dwf.FDwfDigitalOutReset(hdwf)
dwf.FDwfDigitalOutConfigure(hdwf, 1)
dwf.FDwfDeviceCloseAll()

# plot
rgTime = [0.0]*(cSamples)
rgAnalog = [0.0]*(cSamples)
rgDigital = [0.0]*(cSamples)
for i in range(0,cSamples):
    rgTime[i] = (i-cSamples/2)/hzAcq
    rgAnalog[i] = rgdAnalog[i]
    rgDigital[i] = rgwDigital[i]&1 # mask DIO0

plt.plot(rgTime, rgAnalog, rgTime, rgDigital)
plt.show()


