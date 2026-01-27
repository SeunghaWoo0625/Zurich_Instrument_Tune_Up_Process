#%%
from sources.calibration_helpers import calibrate_devices
from laboneq.simple import *
import utils
import numpy as np
from datetime import datetime
test_pulse = pulse_library.const(length= 100e-9, amplitude= 0.5)

device = calibrate_devices(measure_type = "spec_square")

test_exp = Experiment(
    uid = "test_exp",
    signals = [ExperimentSignal("measure_signal"),
              ExperimentSignal("acquire_signal")]
    )

time_sweeper = LinearSweepParameter(uid="delay_sweep", 
                                        start=0, 
                                        stop=100e-9, 
                                        count=100, 
                                        axis_name="Time (s)")

with test_exp.sweep(uid = "time_sweep", parameter=time_sweeper):
    with test_exp.acquire_loop_rt(
        uid = "test_exp_acquire_section",
        count = 1000,
        acquisition_type = AcquisitionType.RAW
    ):
        with test_exp.section(uid="measure_section",on_system_grid=True, alignment=SectionAlignment.RIGHT):
            test_exp.play(signal = "measure_signal", pulse = test_pulse, phase = np.pi/4)
            # test_exp.signals["measure_signal"]=ExperimentSignal("measure_signal")
            test_exp.acquire(signal="acquire_signal", handle = "acquire_handle", kernel = test_pulse, )
            # test_exp.signals["acquire_signal"]=ExperimentSignal("acquire_signal")
            test_exp.delay(time=70e-6, signal = "measure_signal")
            test_exp.delay(time=70e-6, signal = "acquire_signal")
exp_calibration = Calibration()
exp_calibration["acquire_signal"] = SignalCalibration(
    port_delay = time_sweeper)
test_exp.set_calibration(exp_calibration)


#%%
qubit_parameters = utils.get_qubit_params()

session = Session(device_setup=device)
session.connect()

lsg = device.logical_signal_groups["d1"]
test_exp.map_signal("measure_signal", device.logical_signal_groups["d1"].logical_signals["measure_line"])
test_exp.map_signal("acquire_signal", device.logical_signal_groups["d1"].logical_signals["acquire_line"])

compiled_exp = session.compile(test_exp)
now = datetime.now()
time_str = now.strftime("%y%m%d_%H%M%S")
show_pulse_sheet(f"pulse_sheets/acquire_raw_test_{time_str}", compiled_exp)
results = session.run(compiled_exp, include_results_metadata=True)

# %%
data = results.get_data(handle = "acquire_handle")
axis = results.get_axis(handle="acquire_handle")
import matplotlib.pyplot as plt
import numpy as np
#%%
plt.figure()
plt.plot(axis[1],data[1])

#%%

plt.figure(figsize=(10, 6))

# 1. Real Part (실수부)
plt.plot(axis[0], np.real(data), label="Real (I)", alpha=0.7)

# 2. Imaginary Part (허수부)
plt.plot(axis[0], np.imag(data), label="Imag (Q)", alpha=0.7)

# 3. Absolute Value (크기/절댓값) - 보통 강조하기 위해 조금 더 굵거나 진하게 그립니다
plt.plot(axis[0], np.abs(data), 'k--', linewidth=2, label="Abs (Magnitude)")

plt.title(f"Signal Components: Real, Imag, and Abs")
plt.xlabel("Time / Frequency (axis unit)") # 축 단위에 맞게 수정하세요 (예: Time [s])
plt.ylabel("Amplitude [a.u.]")
plt.legend(loc='best') # 범례 표시
plt.grid(True, linestyle=':', alpha=0.6)
plt.show()
# %%
