#%%
import utils
from sources.calibration_helpers import calibrate_devices
from laboneq.simple import *
from laboneq.contrib.example_helpers.plotting.plot_helpers import plot_simulation

baseline_calibration = calibrate_devices("INTEGRATION")
exp_basic = Experiment(
    uid = "exp_basic",
    signals=[
        ExperimentSignal("mesure"),
        ExperimentSignal("acquire"),
    ]
)

# %%
for keys in exp_basic.signals.keys():
    print(keys)
# %%
