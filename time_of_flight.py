from laboneq import workflow
from laboneq.simple import *
from sources.calibration_helpers import calibrate_devices

@workflow.task
def time_of_flight(id, qubit_parameters, device_qubit_config,
                   Num_avg = 1000, 
                   Delay_time_begin = 0e-9, 
                   Delay_time_end = 150e-9, 
                   Delay_time_points=150, 
                   Measure_length = 100e-9):
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

    for qubit in device_qubit_config["qubits"]:
        baseline_calibration = calibrate_devices()
        session = Session(device_setup=baseline_calibration)
        session.connect()

        exp = time_of_flight_experiment(qubit, delay_time_sweeper, readout_pulse, Num_avg)
        lsg = baseline_calibration.logical_signal_groups

        
@workflow.task
def time_of_flight_experiment(qubit, delay_time_sweeper, readout_pulse, Num_avg):
    exp_tof = Experiment(id = "time_of_flight")

    with exp_tof.sweep(uid = "delay_time_sweep", parameter = delay_time_sweeper):
        with exp_tof.acquire_loop_rt(uid = "raw_data_acquisition",
                                     count = Num_avg,
                                     acquisition_type=AcquisitionType.RAW):
            with exp_tof.section(uid = "mesure", on_system_grid=True, alignment=SectionAlignment.LEFT):
                exp_tof.play(signal = f"{qubit}_measure", pulse = readout_pulse)
                exp_tof.acquire(singal = f"{qubit}_acquire", pulse = readout_pulse)
                

    exp_calibration = Calibration()
    exp_calibration["acquire"] = SignalCalibration(
        port_delay=delay_time_sweeper,
    )
    exp_tof.set_calibration(exp_calibration)
    return exp_tof
