import numpy as np

def pulse_array_test(frequency, length, phase, amplitude, sampling_rate=2.0e9):
    num_samples = int(round(length * sampling_rate))    
    t = np.arange(num_samples) / sampling_rate
    return amplitude*np.exp(1j * (2 * np.pi * frequency * t + phase)) 