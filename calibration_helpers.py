from laboneq.simple import *

muting_mode = False     # Choose btw. muting output on/off
# 4.408 qubit
# 7.148

device_configs = [
    {"uid": "shfqc_0", "address": "DEV12079", "interface" : "USB"},
    # {"uid": "shfqc_1", "address": "DEV12080", "interface" : "USB"}, 
    # {"uid": "hdawg", "address": "DEV12080", "interface" : "USB"},
] #interface = "USB" or "1GbE"

def calibrate_devices(qubit_list, qubit_params, type="INTEGRATION"):
    # Device Setup
    device_setup = DeviceSetup()
    device_setup.add_dataserver(host="localhost", port="8004")

    for dev_cfg in device_configs:
        device_setup.add_instruments(
            SHFQC(
                uid=dev_cfg["uid"], 
                address=dev_cfg["address"],
                interface = dev_cfg["interface"],
                device_options="SHFQC/PLUS/QC6CH"
            )
        )

    '''
    device_setup.add_instruments(SHFQC(uid="device_shfqc",
    address="DEV12079", 
    interface="USB", 
    device_options="SHFQC/PLUS/QC6CH")) #interface = "USB" or "1GbE"
    '''
    
    for qbn in qubit_list:
        #xy, measure, acquire 연결
        device_setup.add_connections(qubit_params[f"Q{qbn}"]["DRV"]["device"],
                                        create_connection(to_signal=f"q{qbn}/measure_line", ports="QACHANNELS/0/OUTPUT"),
                                        create_connection(to_signal=f"q{qbn}/acquire_line", ports="QACHANNELS/0/INPUT"),
                                        create_connection(to_signal=f"q{qbn}/drive_line", ports=f"SGCHANNELS/{qubit_params[f"Q{qbn}"]["DRV"]["port"]}/OUTPUT",),
                                        create_connection(to_signal=f"q{qbn}/drive_line_ef", ports=f"SGCHANNELS/{qubit_params[f"Q{qbn}"]["DRV"]["port"]}/OUTPUT",),)
        
        #z line 연결
        if any(dev["uid"] == "hdawg" for dev in device_configs):
            device_setup.add_connections(qubit_params[f"Q{qbn}"]["FDRV"]["device"],
                                        create_connection(to_signal=f"q{qbn}/flux_line", ports=f"SIGOUTS/{qubit_params[f"Q{qbn}"]["FDRV"]["port"]}"))
        

    for qbn in qubit_list:
        device = qubit_params[f"Q{qbn}"]["DRV"]["device"]
        xyport = qubit_params[f"Q{qbn}"]["DRV"]["port"]

        qa = qubit_params["QA"][device]
        qubit = qubit_params[f"Q{qbn}"]

        lsg = device_setup.logical_signal_groups[f"q{qbn}"]

        qa_lo = Oscillator(device+"shfqa_lo", frequency=qa["LO"])

        if type == "SPECTROSCOPY":
            ro_osc = Oscillator(device+"measure_osc", frequency=qubit["RO"]["freq"]-qa["LO"], modulation_type=ModulationType.HARDWARE)
        elif type == "INTEGRATION":
            ro_osc = Oscillator(device+"measure_osc", frequency=qubit["RO"]["freq"]-qa["LO"], modulation_type=ModulationType.SOFTWARE)

        lsg.logical_signals["measure_line"].calibration = SignalCalibration(
            local_oscillator=qa_lo, oscillator=ro_osc, range=qa["range_out"], automute=muting_mode,
        )
        lsg.logical_signals["acquire_line"].calibration = SignalCalibration(
            local_oscillator=qa_lo, oscillator=ro_osc, range=qa["range_in"], port_delay=qa["port_delay"],
        )

        lo_index = xyport//2
        sg_lo_freq = qubit_params["SG"][device]["LO"][lo_index]

        sg_lo = Oscillator(device+f"shfsg_lo_{lo_index}", frequency=sg_lo_freq)

        lsg.logical_signals["drive_line"].calibration = SignalCalibration(
            oscillator=Oscillator(device+f"drive_osc_{qbn}",
                frequency=qubit["DRV"]["freq"]-sg_lo_freq,
                modulation_type=ModulationType.HARDWARE,
            ),
            local_oscillator=sg_lo,
            range=qubit["DRV"]["range_out"],
            automute=muting_mode,
        )
        if any(dev["uid"] == "hdawg" for dev in device_configs):
            lsg.logical_signals["flux_line"].calibration = SignalCalibration(
                range=qubit["FDRV"]["range_out"], # 예: 0.8 (Volts)
                voltage_offset=qubit["FDRV"]["offset"], # 예: Sweet spot 바이어스 전압
                port_delay=qubit["FDRV"]["port_delay"] # 라인 간 딜레이 보정
            )
            
    return device_setup