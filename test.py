import os         
from pathlib import Path
import utils
import json

qbn = 0
folder_path = Path("experiment_results")
device_qubit_config = utils.get_qubit_params()

device_qubit_config_file_full_name = os.path.join(folder_path, f"{qbn}_device_qubit_config.json")
with open(device_qubit_config_file_full_name, 'w', encoding='utf-8') as f:
    json.dump(device_qubit_config, f, indent=4, ensure_ascii=False)
#%%
from sources.fitting_helpers import power_to_voltage
print(power_to_voltage(10))
# %%
from sources.fitting_helpers import voltage_to_power
print(voltage_to_power(10**0.5))

# %%
