#%%
from laboneq.dsl.quantum import Transmon
from sources.calibration_helpers import calibrate_devices
from pathlib import Path
#%%
# quantum platform
device = calibrate_devices()
#%% quantum platform은 qpu랑 setup으로 이루어져 있다.
qpu  = device.qpu 
device_setup = device.setup
#%% qpu는 qubit의 list인 quantum_elements 그 quantum_elements에 작용하는 quantum operations들로 이루어져 잇음
qubits = qpu.quantum_elements
qop = qpu.quantum_operations
#%% qubit에는 uid, parameters, signals기 있다
q0_uid = qubits[0].uid
q0_parameters = qubits[0].parameters
q0_signals = qubits[0].signals
#%% quantum operations에는 여러 operations들이 정의되어있다.
qop_all = qop.keys()
print(qop.set_frequency.src)

#%% ========================================================================
from sources.QDLTransmon_def import *
qubits[0].calibration()
# %%
from sources.calibration_helpers import calibrate_devices
from laboneq_applications.qpu_types.tunable_transmon import TunableTransmonQubit
from sources.utils import get_qubit_params
q_param = get_qubit_params()
device = calibrate_devices()
transmon = TunableTransmonQubit.from_device_setup(device.setup)
transmon[0].parameters.replace(**q_param["d1"])
#%% 
transmon[0].parameters.readout_frequency()
#%%
from sources.QDLTransmon_def import *
QDLTransmonParameters.type