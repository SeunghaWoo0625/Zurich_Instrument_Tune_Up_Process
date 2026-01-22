#%%
import utils

print(utils.validate_device_existence())
from sources.calibration_helpers import calibrate_devices

cal = calibrate_devices(measure = "spec_square")

#%%
import utils
from laboneq.simple import *

device_qubit_configs = utils.get_device_qubit_config()
HDAWG(**device_qubit_configs["device"]["hdawg_0"])
# %%
