# #%%
# from test.time_of_flight_no_workflow import time_of_flight
# from Experimental_Setup_Parameters.tune_up_parameters import TuneUpProcessOptions, time_of_flight_parameters
# from laboneq import workflow
# from sources.calibration_helpers import calibrate_devices
# from laboneq.simple import Session
# from laboneq.workflow.logbook import FolderStore

# device = calibrate_devices()
# session = Session(device_setup = device)

# @workflow.workflow(name = "time_of_flight_name")
# def final_tof(
#     experiment_parameters : time_of_flight_parameters,
#     experiment_options : TuneUpProcessOptions,
#     ) -> None:

#     time_of_flight(experiment_parameters=experiment_parameters, 
#                    experiment_options = experiment_options)

# exp_option = TuneUpProcessOptions(id = "test", show_figure = True)
# exp_params = time_of_flight_parameters(Num_avg = 2, Delay_time_points= 2)
# exp = final_tof(exp_params, exp_option)
# # %%
# from laboneq_applications.experiments import resonator_spectroscopy
# from sources.calibration_helpers import calibrate_devices
# device = calibrate_devices()
# device_setup = device.setup
# qpu = device.qpu
# session = Session()
# session.connect()
# resonator_spectroscopy.experiment_workflow()
# #%% 
# from laboneq_applications.experiments import qubit_spectroscopy, resonator_spectroscopy, amplitude_rabi, time_traces
# from laboneq.simple import Session
# from sources.calibration_helpers import calibrate_devices
# import numpy as np
# from copy import deepcopy
# from laboneq.dsl.quantum import QuantumElement

# qubit_spectroscopy.experiment_workflow.src

# device = calibrate_devices()
# device_setup = device.setup
# qpu = device.qpu
# qubits = qpu.quantum_elements

# session = Session(device_setup)
# session.connect()
# options = resonator_spectroscopy.experiment_workflow.options()
# options.update(True)

# qubit_to_measure = qubits[0]

# temporary_parameters = deepcopy(qubit_to_measure.parameters)
# temporary_parameters.readout_range_out = -20
# temporary_parameters.readout_range_in = -10

# #%%
# exp_workflow = resonator_spectroscopy.experiment_workflow(session= session, qpu=qpu, qubit = qubit_to_measure, temporary_parameters= {qubit_to_measure.uid : temporary_parameters}, frequencies = qubit_to_measure.parameters.readout_resonator_frequency+np.linspace(-20e6,20e6,201), options=options)
# exp_workflow.run()
# #%%
# qpu.qubits[0].parameters
#%%
# from laboneq.simple import Session
# from sources.calibration_helpers import calibrate_devices
# import numpy as np
# from copy import deepcopy
# from Main_Experiments_Def import time_of_flight
# from sources.utils import *

# device = calibrate_devices()
# device_setup = device.setup
# qpu = device.qpu
# qubits = qpu.quantum_elements

# session = Session(device_setup)
# session.connect()
# options = time_of_flight.experiment_workflow.options()
# options.update_parameters(True)

# qubit_to_measure = qubits

# # temporary_parameters = deepcopy(qubit_to_measure.parameters)
# # temporary_parameters.readout_range_out = -20
# # temporary_parameters.readout_range_in = -10

# exp_workflow = time_of_flight.experiment_workflow(session= session, qpu=qpu, qubits = qubit_to_measure, options=options)
# exp_workflow.run()

#%%
from laboneq_applications.experiments import qubit_spectroscopy, resonator_spectroscopy, amplitude_rabi, time_traces

from laboneq.simple import Session
from sources.calibration_helpers import calibrate_devices
import numpy as np
from copy import deepcopy
from Main_Experiments_Def import time_of_flight
from sources.utils import *
from sources.QDLTransmon_def import QDLTransmon
from laboneq_applications.experiments.options import (
    ResonatorSpectroscopyExperimentOptions,
    QubitSpectroscopyExperimentOptions,
    TuneupExperimentOptions,
    TuneUpWorkflowOptions,
)

