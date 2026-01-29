#%%
from sources.calibration_helpers import calibrate_devices
from laboneq.simple import *
import sources.utils as utils
import numpy as np
from datetime import datetime
from pathlib import Path

now = datetime.now()
time_str = now.strftime("%y%m%d")
folder_dir = Path(f"figures/test_76GHz_delay80_{time_str}")
folder_dir.mkdir(parents=True, exist_ok=True)


test_pulse = pulse_library.const(length= 100e-9, amplitude= 0.5)

device = calibrate_devices(measure_type = "spec_square")

time_sweeper = LinearSweepParameter(uid="delay_sweep", 
                                        start=-400e-9, 
                                        stop=100e-9, 
                                        count=100, 
                                        axis_name="Time (s)")
phase_sweeper = LinearSweepParameter(uid = "phase_sweeper", start = 0
                                     ,stop = np.pi*2,
                                     count = 9, 
                                     axis_name = "phase (rad)")
test_exp = Experiment(
    uid = "test_exp",
    signals = [ExperimentSignal("measure_signal"),
              ExperimentSignal("acquire_signal")]
    )

# with test_exp.sweep(uid = "time_sweep", parameter=time_sweeper):
with test_exp.sweep(uid = "phase_sweep", parameter = phase_sweeper):
    with test_exp.acquire_loop_rt(
        uid = "test_exp_acquire_section",
        averaging_mode=AveragingMode.CYCLIC,
        count = 1000,
        acquisition_type = AcquisitionType.RAW
    ):
        with test_exp.section(uid="measure_section",on_system_grid=True, alignment=SectionAlignment.LEFT):
            test_exp.play(signal = "measure_signal", pulse = test_pulse, phase = phase_sweeper)
            # test_exp.signals["measure_signal"]=ExperimentSignal("measure_signal")
            test_exp.acquire(signal="acquire_signal", handle = "acquire_handle", kernel = test_pulse, length = 300e-9)
            # test_exp.signals["acquire_signal"]=ExperimentSignal("acquire_signal")
            test_exp.delay(time=70e-6, signal = "measure_signal")
            test_exp.delay(time=70e-6, signal = "acquire_signal")

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
real = {}
imag = {}
#%%
for i, phase in enumerate(phase_sweeper.values):
    plt.figure(figsize=(10, 6))

    # 1. Real Part (실수부)
    plt.plot(axis[1]/2, np.real(data[i]), label="Real (I)", alpha=0.7)

    # 2. Imaginary Part (허수부)
    plt.plot(axis[1]/2, np.imag(data[i]), label="Imag (Q)", alpha=0.7)

    # 3. Absolute Value (크기/절댓값) - 보통 강조하기 위해 조금 더 굵거나 진하게 그립니다
    plt.plot(axis[1]/2, np.abs(data[i]), 'k--', linewidth=2, label="Abs (Magnitude)")

    plt.title(rf"play phase = {phase/np.pi:.2f}$\pi$")
    plt.axvline(x= axis[1][21]/2, color='gray', linestyle='--', linewidth=1, label=f'x = {axis[1][21]/2}')
    plt.axvline(x= axis[1][201]/2, color='gray', linestyle='--', linewidth=1, label=f'x = {axis[1][201]/2}')
    plt.xlabel("ns")
    plt.ylabel("Amplitude")
    plt.legend(loc='best') # 범례 표시

    plt.savefig(folder_dir / rf"raw_test_{round(phase/np.pi*100)}pi.png")
    plt.show
    real[phase] = np.mean(np.real(data[i][21:202]))
    imag[phase] = np.mean(np.imag(data[i][21:202]))
# %%
plt.figure()
for phase in real.keys():
    plt.scatter(real[phase],imag[phase],label = rf"{phase/np.pi:.2f}$\pi$")
plt.legend()
plt.xlabel("real part")
plt.ylabel("imga part")
plt.axis('equal')
plt.savefig(folder_dir / "play phase, IQ blob")
# %%
