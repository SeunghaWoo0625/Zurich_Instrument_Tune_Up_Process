from pulses.pulse_test import test_custom_pulse_function
from laboneq.dsl.experiment.pulse_library import pulse_factory
from laboneq.dsl.experiment.pulse_library import sampled_pulse
import numpy as np
from laboneq.dsl.experiment import pulse_library
from pulses.array import pulse_array_test

pulse1 = test_custom_pulse_function(uid="test", length = 10e-9, amplitude = 0.5)
pulse2_array = pulse_array_test(frequency=100e6, length=50e-9, phase=0, amplitude=.5)
pulse2 = sampled_pulse(samples=pulse2_array, uid="array_pulse")

# print(pulse([1,2,3,4,5]))
print(pulse1)
print(pulse2)