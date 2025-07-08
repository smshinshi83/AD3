"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2024-10-14

   Requires:                       
       Python 2.7, 3
"""

from ctypes import *
import threading
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

hdwf = c_int()
sts = c_byte()

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == 0:
    print("failed to open device")
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    quit()

# the device will only be configured when FDwf###Configure is called
dwf.FDwfDeviceAutoConfigureSet(hdwf, 0) 

pinA = 0
pinB = 1
rgData = (c_uint32*1048576)()
fRun = True
cLost = 0
cWarn = 0
filt = 2 # glitch filter 20ns, 2/100MHz
x = 4 # 1, 2 or 4
count = 0
cps = 0
cfw = 0
crev = 0
hzRate = 100e6
lock = threading.Lock()

hzDI = c_double()
dwf.FDwfDigitalInInternalClockInfo(hdwf, byref(hzDI))
dwf.FDwfDigitalInDividerSet(hdwf, int(round(hzDI.value/hzRate)))
dwf.FDwfDigitalInSampleFormatSet(hdwf, 32)
dwf.FDwfDigitalInInputOrderSet(hdwf, 1) # DIO as least significant bits for Digital Discovery
dwf.FDwfDigitalInAcquisitionModeSet(hdwf, acqmodeRecord)
dwf.FDwfDigitalInSampleSensibleSet(hdwf, (1<<pinA)|(1<<pinB))

def receive():
    global fRun, count, cps, cfw, crev, cLost, cWarn
    s = 0
    fa2 = 0
    fb2 = 0
    if dwf.FDwfDigitalInConfigure(hdwf, 0, 1) == 0: fRun = False
    while fRun:
        sts = c_ubyte()
        if dwf.FDwfDigitalInStatus(hdwf, 1, byref(sts)) == 0: break
        ca = c_int()
        cl = c_int()
        cw = c_int()
        dwf.FDwfDigitalInStatusCompress(hdwf, byref(ca), byref(cl), byref(cw)) 
        if ca.value == 0: continue
        cb = min(ca.value, len(rgData));
        if ca.value > cb: cLost += ca.value - cb;
        if cl.value : cLost += cl.value;
        if cw.value : cWarn += cw.value;
        # data are pairs of value and count
        dwf.FDwfDigitalInStatusCompressed(hdwf, byref(rgData), 4*cb)
        
        lock.acquire()
        for i in range(0,cb,2) :
            v = rgData[i] # odd data is DIO value
            fa = (v >> pinA) & 1
            fb = (v >> pinB) & 1
            if s > filt :
                fw = 0
                if x == 1: 
                    if fa2 == 0 and fa != 0 : 
                        if fb != 0: fw = -1
                        else: fw = 1
                elif x == 2:
                    if fa2 != fa :
                        if fa == fb : fw = -1
                        else: fw = 1
                else : # 4X
                    if fa2 != fa :
                        if fa == fb : fw = -1
                        else: fw = 1
                    elif fb2 != fb :
                        if fa != fb : fw = -1
                        else: fw = 1
                if fw > 0 :
                    cps = s
                    count += 1
                    cfw += 1
                    s = 0
                elif fw < 0 :
                    cps = -s
                    count -= 1
                    crev += 1
                    s = 0
            fa2 = fa
            fb2 = fb
            # even data is stable count - 1
            s = s + 1 + rgData[i+1];
                
        lock.release()
        
    fRun = False

print("Press Ctrl+C to stop")

thread = threading.Thread(target=receive)
thread.start()

try:
    while True:
        time.sleep(1.0)
        
        if fRun != True :
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            print(str(szerr.value))
            quit()
            
        lock.acquire()
        if cps != 0:
            print(f"Count: {count} FW: {cfw} REV: {crev} RPM: {hzRate/cps*60/x} {hzRate/cps/x}Hz")
            cps = 0
        lock.release()

except KeyboardInterrupt:
    pass

fRun = False
thread.join()

dwf.FDwfDeviceCloseAll()


