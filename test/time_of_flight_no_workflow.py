#%%
from laboneq import workflow
from laboneq.simple import *
from sources.calibration_helpers import calibrate_devices
from sources.signal_helpers import *
from datetime import datetime
from pathlib import Path
import sources.utils as utils
from sources.fitting_helpers import time_of_flight_figure
from sources.logging_helpers import data_logger
from Experimental_Setup_Parameters.tune_up_parameters import *
import matplotlib.pyplot as plt

@workflow.task
def time_of_flight(experiment_parameters : time_of_flight_parameters = time_of_flight_parameters(),
                   experiment_options : TuneUpProcessOptions = TuneUpProcessOptions(),
                   qubit_parameters_optional : dict | None = None,
                   qubit_parameters : dict = utils.get_qubit_params(),
                   device_qubit_config : dict = utils.get_device_qubit_config(),
                   ):
    
    """
    readout pulse를 쏴주고, 돌아오는 신호를 raw data로 읽는 실험
    kernel을 시작하는 delay를 sweep해서 첫 신호가 가장 클때의 delay로 정한다.
    Delay_time_begin : sweep할 delay 시작 값
    Delay_time_end : sweep할 delay 마지막 값
    Delay_time_points : sweep할 delay 값 개수 
    Measure_length : readout할 kernel 길이
    """
    if qubit_parameters_optional is not None:
        utils.deep_update(qubit_parameters, qubit_parameters_optional)

    print("experiment_parameters :", experiment_parameters)
    print("experiment_parameters :", experiment_options)
    
    delay_time_sweeper = LinearSweepParameter(uid="delay_sweep", 
                                        start=experiment_parameters.Delay_time_begin, 
                                        stop=experiment_parameters.Delay_time_end, 
                                        count=experiment_parameters.Delay_time_points, 
                                        axis_name="Time (s)")
    
    readout_pulse = pulse_library.const(uid="readout_pulse", length=experiment_parameters.Measure_length, amplitude = 0.8)
    now = datetime.now()    
    time_str = now.strftime("%y%m%d_%H%M%S")
    results_folder_path = Path(f"experiment_results/{experiment_options.id}/{time_str}_{Path(__file__).stem}")
    results_folder_path.mkdir(parents=True, exist_ok=True)

    for i, device in enumerate(device_qubit_config["devices"]):
        if "shfqc" in device:
            baseline_calibration = calibrate_devices(measure_type = "spec_square")
            session = Session(device_setup=baseline_calibration)
            session.connect()

            for qubit in device_qubit_config["qubits"]:
                if device_qubit_config["qubits"][qubit]["measure"]["device"] == device:
                    break

            exp = time_of_flight_experiment(qubit, delay_time_sweeper, readout_pulse, experiment_parameters.Num_avg, experiment_parameters.reset_delay_length)
            
            auto_map_signals(exp, baseline_calibration)
            compiled_exp = session.compile(exp)
            if experiment_options.save_pulse_sheet == True:
                show_pulse_sheet(results_folder_path / f"{device}_pulse_sheet", compiled_exp)

            results = session.run(compiled_exp, include_results_metadata=True)
            figure, optimal_delay = time_of_flight_figure(results, qubit, device)
            if experiment_options.show_figure == True:
                plt.show()

            # if experiment_options.save_results == True:
            #     data_logger(results, "time_of_flight", time_str, experiment_options.author, qubit_parameters, parameters.__dict__)
            if experiment_options.save_figure == True:
                utils.save_fig_qubit_params(results_folder_path, results, figure, device, qubit_parameters=qubit_parameters, device_qubit_config=device_qubit_config)
            else:
                utils.save_fig_qubit_params(results_folder_path, results, figure, device)
        
@workflow.task
def time_of_flight_experiment(qubit, delay_time_sweeper, readout_pulse, Num_avg, reset_delay_length = 70e-6):
    exp_tof = Experiment(uid = "time_of_flight")

    with exp_tof.sweep(uid = "delay_time_sweep", parameter = delay_time_sweeper):
        with exp_tof.acquire_loop_rt(uid = "raw_data_acquisition",
                                     count = Num_avg,
                                    #  averaging_mode=AveragingMode.CYCLIC,
                                     acquisition_type=AcquisitionType.RAW):
            with exp_tof.section(uid = "mesure", on_system_grid=True, alignment=SectionAlignment.LEFT):
                exp_tof.play(signal = f"{qubit}_measure_signal", pulse = readout_pulse)
                exp_tof.signals[f"{qubit}_measure_signal"] = ExperimentSignal(f"{qubit}_measure_signal")
                exp_tof.acquire(signal = f"{qubit}_acquire_signal", handle = f"{qubit}_acquire_handle", kernel = readout_pulse)
                exp_tof.signals[f"{qubit}_acquire_signal"] = ExperimentSignal(f"{qubit}_acquire_signal")
                exp_tof.delay(signal = f"{qubit}_measure_signal", time = reset_delay_length)
                exp_tof.delay(signal = f"{qubit}_acquire_signal", time = reset_delay_length)



    exp_calibration = Calibration()
    exp_calibration[f"{qubit}_acquire_signal"] = SignalCalibration(
        port_delay=delay_time_sweeper,
    )
    exp_tof.set_calibration(exp_calibration)
    return exp_tof

if __name__ == "__main__":
    

    @workflow.workflow
    def run_time_of_flight():
        exp_option = ExperimentOptions(id = "test", show_figure = True)
        time_of_flight(experiment_options=exp_option)
    
    run_time_of_flight().run()
# %%
