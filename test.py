import utils
from sources.calibration_helpers import calibrate_devices
from laboneq.simple import *
from laboneq.contrib.example_helpers.plotting.plot_helpers import plot_simulation
device_qubit_configs = utils.get_device_qubit_config()
for signal in device_qubit_configs["qubit"]["d1"]:
    if signal not in ["measure", "acquire", "flux"]:  # drive 신호만 처리
        print(f"Signal: {signal}")