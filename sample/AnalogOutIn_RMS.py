"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-08-08

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

dwf.FDwfParamSet(DwfParamOnClose, 1) # 0 = run, 1 = stop, 2 = shutdown

print("Opening first device")
hdwf = c_int()
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 


hzSig = 60
fScan = False

print("Configure analog out channel")
dwf.FDwfAnalogOutEnableSet(hdwf, 0, 1) # enable first channel
dwf.FDwfAnalogOutFunctionSet(hdwf, 0, funcSine)
dwf.FDwfAnalogOutFrequencySet(hdwf, 0, c_double(hzSig))
dwf.FDwfAnalogOutAmplitudeSet(hdwf, 0, c_double(2.0 ** 0.5))
dwf.FDwfAnalogOutConfigure(hdwf, 0, 1)


print("Configure analog in")
cBuf = c_int(0)
dwf.FDwfAnalogInBufferSizeInfo(hdwf, None, byref(cBuf))
hzSys = c_double(0)
dwf.FDwfAnalogInFrequencyInfo(hdwf, None, byref(hzSys))
cDiv = round(0.5+hzSys.value/hzSig/cBuf.value)
hzCap = hzSys.value/cDiv
cSample = round(hzCap/hzSig)
print(f"Signal: {hzSig}Hz Buffer: {cBuf.value} System: {hzSys.value/1e6}MHz")
print(f"Capture: {round(hzCap/1000,3)}kHz Samples: {cSample} Length: {round(cSample/hzCap*1000,3)}ms / {round(hzCap/cSample,3)}Hz")
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(hzCap))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(cSample))

if fScan:
    dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeScanShift)
else:
    dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeSingle)

dwf.FDwfAnalogInChannelAttenuationSet(hdwf, 0, c_double(500))
dwf.FDwfAnalogInChannelRangeSet(hdwf, 0, c_double(2*360))
dwf.FDwfAnalogInChannelRangeSet(hdwf, 1, c_double(2*14))
dwf.FDwfAnalogInConfigure(hdwf, 1, 1)
rgdSamples = (c_double*cSample)()

if fScan:
    plt.axis([0, len(rgdSamples), -1000, 1000])
    plt.ion()
    hl, = plt.plot([], [])
    hl.set_xdata(range(0, len(rgdSamples)))

    print("Press Ctrl+C to stop")
    try:
        while True:
            sts = c_byte()
            cValid = c_int()
            dwf.FDwfAnalogInStatus(hdwf, 1, byref(sts))
            dwf.FDwfAnalogInStatusSamplesValid(hdwf, byref(cValid))
            if cValid.value < cSample:
                continue

            dwf.FDwfAnalogInStatusData(hdwf, c_int(0), byref(rgdSamples), cSample)
            rms1 = 0
            for i in range(cSample): rms1 += (rgdSamples[i]) ** 2
            rms1 = (rms1 / cSample) ** 0.5
            print(f"C1: {rms1}V")
            hl.set_ydata(rgdSamples)
            plt.draw()
            plt.pause(0.1)
    except KeyboardInterrupt:
        pass
        
else:
    while True:
        while True:
            sts = c_byte()
            dwf.FDwfAnalogInStatus(hdwf, 1, byref(sts))
            if sts.value == DwfStateDone.value :
                break
            time.sleep(0.1)
        print("Acquisition done")

        dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples, cSample)
        plt.plot(numpy.fromiter(rgdSamples, dtype = numpy.float))
        plt.show()
        rms1 = 0
        for i in range(cSample): rms1 += (rgdSamples[i]) ** 2
        rms1 = (rms1 / cSample) ** 0.5
        print(f"C1: {rms1}V")
        dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSamples, cSample)
        plt.plot(numpy.fromiter(rgdSamples, dtype = numpy.float))
        plt.show()
        rms2 = 0
        for i in range(cSample): rms2 += (rgdSamples[i]) ** 2
        rms2 = (rms2 / cSample) ** 0.5
        print(f"C2: {rms2}V")
        
        if 'y' != input("Next ? enter y: "):
            break

dwf.FDwfDeviceCloseAll()
