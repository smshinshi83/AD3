"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2025-03-26

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
from dwfconstants import *
import numpy as np
import math
import sys
import time

if sys.platform.startswith("win"):
    dwf = cdll.LoadLibrary("dwf.dll")
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")


# continue running after device close
dwf.FDwfParamSet(DwfParamOnClose, 0) # 4 = , 0 = run 1 = stop 2 = shutdown

hdwf = c_int()

print("Opening first device")
dwf.FDwfDeviceOpen(-1, byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()


# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 

# DIO pull-up AD3, ADP2230
dwf.FDwfDigitalIOPullSet(hdwf, 0xFFFF, 0)
dwf.FDwfDigitalIOConfigure(hdwf)


# V+ 3.3V
dwf.FDwfAnalogIOChannelNodeSet(hdwf, 0, 0, c_double(1))  # enable
dwf.FDwfAnalogIOChannelNodeSet(hdwf, 0, 1, c_double(3.3))  # 3.3V
dwf.FDwfAnalogIOEnableSet(hdwf, 1)
dwf.FDwfAnalogIOConfigure(hdwf)

# wait for V+ to settle
time.sleep(0.1)


print("Configuring I2C...")
iNak = c_int()
dwf.FDwfDigitalI2cReset()
dwf.FDwfDigitalI2cStretchSet(hdwf, 1) # clock stretching
dwf.FDwfDigitalI2cRateSet(hdwf, c_double(100e3)) # 100kHz
dwf.FDwfDigitalI2cSclSet(hdwf, 0) # SCL = DIO-0
dwf.FDwfDigitalI2cSdaSet(hdwf, 1) # SDA = DIO-1
dwf.FDwfDigitalI2cClear(hdwf, byref(iNak))
if iNak.value == 0:
    print("I2C bus error. Check the pull-ups.")
    quit()

adr = 0x1D;
#                                8bit address  
dwf.FDwfDigitalI2cWrite(hdwf, adr<<1, 0, 0, byref(iNak)) # write 0 bytes
if iNak.value != 0:
    print("Device test NAK "+str(iNak.value))
    quit()

rgPower = (c_ubyte*2)(0x2D, 0x08) # POWER_CTL | Measure
dwf.FDwfDigitalI2cWrite(hdwf, adr<<1, rgPower, 2, byref(iNak)) # write 2 bytes
if iNak.value != 0:
    print("Device power NAK "+str(iNak.value))
    quit()

rgFormat = (c_ubyte*2)(0x31, 0x08) # DATA_FORMAT | FULL_RES
dwf.FDwfDigitalI2cWrite(hdwf, adr<<1, rgFormat, 2, byref(iNak)) # write 2 bytes
if iNak.value != 0: 
    print("Device format NAK"+str(iNak.value))
    quit()

# first read
rgData = (c_ubyte*1)(0xF2)
rgAcc = (c_int16*3)()
dwf.FDwfDigitalI2cWriteRead(hdwf, adr<<1, rgData, 1, rgAcc, 6, byref(iNak)) # write 1 byte, restart, read 6 bytes
if iNak.value != 0:
    print("Device Data NAK "+str(iNak.value))
    #quit()

# convert data
x = rgAcc[0]/256 
y = rgAcc[1]/256 
z = rgAcc[2]/256 
g = math.sqrt(math.pow(x,2)+math.pow(y,2)+math.pow(z,2))
print(f"G: {g:.3f} \tX: {x:.3f} \tY: {y:.3f} \tZ: {z:.3f}")
    
# start spy
dwf.FDwfDigitalI2cSpyStart(hdwf)

# this will repeat last I2C transfer (first read) with the given period
dwf.FDwfDigitalOutWaitSet(hdwf, c_double(0.0))
dwf.FDwfDigitalOutRunSet(hdwf, c_double(0.5)) # 500ms = 2Hz
dwf.FDwfDigitalOutRepeatSet(hdwf, 0)
dwf.FDwfDigitalOutConfigure(hdwf, 1)


print("Press Ctrl+C to stop...")
try:
    while True:
        nData = 16
        fStart = c_int()
        fStop = c_int()
        rgData = (c_ubyte*nData)()
        cData = c_int()
        iNak = c_int()
        cData.value = nData
        
        if dwf.FDwfDigitalI2cSpyStatus(hdwf, byref(fStart), byref(fStop), byref(rgData), byref(cData), byref(iNak)) == 0:
            print("Communication with the device failed.")
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            print(str(szerr.value))
            break
        
        if fStart.value==1 and fStop.value==0 and cData.value==2 and rgData[0]==(adr<<1) and rgData[1]==0xF2 : # write command 
            continue
        elif fStart.value==2 and fStop.value==1 and cData.value==7 and rgData[0]==((adr<<1)|1): # read command
            x = np.int16((rgData[2]<<8)|rgData[1])/256 
            y = np.int16((rgData[4]<<8)|rgData[3])/256 
            z = np.int16((rgData[6]<<8)|rgData[5])/256 
            g = math.sqrt(math.pow(x,2)+math.pow(y,2)+math.pow(z,2))
            print(f"G: {g:.3f} \tX: {x:.3f} \tY: {y:.3f} \tZ: {z:.3f}")
        elif fStart.value!=0 or fStop.value!=0 or cData.value!=0 or iNak.value!=0: # other, unexpected
            msg = []
            if fStart.value == 1: 
                msg.append("Start")
            elif fStart.value == 2:
                msg.append("ReStart")
                
            for i in range(cData.value):
                # first data is address when fStart is not zero
                if i == 0 and fStart.value != 0:
                    msg.append(hex(rgData[i]>>1))
                    if rgData[i]&1:
                        msg.append("RD")
                    else:
                        msg.append("WR")
                else:
                    msg.append(hex(rgData[i]))
                    
            if fStop.value != 0: 
                msg.append("Stop")
            
            # NAK of data index + 1 or negative error
            if iNak.value > 0: 
                msg.append("NAK: "+str(iNak.value))
            elif iNak.value < 0:
                msg.append("Error: "+str(iNak.value))
            
            if len(msg):
                print(msg)
            break

except KeyboardInterrupt: # Ctrl+C
    pass

dwf.FDwfDigitalOutConfigure(hdwf, 0) # stop

dwf.FDwfDeviceCloseAll()
