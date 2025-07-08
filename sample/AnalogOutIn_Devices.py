"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-08-06

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import time
from dwfconstants import *
import sys
import numpy
import matplotlib.pyplot as plt

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
channel = c_int(0)

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

# prevent temperature drift
dwf.FDwfParamSet(DwfParamOnClose, c_int(1)) # 0 = run, 1 = stop, 2 = shutdown
dwf.FDwfParamSet(DwfParamExtFreq, 10000000) # reference clock frequency
dwf.FDwfParamSet(DwfParamFrequency, 100000000) # system clock frequency

cDevice = c_int()
dwf.FDwfEnum(0, byref(cDevice))
print(f"Found {cDevice.value} devices")
print("Connect trigger lines between devices for reference clock and triggering\nTwist each wire with ground for shielding")

hzRate = 10e9 # analog-in sample rate
cSamples = 16*1024 # samples, with AD3: up to 16ki/channel or 32ki/ch with 2nd configuration
sPos = 280e-9 # trigger position, also compensate for analog-out delay
rgdSamples = (c_double*cSamples)()

cSteps = 4 # analog-out steps
hzFreq = 1000 # 
rghdwf = []

for iDevice in range(cDevice.value):
    hdwf = c_int(0)
    dwf.FDwfDeviceOpen(iDevice, byref(hdwf))
    if hdwf.value == 0:
        continue
    
    dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) # the instruments will only be configured when FDwf###Configure is called
    rghdwf.append(hdwf.value)
    
    if len(rghdwf) == 1: # let use first device as master
        dwf.FDwfDeviceTriggerSet(hdwf, 1, trigsrcPC) # Trigger 2 outputs TriggerPC
        dwf.FDwfDeviceParamSet(hdwf, DwfParamClockMode, 1) # reference clock output on Trigger 1
        dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(sPos))
        cPhaseSteps = c_int()
        dwf.FDwfDeviceParamGet(hdwf, DwfParamFreqPhaseSteps, byref(cPhaseSteps)) # phase for slave device, if needed
        print(f"Phase steps:{cPhaseSteps.value} increment: {360000/cPhaseSteps.value}")
    else:
        dwf.FDwfDeviceParamSet(hdwf, DwfParamFreqPhase, 300*1000) # mDeg, phase for slave device, if needed
        dwf.FDwfDeviceParamSet(hdwf, DwfParamClockMode, 2) # reference clock input on Trigger 1
        dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(sPos - 10e-9)) # compensate trigger delay to slave, 10ns @ 100MHz
    
    cChannel = c_int()
    dwf.FDwfAnalogOutCount(hdwf, byref(cChannel))
    
    dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcExternal2)
    dwf.FDwfAnalogInFrequencySet(hdwf, c_double(hzRate))
    dwf.FDwfAnalogInBufferSizeSet(hdwf, cSamples) 
    dwf.FDwfAnalogInChannelEnableSet(hdwf, -1, 1)
    dwf.FDwfAnalogInChannelRangeSet(hdwf, -1, c_double(2.0))
    dwf.FDwfAnalogInConfigure(hdwf, 1, 1)
    
    # in AD3 the power supplies can be be used as slow AWG channels 3-4, but we don't need these now
    if cChannel.value > 2: cChannel.value = 2
    
    for iChannel in range(cChannel.value):
        print(f"Configure Device {iDevice +1} W{iChannel+1}")
        dwf.FDwfAnalogOutIdleSet(hdwf, iChannel, DwfAnalogOutIdleOffset)
        dwf.FDwfAnalogOutTriggerSourceSet(hdwf, iChannel, trigsrcExternal2)
        dwf.FDwfAnalogOutRepeatTriggerSet(hdwf, iChannel, 1) # repeat trigger
        dwf.FDwfAnalogOutRunSet(hdwf, iChannel, c_double(1.0/hzFreq)) # run length
        dwf.FDwfAnalogOutRepeatSet(hdwf, iChannel, 0) # run infinite
        
        # synchronize analog-out of devices, master +10ns, min 30ns @ 100MHz
        if len(rghdwf) == 1 :
            dwf.FDwfAnalogOutWaitSet(hdwf, iChannel, c_double(40e-9))
        else:
            dwf.FDwfAnalogOutWaitSet(hdwf, iChannel, c_double(30e-9))
        
        dwf.FDwfAnalogOutNodeEnableSet(hdwf, iChannel, AnalogOutNodeCarrier, c_int(1))
        dwf.FDwfAnalogOutNodeFunctionSet(hdwf, iChannel, AnalogOutNodeCarrier, funcPulse)
        dwf.FDwfAnalogOutNodeFrequencySet(hdwf, iChannel, AnalogOutNodeCarrier, c_double(hzFreq))
        dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, iChannel, AnalogOutNodeCarrier, c_double(1.0))
        
        dwf.FDwfAnalogOutConfigure(hdwf, iChannel, 1)

time.sleep(0.1)

# adjust amplitude channel 0 (1st) of the first device
for i in range(cSteps) :
    time.sleep(0.01) # approximately 10ms software wait
    dwf.FDwfAnalogOutNodeAmplitudeSet(rghdwf[0], 0, AnalogOutNodeCarrier, c_double(1.0-2.0*i/(cSteps-1)))
    dwf.FDwfAnalogOutConfigure(rghdwf[0], 0, 3)
    dwf.FDwfDeviceTriggerPC(rghdwf[0])
    
    for iDevice in range(cDevice.value):
        while True:
            sts = c_byte(0)
            dwf.FDwfAnalogInStatus(rghdwf[iDevice], 1, byref(sts))
            if sts.value == DwfStateDone.value :
                break
        cChannel = c_int(0)
        dwf.FDwfAnalogInChannelCount(rghdwf[iDevice], byref(cChannel))
        for iChannel in range(cChannel.value): 
            dwf.FDwfAnalogInStatusData(rghdwf[iDevice], iChannel, rgdSamples, cSamples)
            plt.plot(numpy.fromiter(rgdSamples, dtype = numpy.float), label=f'D{iDevice+1}C{iChannel+1}')
        
    plt.show()

dwf.FDwfDeviceCloseAll()
