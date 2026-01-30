#%%
from laboneq import workflow
# from laboneq import dsl
from laboneq.simple import dsl, Experiment, AcquisitionType, AveragingMode, show_pulse_sheet
from laboneq.workflow.tasks import (
    compile_experiment,
    run_experiment
)
from laboneq.dsl.quantum.qpu import QPU
from laboneq_applications.tasks.parameter_updating import (
    temporary_qpu,
    temporary_quantum_elements_from_qpu,
    update_qpu,
)
from laboneq.dsl.session import Session
from laboneq_applications.core import validation

import numpy as np
from numpy.typing import ArrayLike

from sources.QDLTransmon_def import QDLTransmon, QDLTransmonOperations, QDLTransmonParameters
from Experimental_Setup_Parameters.tune_up_options import TuneUpProcessOptions, TimeOfFlightExperimentOptions
from sources.calibration_helpers import calibrate_devices
import sources.utils as utils
from laboneq.dsl.parameter import SweepParameter
from laboneq_applications.typing import QuantumElements, QubitSweepPoints

@workflow.workflow(name = "time_of_flight")
def experiment_workflow(
    session: Session,
    qpu: QPU,
    qubits : QuantumElements,
    temporary_parameters : dict[str, dict | QDLTransmon] | None = None,
    options : TuneUpProcessOptions | None = None, # metadata 저장 RunExperimentOptions(include_results_metadata = True)
) -> None:
    temp_qpu = temporary_qpu(qpu, temporary_parameters)
    qubits = temporary_quantum_elements_from_qpu(temp_qpu, qubits)
    exp = create_experiment(
        temp_qpu,
        qubits
    )
    compiled_exp = compile_experiment(session, exp)
    # with workflow.if_(options.save_pulse_sheet):
    #     show_pulse_sheet(PULSE_SHEET_SAVE_PATH, compiled_exp)
    result = run_experiment(session, compiled_exp)
    # with workflow.if_(options.do_analysis):
    #     analysis_results = analysis_workflow(result, qubit, frequencies)
    #     qubit_parameters = analysis_results.output
    #     with workflow.if_(options.update_parameters):
    #         update_qpu(qpu, qubit_parameters["new_parameter_values"])
    workflow.return_(result)


@workflow.task
@dsl.qubit_experiment
def create_experiment(
    qpu: QPU,
    qubits: QuantumElements,
    options: TimeOfFlightExperimentOptions | None = None,
) -> Experiment:
    options = TimeOfFlightExperimentOptions() if options is None else options
    sweeper = [np.linspace(options.Delay_time_begin, options.Delay_time_end, options.Delay_time_points) for i in qubits]
    qubits, time_delays = validation.validate_and_convert_qubits_sweeps(qubits, sweeper)
    qop = qpu.quantum_operations
    # for q, q_time_delay in zip(qubits, time_delays):
    #     print(q, q_time_delay)
    with dsl.acquire_loop_rt(
                count = options.count,
                averaging_mode = AveragingMode.CYCLIC,
                acquisition_type = AcquisitionType.RAW
    ):
        for q, q_time_delay in zip(qubits, time_delays):
            print(q, q_time_delay)
            with dsl.sweep(
                name = "delay_sweep",
                parameter = SweepParameter("Delay_sweep_{qubit.uid}", q_time_delay),
            )as time_delay:
                calibration = dsl.experiment_calibration()
                signal_calibration = calibration[q.signals["acquire"]]
                signal_calibration.port_delay = time_delay
#                 sec = qop.measure(q, dsl.handles.result_handle(q.uid))
#                 sec.length = 1e6
#                 qop.passive_reset(q, delay=options.passive_reset_delay)
