# dwfconstants.py

# AnalogOut Function
DwfAnalogOutFunctionSine        = 0
DwfAnalogOutFunctionSquare      = 1
DwfAnalogOutFunctionTriangle    = 2
DwfAnalogOutFunctionRampUp      = 3
DwfAnalogOutFunctionRampDown    = 4
DwfAnalogOutFunctionDC          = 5
DwfAnalogOutFunctionNoise       = 6
DwfAnalogOutFunctionPulse       = 7
DwfAnalogOutFunctionTrapezium   = 8
DwfAnalogOutFunctionSinePower   = 9
DwfAnalogOutFunctionCustom      = 30

# TriggerSource
DwfTriggerSourceNone     = 0
DwfTriggerSourcePC       = 1
DwfTriggerSourceDetectorAnalogIn  = 2
DwfTriggerSourceDetectorDigitalIn = 3
DwfTriggerSourceAnalogIn  = 4
DwfTriggerSourceDigitalIn = 5
DwfTriggerSourceDigitalOut = 6
DwfTriggerSourceAnalogOut  = 7
DwfTriggerSourceLink       = 8
DwfTriggerSourceExternal1  = 9
DwfTriggerSourceExternal2  = 10
DwfTriggerSourceExternal3  = 11
DwfTriggerSourceExternal4  = 12

# DwfState
DwfStateReady      = 0
DwfStateConfig     = 4
DwfStatePrefill    = 5
DwfStateArmed      = 1
DwfStateWait       = 7
DwfStateTriggered  = 3
DwfStateRunning    = 3
DwfStateDone       = 2
