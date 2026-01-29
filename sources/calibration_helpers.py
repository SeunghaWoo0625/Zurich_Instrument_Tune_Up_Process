from laboneq.simple import *
import sources.utils as utils
from sources.QDLTransmon_def import *
from laboneq.dsl.quantum import QuantumPlatform

muting_mode = False

def calibrate_devices(
        qubit_params : dict | None = None, 
        device_qubit_configs : dict | None = None, 
        qubit_list : list | None = None,
        measure_type : str = "SPECTROSCOPY"):
    
    assert utils.validate_device_existence(device_qubit_configs), "Device existence validation failed. Please check device configuration."

    # Device Setup
    if device_qubit_configs == None:
        device_qubit_configs = utils.get_device_qubit_config()
    if qubit_params ==None:
        qubit_params = utils.get_qubit_params()
    if qubit_list == None:
        qubit_list = device_qubit_configs["qubits"].keys()
    else:
        assert list(qubit_list - device_qubit_configs["qubits"].keys()) == []
    device_setup = DeviceSetup()
    device_setup.add_dataserver(**device_qubit_configs["data_server"])


    # 장비들 모두 추가
    for dev_cfg in device_qubit_configs["devices"]:
        if "shfqc" in dev_cfg:
            device_setup.add_instruments(
                SHFQC(
                    **device_qubit_configs["devices"][dev_cfg]
                )
            )
        elif "hdawg" in dev_cfg:
            device_setup.add_instruments(
                HDAWG(
                    **device_qubit_configs["devices"][dev_cfg]
                )
            )
        elif "pqsc" in dev_cfg:
            device_setup.add_instruments(
                PQSC(
                    **device_qubit_configs["devices"][dev_cfg]
                )
            )
    
    #Physical connection 설정
    for qubit in qubit_list:
        #xy, measure, acquire 연결
        for drive in device_qubit_configs["qubits"][qubit]:
            device_setup.add_connections(device_qubit_configs["qubits"][qubit][drive]["device"], create_connection(to_signal=f"{qubit}/{drive}", ports=device_qubit_configs["qubits"][qubit][drive]["port"]))

    # device setup 바탕으로 quantum elements 생성
    qubits = QDLTransmon.from_device_setup(device_setup)
    for i, qubit in enumerate(qubits):
        qubit_uid = qubit.uid
        qubit_params_to_replace = qubit_params[qubit_uid]
        qubit.parameters = qubit.parameters.replace(**qubit_params_to_replace)

        qubit.parameters.drive_device = device_qubit_configs["qubits"][qubit_uid]["drive"]["device"]
        qubit.parameters.drive_port = utils.port_to_int(device_qubit_configs["qubits"][qubit_uid]["drive"]["port"])
        qubit.parameters.measure_device = device_qubit_configs["qubits"][qubit_uid]["measure"]["device"]
        if "flux" in qubit.signals:
            qubit.parameters.flux_device = device_qubit_configs["qubits"][qubit_uid]["flux"]["device"]
            qubit.parameters.flux_port = utils.port_to_int(device_qubit_configs["qubits"][qubit_uid]["flux"]["port"])
            qubit.parameters.flux_range = qubit_params[qubit.parameters.flux_device]["flux_range"][qubit.parameters.flux_port]

        qubit.parameters.drive_lo_frequency = qubit_params[qubit.parameters.drive_device]["sg_channel"]["drive_lo_frequency"][qubit.parameters.drive_port//2]
        qubit.parameters.readout_lo_frequency = qubit_params[qubit.parameters.measure_device]["qa_channel"]["readout_lo_frequency"]
        qubit.parameters.readout_range_out = qubit_params[qubit.parameters.measure_device]["qa_channel"][f"readout_range_out_{measure_type}"]
        qubit.parameters.readout_range_in = qubit_params[qubit.parameters.measure_device]["qa_channel"][f"readout_range_in_{measure_type}"]
        qubit.parameters.drive_range = qubit_params[qubit.parameters.drive_device]["sg_channel"]["drive_range"][qubit.parameters.drive_port]

        device_setup.qubits[qubit_uid] = qubit
        device_setup.set_calibration(qubit.calibration())

    qpu = QPU(quantum_elements=qubits, quantum_operations=QDLTransmonOperations())
    qt_platform = QuantumPlatform(setup=device_setup, qpu=qpu)

    return qt_platform

    # TunableTransmonParameters 중에서 직접 추가할 내용들
    # "drive_lo_frequency": "None",
    # "readout_lo_frequency": "None",
    # "readout_range_out": 5,
    # "readout_range_in": 10,
    # "drive_range": 10,
    # "flux_range": 5,

    #==========================
    # 기존에 하던 직접 추가하는 방식
    # #logical signal, baseline calibration 설정
    # for qubit in qubit_list:

    #     # logical signal group 설정
    #     lsg = device_setup.logical_signal_groups[qubit]

    #     #Local oscillator 및 신호 주파수 설정
    #     qubit_info = qubit_params[qubit]
    #     measure_device = device_qubit_configs["qubits"][qubit]["measure"]["device"]
    #     measure_lo_freq = qubit_params[measure_device]["qa_channel"]["readout_lo_frequency"]
    #     drive_device = device_qubit_configs["qubits"][qubit]["drive"]["device"]
    #     drive_port = utils.port_to_int(device_qubit_configs["qubits"][qubit]["drive"]["port"])
    #     drive_lo_freq = qubit_params[drive_device]["sg_channel"]["drive_lo_frequency"][drive_port//2]
    #     # flux_device = device_qubit_configs["qubit"][qubit]["flux"]["device"]
    #     ge_drive_freq = qubit_info["information"]["resonance_frequency_ge"] - drive_lo_freq
    #     ef_drive_freq = qubit_info["information"]["resonance_frequency_ef"] - drive_lo_freq
    #     measure_freq = qubit_info["measures"][measure_type]["readout_resonator_frequency"] - measure_lo_freq

    #     measure_lo_osc = Oscillator(f"{measure_device}_qa_lo_osc", frequency=measure_lo_freq)
    #     drive_lo_osc = Oscillator(f"{drive_device}_sg_lo_osc_{drive_port//2}", frequency=drive_lo_freq)
        
    #     #measure 방식 : INTEGRATION / SPECTROSCOPY
    #     acquisition_type = qubit_info["measures"][measure_type]["acquire_type"]

    #     if acquisition_type == "INTEGRATION":
    #         if qubit_info["measures"][measure_type]["type"] == "parametric":
    #             measure_osc = Oscillator(f"{qubit}_measure_osc", frequency = measure_freq, modulation_type=ModulationType.SOFTWARE)
    #             acquire_osc = Oscillator(f"{qubit}_acquire_osc", frequency = measure_freq, modulation_type=ModulationType.SOFTWARE)
    #             lsg.logical_signals["measure_line"].calibration = SignalCalibration(
    #                 local_oscillator=measure_lo_osc,
    #                 oscillator=measure_osc,
    #                 port_delay=0,
    #                 range = qubit_params[measure_device]["qa_channel"]["readout_range_out_INTEGRATION"],
    #                 automute=muting_mode,
    #             )
    #             lsg.logical_signals["acquire_line"].calibration = SignalCalibration(
    #                 local_oscillator=measure_lo_osc,
    #                 oscillator=acquire_osc,
    #                 range = qubit_params[measure_device]["qa_channel"]["readout_range_in_INTEGRATION"],
    #                 port_delay=qubit_info["measures"][measure_type]["reset_delay_length"],
    #                 threshold =qubit_info["measures"][measure_type]["threshold"]
    #             )
    #         elif qubit_info["measures"][measure_type]["type"] == "waveform":
    #             #추후 작성
    #             print("아직 작성 안됨")
    #             assert False
    #     ## 여러개 qubit spec할때  hardware modulation 동시에 되는지 확인 필요?
    #     elif acquisition_type == "SPECTROSCOPY":
    #         measure_osc = Oscillator(f"{qubit}_measure_osc", frequency = measure_freq, modulation_type=ModulationType.HARDWARE)
    #         acquire_osc = Oscillator(f"{qubit}_acquire_osc", frequency = measure_freq, modulation_type=ModulationType.HARDWARE)
    #         lsg.logical_signals["measure_line"].calibration = SignalCalibration(
    #             local_oscillator=measure_lo_osc,
    #             oscillator=measure_osc,
    #             range = qubit_params[measure_device]["qa_channel"]["readout_range_out_SPECTROSCOPY"],
    #             automute=muting_mode,
    #         )
    #         lsg.logical_signals["acquire_line"].calibration = SignalCalibration(
    #             local_oscillator=measure_lo_osc,
    #             oscillator=acquire_osc,
    #             range = qubit_params[measure_device]["qa_channel"]["readout_range_in_SPECTROSCOPY"],
    #             port_delay=qubit_info["measures"][measure_type]["reset_delay_length"],
    #             threshold =qubit_info["measures"][measure_type]["threshold"]

    #         )

    #     # drive 신호 설정 (ge, ef) 
    #     # higher level drive 신호 추가되면 여기에 추가
    #     ge_osc = Oscillator(f"{qubit}_ge_drive_osc", frequency=ge_drive_freq, modulation_type=ModulationType.HARDWARE)
    #     lsg.logical_signals["drive_line"].calibration = SignalCalibration(
    #         oscillator=ge_osc,
    #         local_oscillator=drive_lo_osc,
    #         range=qubit_params[drive_device]["sg_channel"]["drive_range"][drive_port]
    #     )

    #     ef_osc = Oscillator(f"{qubit}_drive_ef_osc", frequency=ef_drive_freq, modulation_type=ModulationType.HARDWARE)
    #     lsg.logical_signals["drive_ef_line"].calibration = SignalCalibration(
    #         oscillator=ef_osc,
    #         local_oscillator=drive_lo_osc
    #     )

    #     #나중에 flux도 calibration해야되면 하기        
            