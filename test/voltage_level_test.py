#%%
from sources.calibration_helpers import calibrate_devices
from laboneq.simple import *
import sources.utils as utils
import numpy as np

qubit_parameters = utils.get_qubit_params()
qubit_parameters["shfqc_0"]["qa_channel"]["local_oscillator_frequency"] = 2e9
qubit_parameters["shfqc_0"]["sg_channel"]["local_oscillator_frequency"][0] = 2e9
qubit_parameters["shfqc_0"]["qa_channel"]["range_out_spectroscopy"] = 0
qubit_parameters["shfqc_0"]["sg_channel"]["range_out"][1] = 0
qubit_parameters["shfqc_0"]["qa_channel"]["range_in_spectroscopy"] = 10

device = calibrate_devices(qubit_params=qubit_parameters)
session = Session(device_setup = device)
session.connect(do_emulation = False)

exp_test = Experiment(uid = "test", 
                      signals = [ExperimentSignal("drive"),
                                 ExperimentSignal("measure"),
                                 ExperimentSignal("acquire")])

drive_test_pulse = pulse_library.const(length = 40e-9, amplitude=1.0)
measure_test_pulse = pulse_library.const(length = 1000e-9, amplitude=0.9)
acquire_test_pulse = pulse_library.const(length = 1000e-9, amplitude=0.9)

# dummy_sweeper = LinearSweepParameter(uid = "dummy_sweeper", 
#                                      start = 0, 
#                                      stop = 0, 
#                                      count = 1000,
#                                      axis_name = "dummy count")
# with exp_test.sweep(uid = "dummy_sweep", parameter = dummy_sweeper):
with exp_test.acquire_loop_rt(uid = "acquire_loop",
                                averaging_mode=AveragingMode.CYCLIC,
                                count = 100,
                            acquisition_type = AcquisitionType.RAW):
    with exp_test.section(uid = "measure and play", on_system_grid=True, alignment=SectionAlignment.LEFT):
        exp_test.play(signal = "measure", pulse = measure_test_pulse)
        exp_test.acquire(signal = "acquire", kernel = acquire_test_pulse, handle = "acquire")
        exp_test.play(signal = "drive", pulse = drive_test_pulse, increment_oscillator_phase=np.pi/2)
        exp_test.delay(signal = "drive", time = 160e-9)
        exp_test.play(signal = "drive", pulse = drive_test_pulse, increment_oscillator_phase=np.pi/2)
        exp_test.delay(signal = "drive", time = 160e-9)
        exp_test.play(signal = "drive", pulse = drive_test_pulse, increment_oscillator_phase=np.pi/2)
        exp_test.delay(signal = "drive", time = 160e-9)
        exp_test.play(signal = "drive", pulse = drive_test_pulse, increment_oscillator_phase=np.pi/2)
        exp_test.delay(signal = "drive", time = 160e-9)

        exp_test.delay(signal = "measure", time = 50e-9)

exp_calibration = Calibration()
measure_osc = Oscillator(frequency = 20e6)
drive_osc = Oscillator(frequency = 20e6)

exp_calibration["drive"] = SignalCalibration(
    oscillator = drive_osc
)

exp_calibration["measure"] = SignalCalibration(
    oscillator = measure_osc
)

exp_calibration["acquire"] = SignalCalibration(
    oscillator = measure_osc,
    port_delay=0e-9
)

exp_test.set_calibration(exp_calibration)

lsg = device.logical_signal_groups["d1"]
exp_test.map_signal("drive", lsg.logical_signals["drive_line"])
exp_test.map_signal("measure", lsg.logical_signals["measure_line"])
exp_test.map_signal("acquire", lsg.logical_signals["acquire_line"])

compiled_exp = session.compile(exp_test)
show_pulse_sheet("pulse_sheets/voltage_level_test", compiled_exp)
results = session.run(exp_test, include_results_metadata=True)


# %%
import matplotlib.pyplot as plt
axis = results.get_axis("acquire")
data = results.get_data("acquire")
plt.figure()
plt.plot(axis[0]/2, np.abs(data), label = "abs")
plt.plot(axis[0]/2, np.real(data), label="Real (I)", alpha=0.7)
plt.plot(axis[0]/2, np.imag(data), label="imag (I)", alpha=0.7)

plt.legend()
plt.show()
# %%
