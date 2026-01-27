#%%
from sources.calibration_helpers import calibrate_devices
from laboneq.simple import *
import utils
import numpy as np

test_pulse = pulse_library.const(length= 100e-9, amplitude= 0.5)

device = calibrate_devices(measure_type = "spec_square")

test_exp = Experiment(
    uid = "test_exp",
    signals = [
        ExperimentSignal("measure"),
        ExperimentSignal("acquire")
    ]
)

with test_exp.acquire_loop_rt(
    uid = "test_exp_acquire_section",
    count = 1000,
    acquisition_type = AcquisitionType.RAW
):
    with test_exp.section(uid="play_section",on_system_grid=True, alignment=SectionAlignment.RIGHT):
        test_exp.play(uid="measure_signal",pulse = test_pulse, phase = np.pi/4)
    with test_exp.section(uid = "acquire_section", play_after="play_section",on_system_grid=True, alignment=SectionAlignment.RIGHT):
        test_exp.acquire(uid="acquire_signal")

qubit_parameters = utils.get_qubit_params()

session = Session(qubit_parameters, device_setup=device)
session.connect()

lsg = device.logical_signal_groups["d1"]
test_exp.map_signal("measure", device.logical_signal_groups["d1"].logical_signals["measure_line"])
test_exp.map_signal("acquire", device.logical_signal_groups["d1"].logical_signals["acquire_line"])

compiled_exp = session.compile(test_exp)

results = session.run(compiled_exp, include_results_metadata=True)

# %%
