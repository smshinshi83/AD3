"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-09-19

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import time
from dwfconstants import *
import sys
import matplotlib.pyplot as plt
import numpy

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

print("Opening first available device")
hdwf = c_int()
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(szerr.value)
    quit()

# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 

sRun = 0.01
hzRate = 100e6
hzSig = 8e3
nSamples = int(hzRate * sRun)
rgPlay = numpy.sin(2 * numpy.pi * hzSig * numpy.linspace(0, sRun, nSamples, endpoint=False))
rgdPlay = (c_double * nSamples)(*rgPlay)
iWavegen = 0
iScope = 0

print(f"Run: {sRun}s Rate: {hzRate}Hz Samples: {nSamples} Signal: {hzSig}Hz")


nDeviceScopeBuffer = c_int(0)
dwf.FDwfAnalogInBufferSizeInfo(hdwf, 0, byref(nDeviceScopeBuffer))
if nDeviceScopeBuffer.value < nSamples:
    dwf.FDwfDeviceCloseAll()
    print(f"Device/configuration Scope buffer size is {nDeviceScopeBuffer.value}")
    quit()
    
nDevicePlayBuffer = c_int(0)
dwf.FDwfAnalogOutNodePlayInfo(hdwf, iWavegen, AnalogOutNodeCarrier, 0, byref(nDevicePlayBuffer))
if nDevicePlayBuffer == 0:
    dwf.FDwfDeviceCloseAll()
    print("Device/configuration does not not provide deep play buffer")
    quit()
if nDevicePlayBuffer.value < nSamples:
    dwf.FDwfDeviceCloseAll()
    print(f"Device/configuration Wavegen Play buffer size is {nDevicePlayBuffer.value}")
    quit()
    
    

dwf.FDwfAnalogInChannelEnableSet(hdwf, iScope, 1)
dwf.FDwfAnalogInChannelRangeSet(hdwf, iScope, c_double(2.0))
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(hzRate))
dwf.FDwfAnalogInBufferSizeSet(hdwf, nSamples)
dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(sRun/2)) # T0 on left, relative to middle
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcAnalogOut1)
dwf.FDwfAnalogInConfigure(hdwf, 1, 1)

dwf.FDwfAnalogOutEnableSet(hdwf, iWavegen, 1) 
dwf.FDwfAnalogOutFunctionSet(hdwf, iWavegen, funcPlay)
dwf.FDwfAnalogOutFrequencySet(hdwf, iWavegen, c_double(hzRate))
dwf.FDwfAnalogOutRepeatSet(hdwf, iWavegen, 1)
dwf.FDwfAnalogOutRunSet(hdwf, iWavegen, c_double(sRun))
dwf.FDwfAnalogOutDataSet(hdwf, iWavegen, rgdPlay, nSamples)
dwf.FDwfAnalogOutConfigure(hdwf, iWavegen, 1)


sts = c_int()
while True:
    dwf.FDwfAnalogInStatus(hdwf, 1, byref(sts))
    if sts.value == DwfStateDone.value :
        break

rgdCap = (c_double*nSamples)()
dwf.FDwfAnalogInStatusData(hdwf, iScope, rgdCap, len(rgdCap))

dwf.FDwfDeviceCloseAll()

plt.plot(numpy.fromiter(rgdPlay, dtype = numpy.float))
plt.plot(numpy.fromiter(rgdCap, dtype = numpy.float))
plt.show()

