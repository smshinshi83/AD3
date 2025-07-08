from ctypes import *
from dwfconstants import *
import matplotlib.pyplot as plt
import numpy as np
import time

#SDK読み込み
dwf = cdll.LoadLibrary("dwf")

#デバイスオープン
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))
if hdwf.value == 0:
    print("デバイスが見つかりません")
    quit()

#パルス設定
pulse_width = 5e-7
period = pulse_width * 5
frequency = 1 / period
duty = (pulse_width / period) * 100
amplitude = 0.5
repeat = 0

dwf.FDwfAnalogOutReset(hdwf, 0)
dwf.FDwfAnalogOutEnableSet(hdwf, 0, 1)
dwf.FDwfAnalogOutFunctionSet(hdwf, 0, DwfAnalogOutFunctionPulse)
dwf.FDwfAnalogOutFrequencySet(hdwf, 0, c_double(frequency))
dwf.FDwfAnalogOutAmplitudeSet(hdwf, 0, c_double(amplitude))
dwf.FDwfAnalogOutOffsetSet(hdwf, 0, c_double(0))
dwf.FDwfAnalogOutSymmetrySet(hdwf, 0, c_double(duty))
dwf.FDwfAnalogOutIdleSet(hdwf, 0, "DwfAnalogOutIdleOffset")

dwf.FDwfAnalogOutRepeatSet(hdwf, 0, c_int(repeat))
dwf.FDwfAnalogOutRepeatTriggerSet(hdwf, 0, c_int(repeat))
dwf.FDwfAnalogOutRunSet(hdwf, 0, c_double(period))
#dwf.FDwfAnalogOutWaitSet(hdwf, 0, c_double(0))

#オシロスコープ
hzAcq = c_double(100e6)  # 100MS/s
nSamples = 1000

dwf.FDwfAnalogInReset(hdwf)

dwf.FDwfAnalogInFrequencySet(hdwf, hzAcq)
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(nSamples))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))  # CH1
dwf.FDwfAnalogInChannelRangeSet(hdwf, 0, c_double(0.2))

# トリガ設定
dwf.FDwfAnalogOutTriggerSourceSet(hdwf, 0, DwfTriggerSourceNone)
dwf.FDwfAnalogInTriggerSourceSet(hdwf, DwfTriggerSourceAnalogOut)

# 開始
dwf.FDwfAnalogInConfigure(hdwf, c_bool(False), c_bool(True))
dwf.FDwfAnalogOutConfigure(hdwf, 0, 1)

# 測定完了まで待機
sts = c_byte()
while True:
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    if sts.value == DwfStateDone:
        break
    time.sleep(0.01)

# データ取得
rgBuffer = (c_double * nSamples)()
dwf.FDwfAnalogInStatusData(hdwf, c_int(0), rgBuffer, len(rgBuffer))

# 時間軸生成と表示
t = np.linspace(0, nSamples / hzAcq.value, nSamples)
v = np.fromiter(rgBuffer, dtype=np.float64)

plt.plot(t * 1e6, v)  # μs単位で表示
plt.xlabel("Time [μs]")
plt.ylabel("Voltage [V]")
plt.title("Pulse Output + Oscilloscope Capture")
plt.grid()
plt.savefig(f"{pulse_width}s.png")

# 終了処理
dwf.FDwfDeviceCloseAll()

data = np.column_stack((t,v))
np.savetxt(f"{pulse_width}_data.csv", data, delimiter=",", header="Time[s],Voltage[V]",comments="")