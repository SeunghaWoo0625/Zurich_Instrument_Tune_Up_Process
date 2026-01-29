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
from laboneq.simple import Session
from sources.calibration_helpers import calibrate_devices
import numpy as np
from copy import deepcopy
from Main_Experiments_Def import time_of_flight
from sources.utils import *

device = calibrate_devices()
device_setup = device.setup
qpu = device.qpu
qubits = qpu.quantum_elements

session = Session(device_setup)
session.connect()
options = time_of_flight.experiment_workflow.options()
options.update_parameters(True)

qubit_to_measure = qubits[0]

temporary_parameters = deepcopy(qubit_to_measure.parameters)
temporary_parameters.readout_range_out = -20
temporary_parameters.readout_range_in = -10

exp_workflow = time_of_flight.experiment_workflow(session= session, qpu=qpu, qubits = qubit_to_measure, temporary_parameters= {qubit_to_measure.uid : temporary_parameters}, options=options)
exp_workflow.run()