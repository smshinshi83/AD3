"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-08-05

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import math
import sys
import time
import numpy
from dwfconstants import *


if sys.platform.startswith("win"):
    dwf = cdll.LoadLibrary("dwf.dll")
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")



version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, 0) # 0 = run, 1 = stop, 2 = shutdown

hdwf = c_int()

print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))


if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) # 0 = the device will only be configured when FDwf###Configure is called


rgbTX = (c_ubyte*4)(0,1,2,3)
rgbRX = (c_ubyte*4)()
iNak = c_int()


dwf.FDwfDigitalSpiFrequencySet(hdwf, c_double(500)) 
dwf.FDwfDigitalSpiClockSet(hdwf, 1)
dwf.FDwfDigitalSpiDataSet(hdwf, 0, 2) # 0 DQ0_MOSI_SISO = DIO-2
dwf.FDwfDigitalSpiDataSet(hdwf, 1, 3) # 1 DQ1_MISO = DIO-3
dwf.FDwfDigitalSpiIdleSet(hdwf, 0, 3) # 0 DQ0_MOSI_SISO = DwfDigitalOutIdleZet
dwf.FDwfDigitalSpiIdleSet(hdwf, 1, 3) # 1 DQ1_MISO = DwfDigitalOutIdleZet
dwf.FDwfDigitalSpiModeSet(hdwf, 0)
dwf.FDwfDigitalSpiOrderSet(hdwf, 1) # 1 MSB first
dwf.FDwfDigitalSpiSelectSet(hdwf, 0, 1) # CS: DIO-0, idle high

dwf.FDwfDigitalI2cRateSet(hdwf, c_double(500))
dwf.FDwfDigitalI2cSclSet(hdwf, 4) # SCL = DIO-4
dwf.FDwfDigitalI2cSdaSet(hdwf, 5) # SDA = DIO-5


# release CS and CLK, if it is driven by earlier configuration
dwf.FDwfDigitalIOReset(hdwf)
dwf.FDwfDigitalIOConfigure(hdwf)


# SPI
dwf.FDwfDigitalSpiWriteOne(hdwf, 1, 0, 0) # start driving clock and data
# SPI transfer(s)
dwf.FDwfDigitalSpiWriteRead(hdwf, 1, 8, rgbTX, len(rgbTX), rgbRX, len(rgbRX)) 
print("SPI:",list(rgbRX))
# hold CS high and CLK low during I2C
dwf.FDwfDigitalIOOutputEnableSet(hdwf, 3)
dwf.FDwfDigitalIOOutputSet(hdwf, 1)
dwf.FDwfDigitalIOConfigure(hdwf)


# I2C
dwf.FDwfDigitalOutReset(hdwf)
dwf.FDwfDigitalI2cClear(hdwf, byref(iNak)) # check if SCL and SDA are high, try to release SDA
if iNak.value == 0: 
    print("I2C bus error. Check the pull-ups.")
    quit()
else:
    # I2C transfer(s)
    dwf.FDwfDigitalI2cRead(hdwf, 0x1D<<1, rgbRX, len(rgbRX), byref(iNak))
    if iNak.value != 0:
        print("NAK "+str(iNak.value))
    print("I2C:",list(rgbRX))


# SPI
dwf.FDwfDigitalOutReset(hdwf)
dwf.FDwfDigitalSpiWriteOne(hdwf, 1, 0, 0) # start driving clock and data
# release CS and CLK
dwf.FDwfDigitalIOReset(hdwf)
dwf.FDwfDigitalIOConfigure(hdwf)
# SPI transfer(s)
dwf.FDwfDigitalSpiWriteRead(hdwf, 1, 8, rgbTX, len(rgbTX), rgbRX, len(rgbRX)) 
print("SPI:",list(rgbRX))

# hold CS high and CLK low during I2C
dwf.FDwfDigitalIOOutputEnableSet(hdwf, 3)
dwf.FDwfDigitalIOOutputSet(hdwf, 1)
dwf.FDwfDigitalIOConfigure(hdwf)


# I2C
dwf.FDwfDigitalOutReset(hdwf)
dwf.FDwfDigitalI2cRead(hdwf, 0x1D<<1, rgbRX, len(rgbRX), byref(iNak))
if iNak.value != 0:
    print("NAK "+str(iNak.value))
print("I2C:",list(rgbRX))


dwf.FDwfDeviceCloseAll()
