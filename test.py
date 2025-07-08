from ctypes import *
from dwfconstants import *
import matplotlib.pyplot as plt
import numpy as np
import time
import sys

def open_device():
    if sys.platform.startswith("win"):
        dwf = cdll.dwf
    elif sys.platform.startswith("linux"):
        dwf = cdll.LoadLibrary("libdwf.so")

    hdwf = c_int()

    dwf.FDwfParamSet(DwfParamOnClose, c_int(0))
    #Open the first device
    dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

    if hdwf.value == hdwfNone.value:
        print("Failed to open device")
        quit()
    
    dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))
    
    return dwf, hdwf


def close_device(dwf, hdwf):
    dwf.FDwfDeviceClose(hdwf)
    print("Device closed")


def DigitalIO_Switch(dwf, hdwf, mask, value):
    dwf.FDwfDigitalIOOutputEnableSet(hdwf, c_int(mask))
    dwf.FDwfDigitalIOOutputSet(hdwf, c_int(value))
    dwf.FDwfDigitalIOConfigure(hdwf)


def AnalogIO_On(dwf, hdwf, isPositive=False, positive_v=0.0, isNegative=False, negative_v=0.0):
    if isPositive:    
        # enabel positive supply
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, 0, 0, c_double(1))
        # set the voltage
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, 0, 1, c_double(positive_v))
    else:
        # disabel positive supply
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, 0, 0, c_double(0))

    if isNegative:
        # enable negative supply
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, 1, 0, c_double(1))
        # set the voltage
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, 1, 1, c_double(negative_v))
    else:
        # disable negative supply
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, 1, 0, c_double(0))
    
    # master enable
    dwf.FDwfAnalogIOEnableSet(hdwf, c_int(1))


def AnalogIO_Off(dwf, hdwf):
    # disable all analog IO channels
    dwf.FDwfAnalogIOEnableSet(hdwf, c_int(0))


def AnalogOut_pulse(dwf, hdwf, channel, period, width, amplitude, offset=0.0, count=1, wait=0.0, isPlot=False):
    frequency = 1.0 / period
    duty = width / period


    dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_int(1))
    dwf.FDwfAnalogOutIdleSet(hdwf, c_int(channel), DwfAnalogOutIdleOffset)
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(channel), AnalogOutNodeCarrier, funcPulse)
    dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_double(frequency))
    dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_double(amplitude))
    dwf.FDwfAnalogOutNodeOffsetSet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_double(offset))

    dwf.FDwfAnalogOutRunSet(hdwf, c_int(channel), c_double(period))
    dwf.FDwfAnalogOutWaitSet(hdwf, c_int(channel), c_double(wait))
    dwf.FDwfAnalogOutRepeatSet(hdwf, c_int(channel), c_int(count))

    dwf.FDwfAnalogOutConfigure(hdwf, c_int(channel), c_int(1))


def AnalogOut_pulse_setting(dwf, hdwf, channel, period, width, amplitude, offset=0.0):
    frequency = 1.0 / period
    duty = width / period

    dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_int(1))
    dwf.FDwfAnalogOutIdleSet(hdwf, c_int(channel), DwfAnalogOutIdleOffset)
    dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(channel), AnalogOutNodeCarrier, funcPulse)
    dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_double(frequency))
    dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_double(amplitude))
    dwf.FDwfAnalogOutNodeOffsetSet(hdwf, c_int(channel), AnalogOutNodeCarrier, c_double(offset))
    dwf.FDwfAnalogOutRunSet(hdwf, c_int(channel), c_double(period))
    dwf.FDwfAnalogOutWaitSet(hdwf, c_int(channel), c_double(0.0))
    dwf.FDwfAnalogOutRepeatSet(hdwf, c_int(channel), c_int(1))
    
    dwf.FDwfAnalogOutConfigure(hdwf, c_int(channel), c_int(0))


if __name__ == "__main__":
    # open the devices
    dwf, hdwf = open_device()

    # set the wg1 offset to -2.0V
    dwf.FDwfAnalogOutNodeOffsetSet(hdwf, c_int(0), AnalogOutNodeCarrier, c_double(-2.0))

    # READ
    # set pin 1 to high
    DigitalIO_Switch(dwf, hdwf, mask=0x02, value=0x02)

    # SMUA applies the read voltage


    # set pin 1 to low
    DigitalIO_Switch(dwf, hdwf, mask=0x02, value=0x00)


    # SET
    # set AnalogIO to positive 5.0V
    AnalogIO_On(dwf, hdwf, isPositive=True, positive_v=5.0)

    # WG1 applies a pulse
    AnalogOut_pulse(dwf, hdwf, channel=0, period=1e-6, width=5e-7, amplitude=1.0, offset=-2.0, count=1)
    

    # RESET
    # set pin 0 to high
    DigitalIO_Switch(dwf, hdwf, mask=0x01, value=0x01)

    # Wg2 applies a pulse
    AnalogOut_pulse(dwf, hdwf, channel=1, period=1e-6, width=5e-7, amplitude=-0.50, offset=0, count=1)

    # set pin 0 to low
    DigitalIO_Switch(dwf, hdwf, mask=0x01, value=0x00)