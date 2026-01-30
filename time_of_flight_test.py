from laboneq_applications.experiments import qubit_spectroscopy, resonator_spectroscopy, amplitude_rabi, time_traces
from laboneq.simple import Session
from sources.calibration_helpers import calibrate_devices
import numpy as np
from copy import deepcopy
from Main_Experiments_Def import time_of_flight_multi_qubits
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

exp_tof = time_of_flight_multi_qubits.experiment_workflow(session=session, qpu=qpu, qubits=qubits)
results = exp_tof.run()