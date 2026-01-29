#!/usr/bin/env python3
#%%
from laboneq.simple import *
from laboneq.contrib.example_helpers.plotting.plot_helpers import plot_simulation
from fitting_helpers import *
from calibration_helpers import calibrate_devices
import sources.utils as utils
import sys
from fitting_helpers import *

emulation_mode = False

def drive_pulses(id, qubit_params, qubit_num, handle = "ge", **kwarg): #square, gaussian, gaussian_square, drag
    drive_parameters = qubit_params[f"Q{qubit_num}"]["DRV"]
    qa_parameters = qubit_params["QA"][qubit_params[f"Q{qubit_num}"]["DRV"]["device"]]

    if handle == None:
        return None
    
    elif handle == "ge":
        match id:
            case "spec" :
                return pulse_library.const(**kwarg, length=drive_parameters["spec_pulse_length"], 
                    amplitude=drive_parameters["spec_pulse_amp"])
                
            case "spec_gaussian":
                return pulse_library.gaussian(**kwarg, length=drive_parameters["spec_pulse_length"],
                                              amplitude = drive_parameters["spec_pulse_amp"])
                    
            case "gaussian":
                return pulse_library.gaussian(**kwarg, length=drive_parameters["pulse_length"],
                                              amplitude = drive_parameters["amp_pi"])
                
            case "gaussian_square":
                return pulse_library.gaussian_square(**kwarg)
            case "drag":
                return pulse_library.drag(**kwarg, beta = drive_parameters["beta"])
            
            case "pi":
                return pulse_library.drag(**kwarg, length=drive_parameters["pulse_length"],
                                              amplitude=drive_parameters["amp_pi"],
                                              beta = drive_parameters["beta"])
            case "half_pi":
                return pulse_library.drag(**kwarg, length=drive_parameters["pulse_length"],
                                              amplitude=drive_parameters["amp_half_pi"],
                                              beta = drive_parameters["beta"])
            case _:
                raise ValueError(f"유효하지 않은 pulse입니다: {id}")

def measure_pulses(id, qubit_params, qubit_num, handle = None, **kwarg): #square, gaussian, gaussian_square, drag
    measure_parameters = qubit_params[f"Q{qubit_num}"]["RO"]
    qa_parameters = qubit_params["QA"][qubit_params[f"Q{qubit_num}"]["DRV"]["device"]]

    if handle == None:
        match id:
            case "state_readout":
                return pulse_library.const(**kwarg, 
                length=measure_parameters["pulse_length"], 
                amplitude=measure_parameters["pulse_amp"])
            
            case "spec":
                return pulse_library.const(**kwarg,
                length=measure_parameters["spec_pulse_length"], 
                amplitude=measure_parameters["spec_pulse_amp"])
            
            case _:
                raise ValueError(f"유효하지 않은 pulse입니다: {id}")
        
def integration_pulses(id, qubit_params, qubit_num ,  **kwarg):
    #작성하기

    return

# Define experiment
def res_spec(frequency_sweep, num_avg, reset_delay, readout_pulse, integration_pulse):

    exp_spec = Experiment(
        uid="res_spec",
        signals=[
            ExperimentSignal("measure"),  #뒤에 있는 logical signal mapping을 위하여...
            ExperimentSignal("acquire"),
        ],
    )

    with exp_spec.acquire_loop_rt(
        uid="shots",
        count=pow(2, num_avg),
        acquisition_type=AcquisitionType.SPECTROSCOPY,
    ):
        with exp_spec.sweep(uid="res_freq", parameter=frequency_sweep):
            with exp_spec.section(uid="spectroscopy"):
                exp_spec.measure(
                    measure_signal="measure",
                    measure_pulse=readout_pulse,
                    acquire_signal="acquire",
                    integration_kernel=integration_pulse,
                    handle=exp_spec.uid,
                    reset_delay=reset_delay, #parameter_id로 변경
                )
    
    exp_calibration = Calibration()
    ro_osc = Oscillator(
            uid="readout_osc",
            frequency=frequency_sweep,
            modulation_type=ModulationType.HARDWARE,
        )
    exp_calibration["measure"] = SignalCalibration(
        oscillator=ro_osc,
    )
    exp_calibration["acquire"] = SignalCalibration(
        oscillator=ro_osc,
    )
    exp_spec.set_calibration(exp_calibration)
    return exp_spec

