from laboneq.simple import *
import utils

muting_mode = True

def calibrate_devices(measure_type = "spec_square"):
    assert utils.validate_device_existence(), "Device existence validation failed. Please check device configuration."

    # Device Setup
    device_qubit_configs = utils.get_device_qubit_config()
    qubit_params = utils.get_qubit_params()
    device_setup = DeviceSetup()
    device_setup.add_dataserver(**device_qubit_configs["data_server"])


    # 장비들 모두 추가
    for dev_cfg in device_qubit_configs["device"]:
        if "shfqc" in dev_cfg:
            device_setup.add_instruments(
                SHFQC(
                    **device_qubit_configs["device"][dev_cfg]
                )
            )
        elif "hdawg" in dev_cfg:
            device_setup.add_instruments(
                HDAWG(
                    **device_qubit_configs["device"][dev_cfg]
                )
            )
        elif "pqsc" in dev_cfg:
            device_setup.add_instruments(
                PQSC(
                    **device_qubit_configs["device"][dev_cfg]
                )
            )
    
    #Physical connection 설정
    for qubit in device_qubit_configs["qubit"]:
        #xy, measure, acquire 연결
        for drive in device_qubit_configs["qubit"][qubit]:
            device_setup.add_connections(device_qubit_configs["qubit"][qubit][drive]["device"], create_connection(to_signal=f"{qubit}/{drive}_line", ports=device_qubit_configs["qubit"][qubit][drive]["port"]))
    
    #logical signal, baseline calibration 설정
    for qubit in device_qubit_configs["qubit"]:
        #measure 방식 : INTEGRATION / SPECTROSCOPY
        acquisition_type = qubit_params["measures"][measure_type]["acquire_type"]

        # logical signal group 설정
        lsg = device_setup.logical_signal_groups[qubit]

        #Local oscillator 및 신호 주파수 설정
        qubit_info = qubit_params[qubit]
        measure_device = device_qubit_configs["qubit"][qubit]["measure"]["device"]
        measure_lo_freq = qubit_params[measure_device]["qa_channel"]["local_oscillator_frequency"]
        drive_device = device_qubit_configs["qubit"][qubit]["drive"]["device"]
        drive_port = utils.port_to_int(device_qubit_configs["qubit"][qubit]["drive"]["port"])
        drive_lo_freq = qubit_params[drive_device]["sg_channel"]["local_oscillator_frequency"][drive_port//2]
        flux_device = device_qubit_configs["qubit"][qubit]["flux"]["device"]
        ge_drive_freq = qubit_info["parameters"]["freq"] - drive_lo_freq
        ef_drive_freq = qubit_info["parameters"]["freq_ef"] - drive_lo_freq
        measure_freq = qubit_info["measure"][measure_type]["freq"] - measure_lo_freq

        measure_lo_osc = Oscillator(f"{measure_device}_qa_lo_osc", frequency=measure_lo_freq)
        drive_lo_osc = Oscillator(f"{drive_device}_sg_lo_osc_{drive_port//2}", frequency=drive_lo_freq)
        

        if acquisition_type == "INTEGRATION":
            if qubit_info["operations"]["acquire"]["integration_type"] == "parametric":
                measure_osc = Oscillator(f"{qubit}_measure_osc", frequency = measure_freq, modulation_type=ModulationType.SOFTWARE)
                acquire_osc = Oscillator(f"{qubit}_acquire_osc", frequency = measure_freq, modulation_type=ModulationType.SOFTWARE)
                lsg.logical_signals["measure_line"].calibration = SignalCalibration(
                    local_oscillator=measure_lo_osc,
                    oscillator=measure_osc,
                    range = qubit_params[measure_device]["qa_channel"]["range_out_integration"],
                    automute=muting_mode,
                )
                lsg.logical_signals["acquire_line"].calibration = SignalCalibration(
                    local_oscillator=measure_lo_osc,
                    oscillator=acquire_osc,
                    range = qubit_params[measure_device]["qa_channel"]["range_in_integration"],
                    port_delay=qubit_info["measures"][measure_type]["port_delay"],
                    
                    threshold = 
                )
            elif qubit_info["operations"]["acquire"]["integration_type"] == "waveform":
                #추후 작성
                print("아직 작성 안됨")
                assert False
        ## 여러개 qubit spec할때  hardware modulation 동시에 되는지 확인 필요?
        elif acquisition_type == "SPECTROSCOPY":
            measure_osc = Oscillator(f"{qubit}_measure_osc", frequency = measure_freq, modulation_type=ModulationType.HARDWARE)
            acquire_osc = Oscillator(f"{qubit}_acquire_osc", frequency = measure_freq, modulation_type=ModulationType.HARDWARE)
            lsg.logical_signals["measure_line"].calibration = SignalCalibration(
                local_oscillator=measure_lo_osc,
                oscillator=measure_osc,
                range = qubit_params[measure_device]["qa_channel"]["range_out_spectroscopy"],
                automute=muting_mode,
            )
            lsg.logical_signals["acquire_line"].calibration = SignalCalibration(
                local_oscillator=measure_lo_osc,
                oscillator=acquire_osc,
                range = qubit_params[measure_device]["qa_channel"]["range_in_spectroscopy"],
                port_delay=qubit_info["measures"][measure_type]["port_delay"]
            )

        # drive 신호 설정 (ge, ef) 
        # higher level drive 신호 추가되면 여기에 추가
        ge_osc = Oscillator(f"{qubit}_ge_drive_osc", frequency=ge_drive_freq, modulation_type=ModulationType.HARDWARE)
        lsg.logical_signals["drive_line"].calibration = SignalCalibration(
            oscillator=ge_osc,
            local_oscillator=drive_lo_osc,
            range=qubit_params[drive_device]["sg_channel"]["range_out"][drive_port]
        )

        ef_osc = Oscillator(f"{qubit}_ef_drive_osc", frequency=ef_drive_freq, modulation_type=ModulationType.HARDWARE)
        lsg.logical_signals["ef_drive_line"].calibration = SignalCalibration(
            oscillator=ef_osc,
            local_oscillator=drive_lo_osc,
            range=qubit_params[drive_device]["sg_channel"]["range_out"][drive_port]
        )
        ##나중에 flux도 추가하기
            
    return device_setup