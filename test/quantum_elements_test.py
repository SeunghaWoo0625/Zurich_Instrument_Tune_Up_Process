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
import sources.utils as utils
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
from laboneq.simple import *

@workflow.task_options
class ExperimentOptions:
    id:str = "default"
    Num_avg: int = 1000
    experiment_points: int = 100
    save_pulse_sheet:bool = True
    save_figure:bool = True
    save_results:bool = True
    save_simulation:bool = False


# %%
a = ExperimentOptions()
print(a)
# %%
import sources.utils as utils
@workflow.task
def time_of_flight(                   experiment_options : ExperimentOptions = ExperimentOptions(),
                   qubit_parameters = utils.get_qubit_params(),
                   device_qubit_config=utils.get_device_qubit_config(),
                   tuneup_parameters=utils.get_tuneup_params(),
                   ):
    print(experiment_options)
    print(qubit_parameters)
# %%
time_of_flight()