device = calibrate_devices()
device_setup = device.setup
qpu = device.qpu
qubits = qpu.quantum_elements

session = Session(device_setup)
session.connect()



options = TuneUpWorkflowOptions()
options.update = True
resonator_spectroscopy_options = ResonatorSpectroscopyExperimentOptions()
tuneupoptions = TuneupExperimentOptions()
tuneupoptions.use_cal_traces = False

qubit_to_measure = qubits[0]
resonator_spec_frequencies = (qubit_to_measure.parameters.readout_resonator_frequency+np.linspace(-20e6, 20e6, 201)).tolist()
qubit_spec_frequencies = qubit_to_measure.parameters.resonance_frequency_ge+np.linspace(-20e6, 20e6, 201)
amplitude_rabi_amplitudes = np.linspace(0, 1.0, 21).tolist()

@workflow.workflow(name = "ResSpec_to_Raby")
def experiment_workflow(
    session: Session,
    qpu : QPU,
    qubits : QDLTransmon,
    resonator_spec_frequencies,
    qubit_spec_frequencies,
    amplitude_rabi_amplitudes,
    options : TuneUpWorkflowOptions |None = None
) -> None:
    resonator_spectroscopy.experiment_workflow(
        session=session,
        qpu=qpu,
        frequencies=resonator_spec_frequencies,
        qubit=qubits)
    qubit_spectroscopy.experiment_workflow(
        session=session,
        qpu=qpu,
        frequencies=qubit_spec_frequencies,
        qubits=[qubits])
    amplitude_rabi.experiment_workflow(
        session=session,
        qpu=qpu,
        amplitudes=amplitude_rabi_amplitudes,
        qubits=[qubits])


# exp = experiment_workflow(
#     session, 
#     qpu, 
#     qubit_to_measure, 
#     resonator_spec_frequencies= resonator_spec_frequencies,
#     qubit_spec_frequencies=qubit_spec_frequencies,
#     amplitude_rabi_amplitudes=amplitude_rabi_amplitudes,
#     options = options)
# exp.run()
#%%
from laboneq_applications.experiments import qubit_spectroscopy, resonator_spectroscopy, amplitude_rabi, time_traces

from laboneq.simple import Session
from sources.calibration_helpers import calibrate_devices
import numpy as np
from copy import deepcopy
from Main_Experiments_Def import time_of_flight
from sources.utils import *
from sources.QDLTransmon_def import QDLTransmon
from laboneq_applications.experiments.options import (
    ResonatorSpectroscopyExperimentOptions,
    QubitSpectroscopyExperimentOptions,
    TuneupExperimentOptions,
    TuneUpWorkflowOptions,
)

device = calibrate_devices()
device_setup = device.setup
qpu = device.qpu
qubits = qpu.quantum_elements
qubit_to_measure = qubits[0]
session = Session(device_setup)
session.connect()


#%%
option = qubit_spectroscopy.experiment_workflow.options()
option.use_cal_traces(False)
option.acquisition_type(AcquisitionType.SPECTROSCOPY)
option.count(60000)

qubit_spec_frequencies = qubit_to_measure.parameters.resonance_frequency_ge+np.linspace(-20e6, 20e6, 601)
# print(qubit_spec_frequencies)
exp_qubit_spec = qubit_spectroscopy.experiment_workflow(
        session=session,
        qpu=qpu,
        frequencies=qubit_spec_frequencies,
        qubits=qubit_to_measure,
        options = option)
exp_qubit_spec.run()
# %%
option = resonator_spectroscopy.experiment_workflow.options()
option.use_cal_traces(True)
option.update(True)
option.count(100000)
option.include_results_metadata(True)
# option.acquisition_type(AcquisitionType.SPECTROSCOPY)

resonator_spec_frequencies = qubit_to_measure.parameters.readout_resonator_frequency+np.linspace(-20e6, 20e6, 401)
exp_res = resonator_spectroscopy.experiment_workflow(
        session=session,
        qpu=qpu,
        frequencies=resonator_spec_frequencies,
        qubit=qubit_to_measure,
        options = option)
exp_res.run()
# %%