def run_01_res_spec(qubit_list, AUTO = True, EXPERIMENT_ID = "Test", pulse_show = False):
    # Load qubit tuneup parameters 
    qubit_params, qubit_param_f_path = utils.get_qubit_params(__file__)
    tuneup_parameters, _ = utils.get_tuneup_params(__file__)
    function_id = sys._getframe().f_code.co_name.replace("run_","")
    tuneup_params = tuneup_parameters[function_id]

    # Apply baseline calibration of devices
    baseline_calibration = calibrate_devices(qubit_list, qubit_params, type = "SPECTROSCOPY")
    # Create and connect to a session
    session = Session(device_setup=baseline_calibration)
    session.connect(do_emulation=emulation_mode)  #Emulation mode 설정 (True or False)
    
    for qbn in qubit_list:
        qubit = qubit_params[f"Q{qbn}"]
        device = qubit["DRV"]["device"]
        port = qubit["DRV"]["port"]
        qa = qubit_params["QA"][device]
        sg = qubit_params["SG"][device]

        start_freq = qubit["RO"]["freq"] - qa["LO"] - tuneup_params["Freq_span"]/2
        stop_freq = qubit["RO"]["freq"] - qa["LO"] + tuneup_params["Freq_span"]/2

        frequency_sweep = LinearSweepParameter(uid="res_freq_sweep",
                                            start=start_freq, 
                                            stop=stop_freq, 
                                            count=tuneup_params["Exp_pts"], 
                                            axis_name="Frequency (Hz)")

        print(frequency_sweep)
        
        readout_pulse = measure_pulses(tuneup_params["Measure_pulse"], qubit_params, qbn, uid = f"{function_id}_readout_pulse")
                
        if tuneup_params["Integration_pulse"] == "none":
            integration_pulse = readout_pulse
        else:
            integration_pulse = integration_pulses(tuneup_params["Integration_pulse"], qubit_params, qbn, uid = f"{function_id}_integration_pulse")

        # Create experiment
        exp_spec = res_spec(frequency_sweep, tuneup_params["Num_avg"], qa["reset_delay_length"], readout_pulse, integration_pulse)

        # Mapping
        lsg = baseline_calibration.logical_signal_groups[f"q{qbn}"]
        exp_spec.map_signal("measure", lsg.logical_signals["measure_line"])
        exp_spec.map_signal("acquire", lsg.logical_signals["acquire_line"])

        # Compile and run
        compiled_exp = session.compile(exp_spec)
        if pulse_show:
            show_pulse_sheet("pulse_show", compiled_exp)

        # plot_simulation(compiled_exp)
        results = session.run(compiled_exp, include_results_metadata=True)
        fig, fr = res_spec_fit_plot(results, qubit_params, qbn)
        
        utils.save_fig_qubit_params(results, fig, qubit_params, __file__, results.experiment.uid, qbn, EXPERIMENT_ID)

        if AUTO:
            if fr is not None:
                print(f'Updated from {qubit_params[f"Q{qbn}"]["RO"]["freq"]:.5e} to {fr:.5e}')
                qubit_params[f"Q{qbn}"]["RO"]["freq"] = fr
                utils.update_qubit_params(qubit_params, qubit_param_f_path)
            else: print(f"{function_id} Fitting이 되지 않았습니다.")

        else:
            # Update qubit parameters
            if fr is not None:
                update = input("Enter T to save figure, results, and update parameter values: ") == "T"
            else: raise ValueError(f"{function_id} Fitting이 되지 않았습니다.")
            if update:
                print(f'Updated from {qubit_params[f"Q{qbn}"]["RO"]["freq"]:.5e} to {fr:.5e}')
                qubit_params[f"Q{qbn}"]["RO"]["freq"] = fr
                utils.update_qubit_params(qubit_params, qubit_param_f_path)
    return 

