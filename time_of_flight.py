from laboneq import workflow
from laboneq.simple import *
from sources.calibration_helpers import calibrate_devices
from sources.signal_helpers import *
from datetime import datetime
from pathlib import Path
import utils
from sources.fitting_helpers import time_of_flight_figure

@workflow.task
def time_of_flight(qubit_parameters, device_qubit_config, 
                   tuneup_parameters=None, 
                   id = "default",
                   Num_avg = 1000, 
                   Delay_time_begin = 0e-9, 
                   Delay_time_end = 150e-9, 
                   Delay_time_points= 150, 
                   Measure_length = 100e-9,
                   save_pulse_sheet = True):
    """
    readout pulse를 쏴주고, 돌아오는 신호를 raw data로 읽는 실험
    kernel을 시작하는 delay를 sweep해서 첫 신호가 가장 클때의 delay로 정한다.
    Delay_time_begin : sweep할 delay 시작 값
    Delay_time_end : sweep할 delay 마지막 값
    Delay_time_points : sweep할 delay 값 개수 
    Measure_length : readout할 kernel 길이
    """

    delay_time_sweeper = LinearSweepParameter(uid="delay_sweep", 
                                        start=Delay_time_begin, 
                                        stop=Delay_time_end, 
                                        count=Delay_time_points, 
                                        axis_name="Time (s)")
    
    readout_pulse = pulse_library.const(uid="readout_pulse", length=Measure_length)
    now = datetime.now()    
    time_str = now.strftime("%y%m%d_%H%M%S")
    results_folder_path = Path(f"experiment_results/{id}/{time_str}_{Path(__file__).stem}")
    results_folder_path.mkdir(parents=True, exist_ok=True)

    for i, device in enumerate(device_qubit_config["devices"]):
        if "shfqc" in device:
            baseline_calibration = calibrate_devices(measure_type = "spec_square")
            session = Session(device_setup=baseline_calibration)
            session.connect()

            for qubit in device_qubit_config["qubits"]:
                if device_qubit_config["qubits"][qubit]["measure"]["device"] == device:
                    break

            exp = time_of_flight_experiment(qubit, delay_time_sweeper, readout_pulse, Num_avg)
            
            auto_map_signals(exp, baseline_calibration)
            compiled_exp = session.compile(exp)
            if save_pulse_sheet == True:
                show_pulse_sheet(results_folder_path / f"{device}_pulse_sheet", compiled_exp)
            results = session.run(compiled_exp, include_results_metadata=True)
            figure = time_of_flight_figure(results)

            if i == 0:
                utils.save_fig_qubit_params(results_folder_path, results, figure, device, qubit_parameters=qubit_parameters, device_qubit_config=device_qubit_config, tuneup_parameters=tuneup_parameters)
            else:
                utils.save_fig_qubit_params(results_folder_path, results, figure, device)
        
@workflow.task
def time_of_flight_experiment(qubit, delay_time_sweeper, readout_pulse, Num_avg, reset_delay_length = 70e-6):
    exp_tof = Experiment(uid = "time_of_flight")

    with exp_tof.sweep(uid = "delay_time_sweep", parameter = delay_time_sweeper):
        with exp_tof.acquire_loop_rt(uid = "raw_data_acquisition",
                                     count = Num_avg,
                                     acquisition_type=AcquisitionType.RAW):
            with exp_tof.section(uid = "mesure", on_system_grid=True, alignment=SectionAlignment.LEFT):
                exp_tof.play(signal = f"{qubit}_measure_signal", pulse = readout_pulse)
                exp_tof.acquire(signal = f"{qubit}_acquire_signal", handle = f"{qubit}_acquire_handle", kernel = readout_pulse)
                exp_tof.delay(signal = f"{qubit}_measure_signal", time = reset_delay_length)
                exp_tof.delay(signal = f"{qubit}_acquire_signal", time = reset_delay_length)

    exp_calibration = Calibration()
    exp_calibration["acquire"] = SignalCalibration(
        port_delay=delay_time_sweeper,
    )
    exp_tof.set_calibration(exp_calibration)
    return exp_tof

if __name__ == "__main__":
    qubit_parameters = utils.get_qubit_params()
    device_qubit_config = utils.get_device_qubit_config()
    time_of_flight(qubit_parameters, device_qubit_config)