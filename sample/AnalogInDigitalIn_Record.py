"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-12-18

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import math
import time
import matplotlib.pyplot as plt
import sys
import numpy

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_byte()
hzAcq = 50e6
test = int(1e6)
nBuffer = 1<<26
bAnalog = (c_double*nBuffer)()
bDigital = (c_uint16*nBuffer)()
iAnalog = 0
iDigital = 0
xAnalog = 0
xDigital = 0

fLost = 0
fCorrupted = 0

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

print("Open first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == hdwfNone.value:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    print("failed to open device")
    quit()

dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) # 0 = the device will only be configured when FDwf###Configure is called

print("Press Ctrl+C to stop")


dwf.FDwfAnalogOutNodeEnableSet(hdwf, 0, AnalogOutNodeCarrier, 1)
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, 0, AnalogOutNodeCarrier, funcSquare)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, 0, AnalogOutNodeCarrier, c_double(100))
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, 0, AnalogOutNodeCarrier, c_double(1.4))
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, 0, AnalogOutNodeCarrier, c_double(1.4))
dwf.FDwfAnalogOutConfigure(hdwf, 0, 1)

hzDI = c_double()
dwf.FDwfDigitalInInternalClockInfo(hdwf, byref(hzDI))
dwf.FDwfDigitalInAcquisitionModeSet(hdwf, acqmodeRecord)
dwf.FDwfDigitalInDividerSet(hdwf, int(round(hzDI.value/hzAcq)))
dwf.FDwfDigitalInTriggerSourceSet(hdwf, trigsrcAnalogIn)
dwf.FDwfDigitalInSampleFormatSet(hdwf, 16)
#dwf.FDwfDigitalInSampleSensibleSet(hdwf, 0x0001) # compress data, interested only in DIO-0 transitions
dwf.FDwfDigitalInTriggerPositionSet(hdwf, 0) # continuous
dwf.FDwfDigitalInConfigure(hdwf, 1, 0)

dwf.FDwfAnalogInChannelEnableSet(hdwf, 0, 1)
dwf.FDwfAnalogInChannelRangeSet(hdwf, 0, c_double(5))
dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeRecord)
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(hzAcq))
dwf.FDwfAnalogInRecordLengthSet(hdwf, c_double(0)) # continuous
dwf.FDwfAnalogInBufferSizeSet(hdwf, int(nBuffer/2)) 
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn) #one of the analog in channels
dwf.FDwfAnalogInTriggerTypeSet(hdwf, trigtypeEdge)
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0)) # first channel
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(1.5)) 
dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeRise) 
dwf.FDwfAnalogInConfigure(hdwf, 1, 0)


# wait for offsets and relays to settle
time.sleep(0.1) 
dwf.FDwfDigitalInConfigure(hdwf, 0, 1)
dwf.FDwfAnalogInConfigure(hdwf, 0, 1)


try:
    while True:
        cAvailable = c_int()
        cLost = c_int()
        cWarn = c_int()

        if dwf.FDwfAnalogInStatus(hdwf, 1, byref(sts)) != 1:
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            print(str(szerr.value))
            quit()
            
        dwf.FDwfAnalogInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cWarn))
        
        if cLost.value :
            print("Analog samples were lost! Reduce frequency.")
            break
        if cWarn.value :
            print("Analog samples may be lost! Reduce frequency.")
            break
            
        if cAvailable.value != 0 :
            if cAvailable.value > nBuffer :
                print(f"Too much analog data({cAvailable.value}). Increase buffer size.")
                break
                
            cSample1 = cAvailable.value
            cSample2 = 0
            if iAnalog + cSample1 > nBuffer:
                cSample2 = iAnalog + cSample1 - nBuffer
                cSample1 -= cSample2
            
            dwf.FDwfAnalogInStatusData(hdwf, 0, byref(bAnalog, 8*iAnalog), cSample1) # up to the end of buffer
            if cSample2 != 0:
                dwf.FDwfAnalogInStatusData2(hdwf, 0, byref(bAnalog), cSample1, cSample2) # from start of the buffer
            
            iAnalog += cSample1 + cSample2
            if iAnalog >= nBuffer: xAnalog += 1
            iAnalog %= nBuffer


        if dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts)) != 1:
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            print(str(szerr.value))
            quit()
            
        dwf.FDwfDigitalInStatusRecord(hdwf, byref(cAvailable), byref(cLost), byref(cWarn))
        
        if cLost.value :
            print("Digital samples were lost! Reduce frequency.")
            break
        if cWarn.value :
            print("Digital samples may be lost! Reduce frequency.")
            break
            
        if cAvailable.value != 0 :
            if cAvailable.value > nBuffer :
                print(f"Too much digital data ({cAvailable.value}). Increase buffer size.")
                break
                
            cSample1 = cAvailable.value
            cSample2 = 0
            if iDigital + cSample1 > nBuffer:
                cSample2 = iDigital + cSample1 - nBuffer
                cSample1 -= cSample2
            
            dwf.FDwfDigitalInStatusData(hdwf, byref(bDigital, 2*iDigital), int(2*cSample1)) # up to the end of buffer
            if cSample2 != 0:
                dwf.FDwfDigitalInStatusData2(hdwf, byref(bDigital), cSample1, int(2*cSample2)) # from start of the buffer
                
            iDigital += cSample1 + cSample2
            if iDigital >= nBuffer: xDigital += 1
            iDigital %= nBuffer
            
        if test != 0 and xAnalog == 0 and iAnalog > test and iDigital > test:
            break

except KeyboardInterrupt:
    pass

dwf.FDwfDigitalInConfigure(hdwf, 1, 0)
dwf.FDwfAnalogInConfigure(hdwf, 1, 0)
dwf.FDwfDeviceCloseAll()

print(f"done analog:{xAnalog} + {iAnalog} digital:{xDigital} + {iDigital}")

if test !=0 :
    d = 0
    for i in range(iDigital):
        if (bDigital[i] & 1) == 0:
            d = i
            break
    for i in range(d, iDigital):
        if (bDigital[i] & 1) != 0:
            d = i
            break
    a = 0
    for i in range(iAnalog):
        if bAnalog[i] < 1.3:
            a = i
            break
    for i in range(a, iAnalog):
        if bAnalog[i] > 1.4:
            a = i
            break
    print(f"digital to analog delay {a-d}")
            
    plt.plot(numpy.fromiter(bAnalog, count=test, dtype = numpy.float))
    plt.plot(numpy.fromiter(bDigital, count=test, dtype = numpy.float)) # each sample DIO 15:0 value 0-255, mask with &1 for DIO-0
    plt.show()
