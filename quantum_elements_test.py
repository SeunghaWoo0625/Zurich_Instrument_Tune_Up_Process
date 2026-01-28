#%%
from sources.calibration_helpers import calibrate_devices
from laboneq.simple import *
from laboneq.dsl.quantum import (
    QPU,
    QuantumElement,
    QuantumOperations,
    QuantumParameters,
    Transmon,
)


device = calibrate_devices(qubit_list = ["d1","d2"])
qubits = Transmon.from_device_setup(device)
print(qubits)

session = Session(device_setup=device)

# %%
import utils
device_qubit_configs = utils.get_device_qubit_config()
a = device_qubit_configs["qubits"].keys()

qubits[0].parameters.custom.T1 = 10
#%%
class TransmonOperations(QuantumOperations):
    QUBIT_TYPES = Transmon

    @dsl.quantum_operation
    def flux_pulse(
        self,
        q: Transmon,
        amplitude: float | SweepParameter,
        length: float | SweepParameter,
        phase: float = 0.0,
    ) -> None:
        pulse_parameters = {"function": "gaussian_square", "sigma": 0.42}
        flux_pulse = dsl.create_pulse(pulse_parameters, name="flux_pulse")

        dsl.play(
            q.signals["flux"],
            amplitude=amplitude,
            length=length,
            phase=phase,
            pulse=flux_pulse,
        )
        dsl.reserve
        dsl.play
        



qpu = QPU(quantum_elements=qubits, quantum_operations= [TransmonOperations])
# %%
