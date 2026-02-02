from laboneq.simple import *
from . import utils_ttq as utils
from laboneq_applications.qpu_types.tunable_transmon import TunableTransmonQubit, TunableTransmonOperations
muting_mode = False

def calibrate_devices_ttq(
        qubit_params : dict | None = None, 
        device_qubit_configs : dict | None = None, 
        qubit_list : list | None = None,
        measure_type : str = "INTEGRATION"):
    # Device Setup
    if device_qubit_configs == None:
        device_qubit_configs = utils.get_device_qubit_config()
    if qubit_params ==None:
        qubit_params = utils.get_params()
    if qubit_list == None:
        qubit_list = device_qubit_configs["qubits"].keys()
    else:
        assert list(qubit_list - device_qubit_configs["qubits"].keys()) == []
    
    assert utils.validate_device_existence(device_qubit_configs), "Device existence validation failed. Please check device configuration."

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
    qubits = TunableTransmonQubit.from_device_setup(device_setup)
    for i, qubit in enumerate(qubits):
        qubit_uid = qubit.uid
        qubit_params_to_replace = qubit_params[qubit_uid]
        qubit.parameters = qubit.parameters.replace(**qubit_params_to_replace)

        qubit.parameters.user_defined["drive_device"] = device_qubit_configs["qubits"][qubit_uid]["drive"]["device"]
        qubit.parameters.user_defined["drive_port"] = utils.port_to_int(device_qubit_configs["qubits"][qubit_uid]["drive"]["port"])
        qubit.parameters.user_defined["measure_device"] = device_qubit_configs["qubits"][qubit_uid]["measure"]["device"]
        if "flux" in qubit.signals:
            qubit.parameters.user_defined["flux_device"] = device_qubit_configs["qubits"][qubit_uid]["flux"]["device"]
            qubit.parameters.user_defined["flux_port"] = utils.port_to_int(device_qubit_configs["qubits"][qubit_uid]["flux"]["port"])
            qubit.parameters.user_defined["flux_range"] = qubit_params[qubit.parameters.user_defined["flux_device"]]["flux_range"][qubit.parameters.user_defined["flux_port"]]

        qubit.parameters.drive_lo_frequency = qubit_params[qubit.parameters.user_defined["drive_device"]]["sg_channel"]["drive_lo_frequency"][qubit.parameters.user_defined["drive_port"]//2]
        qubit.parameters.readout_lo_frequency = qubit_params[qubit.parameters.user_defined["measure_device"]]["qa_channel"]["readout_lo_frequency"]
        qubit.parameters.readout_range_out = qubit_params[qubit.parameters.user_defined["measure_device"]]["qa_channel"][f"readout_range_out_{measure_type}"]
        qubit.parameters.readout_range_in = qubit_params[qubit.parameters.user_defined["measure_device"]]["qa_channel"][f"readout_range_in_{measure_type}"]
        qubit.parameters.drive_range = qubit_params[qubit.parameters.user_defined["drive_device"]]["sg_channel"]["drive_range"][qubit.parameters.user_defined["drive_port"]]

        device_setup.qubits[qubit_uid] = qubit
        device_setup.set_calibration(qubit.calibration())

    qpu = QPU(quantum_elements=qubits, quantum_operations=TunableTransmonOperations())
    qt_platform = QuantumPlatform(setup=device_setup, qpu=qpu)

    return qt_platform