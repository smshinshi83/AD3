"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-01-03

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import time
import sys
import numpy
import math
import matplotlib.pyplot as plt



if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")


version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

# without this the outputs stops on close
dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown


#open device
"Opening first device..."
hdwf = c_int()
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 


channel = 0
cSamples = c_int()
dwf.FDwfAnalogOutNodeDataInfo(hdwf, channel, AnalogOutNodeCarrier, 0, byref(cSamples))
cSamples.value = int(cSamples.value/2) # half for double buffer

# samples between -1 and +1
rgdSamples = (c_double*cSamples.value)()
for i in range(0, len(rgdSamples)):
    rgdSamples[i] = math.sin(2.0*math.pi*i/cSamples.value);

print("Generating custom waveform...")
dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, 1)
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcDualCustom)  # supported by AD2
dwf.FDwfAnalogOutNodeDataSet(hdwf, channel, AnalogOutNodeCarrier, rgdSamples, cSamples)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(1e3)) 
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(2.0)) 
dwf.FDwfAnalogOutConfigure(hdwf, channel, 1) # start


time.sleep(1.0)
# capture
cCapture = 4096
rgdCapture = (c_double*cCapture)()
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(1e6))
dwf.FDwfAnalogInBufferSizeSet(hdwf, cCapture) 
dwf.FDwfAnalogInChannelEnableSet(hdwf, 0, 1)
dwf.FDwfAnalogInChannelRangeSet(hdwf, 0, c_double(5.0))
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcAnalogOut1) 
dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeEither)
dwf.FDwfAnalogInConfigure(hdwf, 0, 1)
time.sleep(0.01) # software wait or wait to be armed before changing the AWG


print("Changing waveform...")
c1 = cSamples.value
c2 = c1/2
c4 = c2/2
for i in range(0, len(rgdSamples)):
    rgdSamples[i] = (c4-abs(((c4+i) % c1) - c2))/c4;
dwf.FDwfAnalogOutNodeDataSet(hdwf, channel, AnalogOutNodeCarrier, rgdSamples, cSamples)
dwf.FDwfAnalogOutConfigure(hdwf, channel, 3) # apply

# wait for the capture
while True:
    sts = c_byte()
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    if sts.value == DwfStateDone.value :
        break
    
dwf.FDwfAnalogInStatusData(hdwf, 0, rgdCapture, cCapture)

# dwf.FDwfAnalogOutConfigure(hdwf, channel, 0) # stop
# output will continue to be generate with FDwfParamSet DwfParamOnClose 0
dwf.FDwfDeviceCloseAll()  

plt.plot(numpy.fromiter(rgdCapture, dtype = numpy.float))
plt.show()