def qubit_spec(frequency_sweep, num_averages, reset_delay, readout_pulse, drive_pulse, integration_pulse):
    exp_qspec = Experiment(
        uid="qubit_spec",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )
    with exp_qspec.acquire_loop_rt(
        uid="shots",
        count=pow(2, num_averages),
        acquisition_type=AcquisitionType.SPECTROSCOPY,
    ):
        with exp_qspec.sweep(uid="qfreq_sweep", parameter=frequency_sweep):
            with exp_qspec.section(uid="qubit_excitation"):
                exp_qspec.play(signal="drive", pulse=drive_pulse)
            with exp_qspec.section(uid="readout", play_after="qubit_excitation"):
                exp_qspec.measure(
                        measure_signal="measure",
                        measure_pulse=readout_pulse,
                        acquire_signal="acquire",
                        integration_kernel=integration_pulse,
                        handle=exp_qspec.uid,
                        reset_delay=reset_delay,
                    )

    exp_calibration = Calibration()
    
    exp_calibration["drive"] = SignalCalibration(
        oscillator=Oscillator(
            uid="drive_osc",
            frequency=frequency_sweep,
            modulation_type=ModulationType.HARDWARE,
        ),
    )
    exp_qspec.set_calibration(exp_calibration)
    return exp_qspec

def run_03_qubit_spec(qubit_list, AUTO = True, EXPERIMENT_ID = "Test", pulse_show = False):
    # Load qubit tuneup parameters 
    qubit_params, qubit_param_f_path = utils.get_qubit_params(__file__)
    tuneup_parameters, _ = utils.get_tuneup_params(__file__)
    function_id = sys._getframe().f_code.co_name.replace("run_","")
    tuneup_params = tuneup_parameters[function_id]

    # Apply baseline calibration of devices
    baseline_calibration = calibrate_devices(qubit_list, qubit_params, "SPECTROSCOPY")

    # Create and connect to a session
    session = Session(device_setup=baseline_calibration)
    session.connect(do_emulation=emulation_mode)

    # Run for qubits in qubit_list
    for qbn in qubit_list:
        qubit = qubit_params[f"Q{qbn}"]
        device = qubit["DRV"]["device"]
        port = qubit["DRV"]["port"]
        qa = qubit_params["QA"][device]
        sg = qubit_params["SG"][device]
        lo_index = port//2

        start_freq = qubit["DRV"]["freq"] - sg["LO"][lo_index] - tuneup_params["Freq_span"]/2
        stop_freq = qubit["DRV"]["freq"]  - sg["LO"][lo_index] + tuneup_params["Freq_span"]/2

        frequency_sweep = LinearSweepParameter(uid="qubit_freq_sweep", 
                                            start=start_freq, 
                                            stop=stop_freq, 
                                            count=tuneup_params["Exp_pts"], 
                                            axis_name="Frequency (Hz)")

        readout_pulse = measure_pulses(tuneup_params["Measure_pulse"], qubit_params, qbn)

        drive_pulse = drive_pulses(tuneup_params["Drive_pulse"], qubit_params, qbn, uid = f"Q{qbn}_drive_pulse")
        
        if tuneup_params["Integration_pulse"] == "none":
            integration_pulse = readout_pulse
        else:
            integration_pulse = integration_pulses(tuneup_params["Integration_pulse"], qubit_params, qbn)
    
        # Create experiment
        exp_qspec = qubit_spec(frequency_sweep, tuneup_params["Num_avg"], qa["reset_delay_length"], readout_pulse, drive_pulse, integration_pulse)

        # Mapping
        lsg = baseline_calibration.logical_signal_groups[f"q{qbn}"]
        exp_qspec.map_signal("drive", lsg.logical_signals["drive_line"])
        exp_qspec.map_signal("measure", lsg.logical_signals["measure_line"])
        exp_qspec.map_signal("acquire", lsg.logical_signals["acquire_line"])
        
        # Compile and run
        compiled_exp = session.compile(exp_qspec)
        if pulse_show:
            show_pulse_sheet("pulse_show", compiled_exp)
        
        #plot_simulation(compiled_exp)
        results = session.run(compiled_exp, include_results_metadata=True)
        fig, fge = qubit_spec_fit_plot(results, qubit_params, qbn)
        
        utils.save_fig_qubit_params(results, fig, qubit_params, __file__, results.experiment.uid, qbn, EXPERIMENT_ID)

        if AUTO:
            if fge is not None:
                print(f'Updated from {qubit_params[f"Q{qbn}"]["DRV"]["freq"]:.5e} to {fge:.5e}')
                qubit_params[f"Q{qbn}"]["DRV"]["freq"] = fge
                utils.update_qubit_params(qubit_params, qubit_param_f_path)
            else: print(f"{function_id} Fitting이 되지 않았습니다.")

        else:
            # Update qubit parameters
            if fge is not None:
                update = input("Enter T to save figure, results, and update parameter values: ") == "T"
            else: raise ValueError(f"{function_id} Fitting이 되지 않았습니다.")
            if update:
                print(f'Updated from {qubit_params[f"Q{qbn}"]["DRV"]["freq"]:.5e} to {fge:.5e}')
                qubit_params[f"Q{qbn}"]["DRV"]["freq"] = fge
                utils.update_qubit_params(qubit_params, qubit_param_f_path)
    return

# Define experiment
def rabi_amp(amp_sweep, num_averages, reset_delay, readout_pulse, drive_pulse, integration_pulse, DRV_IF_freq):
    
    exp_rabi = Experiment(
        uid="rabi_amp",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    with exp_rabi.acquire_loop_rt(
        uid="shots",
        count=pow(2, num_averages),
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        with exp_rabi.sweep(uid="qamp_sweep", parameter=amp_sweep):
            with exp_rabi.section(uid="qubit_excitation"):
                exp_rabi.play(signal="drive", pulse=drive_pulse, amplitude=amp_sweep)
            with exp_rabi.section(uid="readout", play_after="qubit_excitation"):
                exp_rabi.measure(
                        measure_signal="measure",
                        measure_pulse=readout_pulse,
                        acquire_signal="acquire",
                        integration_kernel=integration_pulse,
                        handle=exp_rabi.uid,
                        reset_delay=reset_delay
                        )
                
    exp_calibration = Calibration()
    
    exp_calibration["drive"] = SignalCalibration(
        oscillator=Oscillator(
            uid="drive_osc",
            frequency=DRV_IF_freq, # JS edit, this needs to be intermediate frequency (DRV_freq - LO)
            modulation_type=ModulationType.HARDWARE
        )
    )
    
    return exp_rabi

def run_04_Rabi_amp(qubit_list, AUTO = True, EXPERIMENT_ID = "Test", pulse_show = False):
    # Load qubit tuneup parameters 
    qubit_params, qubit_param_f_path = utils.get_qubit_params(__file__)
    tuneup_parameters, _ = utils.get_tuneup_params(__file__)
    function_id = sys._getframe().f_code.co_name.replace("run_","")
    tuneup_params = tuneup_parameters[function_id]

    # Apply baseline calibration of devices
    baseline_calibration = calibrate_devices(qubit_list, qubit_params, "INTEGRATION")

    # Create and connect to a session
    session = Session(device_setup=baseline_calibration)
    session.connect(do_emulation=emulation_mode)

    # Run for qubits in qubit_list
    for qbn in qubit_list:
        qubit = qubit_params[f"Q{qbn}"]
        device = qubit["DRV"]["device"]
        port = qubit["DRV"]["port"]
        qa = qubit_params["QA"][device]
        sg = qubit_params["SG"][device]
        lo_index = port//2

        start_amp = 0.01
        stop_amp = tuneup_params["qubit_amp_multiplier"]*qubit["DRV"]["amp_pi"]

        if stop_amp > 1.0:
            stop_amp = 1.0
            print(f"\n>\n>\n> \033[0;34m !! Amplitude cannot exceed 1. Adjust Q{qbn} DRV range for higher power !!  \033[0;30m \n>\n>")
        
        rabi_amp_sweep = LinearSweepParameter(uid="rabi_amp_sweep", 
                                                start=start_amp, 
                                                stop=stop_amp, 
                                                count=tuneup_params["Exp_pts"], 
                                                axis_name="Amplitude")

        readout_pulse = measure_pulses(tuneup_params["Measure_pulse"], qubit_params, qbn)
        
        drive_pulse = drive_pulses(tuneup_params["Drive_pulse"], qubit_params, qbn)
        
        if tuneup_params["Integration_pulse"] == "none":
            integration_pulse = readout_pulse
        else:
            integration_pulse = integration_pulses(tuneup_params["Integration_pulse"], qubit_params, qbn)
                
        DRV_IF_freq = qubit["DRV"]["freq"] - sg["LO"][lo_index]

        # Create experiment
        exp_rabi = rabi_amp(rabi_amp_sweep, tuneup_params["Num_avg"], qa["reset_delay_length"], readout_pulse, drive_pulse , integration_pulse, DRV_IF_freq)   

        # Mapping
        lsg = baseline_calibration.logical_signal_groups[f"q{qbn}"]
        exp_rabi.map_signal("drive", lsg.logical_signals["drive_line"])
        exp_rabi.map_signal("measure", lsg.logical_signals["measure_line"])
        exp_rabi.map_signal("acquire", lsg.logical_signals["acquire_line"])
        
        # Compile and run
        compiled_exp = session.compile(exp_rabi)
        if pulse_show:
            show_pulse_sheet("pulse_show", compiled_exp)

        # plot_simulation(compiled_exp)
        results = session.run(compiled_exp, include_results_metadata=True)

        fig, pi_pulse, first_peak = rabi_amp_fit_plot(results, qubit_params, qbn)
        
        utils.save_fig_qubit_params(results, fig, qubit_params, __file__, results.experiment.uid, qbn, EXPERIMENT_ID)

        # Update qubit parameters
        if AUTO:
            if pi_pulse is not None:
                print(f'Drive amp_pi is updated from {qubit_params[f"Q{qbn}"]["DRV"]["amp_pi"]:.5e} to {pi_pulse:.5e}')
                print(f'Drive amp_half_pi is updated from {qubit_params[f"Q{qbn}"]["DRV"]["amp_half_pi"]:.5e} to {pi_pulse/2:.5e}')
                qubit_params[f"Q{qbn}"]["DRV"]["amp_pi"] = pi_pulse
                qubit_params[f"Q{qbn}"]["DRV"]["amp_half_pi"] = pi_pulse/2
                utils.update_qubit_params(qubit_params, qubit_param_f_path)
            else: print(f"{function_id} Fitting이 되지 않았습니다.")

        else:
            # Update qubit parameters
            if pi_pulse is not None:
                update = input("Enter T to save figure, results, and update parameter values: ") == "T"
            else: raise ValueError(f"{function_id} Fitting이 되지 않았습니다.")
            if update:
                print(f'Drive amp_pi is updated from {qubit_params[f"Q{qbn}"]["DRV"]["amp_pi"]:.5e} to {pi_pulse:.5e}')
                print(f'Drive amp_half_pi is updated from {qubit_params[f"Q{qbn}"]["DRV"]["amp_half_pi"]:.5e} to {pi_pulse/2:.5e}')
                qubit_params[f"Q{qbn}"]["DRV"]["amp_pi"] = pi_pulse
                qubit_params[f"Q{qbn}"]["DRV"]["amp_half_pi"] = pi_pulse/2
                utils.update_qubit_params(qubit_params, qubit_param_f_path)
    return 

#%%
def IQ_Blobs(num_averages, readout_pulse, x180, integration_pulse, handles, reset_delay):
    exp_IQ = Experiment(
        uid="IQ_Blobs",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    with exp_IQ.acquire_loop_rt(
        uid="shots",
        count=pow(2, num_averages),
        averaging_mode=AveragingMode.SINGLE_SHOT,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        for handle in handles:
            handle_int = int(handle.split('_')[-1])
            with exp_IQ.section(uid=handle):
                with exp_IQ.section(uid="drive"+handle):
                    for i in range(handle_int+1):
                        if x180[f"_{i}"] != None:
                            exp_IQ.play(signal="drive", pulse=x180[f"_{i}"])

                with exp_IQ.section(uid="readout"+handle, play_after="drive"+handle):
                    exp_IQ.measure(
                            measure_signal="measure",
                            measure_pulse=readout_pulse,
                            acquire_signal="acquire",
                            integration_kernel=integration_pulse,
                            handle=exp_IQ.uid+handle,
                            reset_delay = reset_delay[handle]
                    )
    return exp_IQ

def run_05_IQ_blobs(qubit_list, AUTO = True, EXPERIMENT_ID = "Test", pulse_show = False):
    # Load qubit tuneup parameters 
    qubit_params, qubit_param_f_path = utils.get_qubit_params(__file__)
    tuneup_parameters, _ = utils.get_tuneup_params(__file__)
    function_id = sys._getframe().f_code.co_name.replace("run_","")
    tuneup_params = tuneup_parameters[function_id]

    # Apply baseline calibration of devices
    baseline_calibration = calibrate_devices(qubit_list, qubit_params, "INTEGRATION")

    # Create and connect to a session
    session = Session(device_setup=baseline_calibration)
    session.connect(do_emulation=emulation_mode)

    # Create Experiment
    handles = ["_0", "_1"]
    handle_for_x180 = {"_0" : None,
                       "_1" : "ge",
                       "_2" : "ef"
                       }

    for qbn in qubit_list:
        qubit = qubit_params[f"Q{qbn}"]
        device = qubit["DRV"]["device"]
        port = qubit["DRV"]["port"]
        qa = qubit_params["QA"][device]
        sg = qubit_params["SG"][device]
        lo_index = port//2

        X180 = {}
        reset_delay = {}

        for handle in handles:
            X180[handle] = drive_pulses(tuneup_params["180_Drive_pulse"], qubit_params, qbn, handle = handle_for_x180[handle])
            reset_delay[handle] = qa["reset_delay_length"]

        readout_pulse = measure_pulses(tuneup_params["Measure_pulse"], qubit_params, qbn)

        if tuneup_params["Integration_pulse"] == "none":
            integration_pulse = readout_pulse
        else:
            integration_pulse = integration_pulses(tuneup_params["Integration_pulse"], qubit_params, qbn)


        exp_IQ = IQ_Blobs(tuneup_params["Num_avg"], readout_pulse, X180, integration_pulse, handles, reset_delay)

        # Mapping
        lsg = baseline_calibration.logical_signal_groups[f"q{qbn}"]
        exp_IQ.map_signal("drive", lsg.logical_signals["drive_line"])
        exp_IQ.map_signal("measure", lsg.logical_signals["measure_line"])
        exp_IQ.map_signal("acquire", lsg.logical_signals["acquire_line"])
        
        # Compile and run
        compiled_exp = session.compile(exp_IQ)
        if pulse_show:
            show_pulse_sheet("pulse_show", compiled_exp)
        # plot_simulation(compiled_exp)

        results = session.run(compiled_exp, include_results_metadata=True)
        fig, threshold, fidelity = IQ_fit_plot(results, handles, qbn)
        
        utils.save_results_fig_qubit_params(results, fig, qubit_params, __file__, results.experiment.uid, qbn, EXPERIMENT_ID)

        # Update qubit parameters
        # update = input("Enter T to save figure and update parameter values: ") == "T"
        # if update:
        #     utils.save_results(results, __file__, results.experiment.uid, qbn)
        #     utils.save_fig(fig, __file__, results.experiment.uid, qbn)
        print(f'ACQ threshold amp_pi is updated from {qubit_params[f"Q{qbn}"]["ACQ"]["threshold"]:.5e} to {threshold:.5e}')
        #     print(f'fidelity is updated from {qubit_params[f"Q{qbn}"]["metadata"]["fidelity"]:.5e} to {fidelity:.5e}')
            
        #     qubit_params[f"Q{qbn}"]["ACQ"]["threshold"] = threshold
        #     qubit_params[f"Q{qbn}"]["metadata"]["fidelity"] = fidelity
        #     utils.update_params(qubit_params, param_f_path)

    return 

#%%
