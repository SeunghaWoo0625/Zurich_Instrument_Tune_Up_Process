import os
import json
from datetime import datetime 
from laboneq.simple import *
import shutil

abs_path = os.path.dirname(os.path.abspath(__file__))
DEVICE_QUBIT_CONFIG_FILE = abs_path + "/jsons/device_qubit_config.json"
QUBIT_PARAMETERS_FILE = abs_path + "/jsons/qubit_device_parameters.json"
TUNEUP_PARAMETERS_FILE = abs_path + "/jsons/tuneup_parameters.json"
PULSES_FILE = abs_path + "/pulses"

def get_device_qubit_config():
    with open(DEVICE_QUBIT_CONFIG_FILE) as f:
        device_qubit_config = json.load(f)
    return device_qubit_config

def get_qubit_params():
    with open(QUBIT_PARAMETERS_FILE) as f:
        qubit_params = json.load(f)
    return qubit_params

def update_qubit_params(qubit_params):
    with open(QUBIT_PARAMETERS_FILE, 'w') as f:
        json.dump(qubit_params, f, indent=2)
    return None

def get_tuneup_params():
    with open(TUNEUP_PARAMETERS_FILE) as f:
        tuneup_params = json.load(f)
    return tuneup_params

def update_tuneup_params(tuneup_params):
    with open(TUNEUP_PARAMETERS_FILE, 'w') as f:
        json.dump(tuneup_params, f, indent=2)
    return None

def port_to_int(port_str):
    # "SGCHANNELS/0/OUTPUT" -> 0
    port_int = int(port_str.split("/")[1])
    return port_int

def device_port_dictionary():
    device_qubit_config = get_device_qubit_config()
    qubit_config = device_qubit_config["qubits"]
    device_usage_map = {}

    # 1. 큐비트 반복 (d1, d2, ...)
    for qubit_name, signals in qubit_config.items():
        # 2. 신호 반복 (drive, measure, acquire, ...)
        for signal_type, connection in signals.items():
            
            device_uid = connection.get("device")
            port_str = connection.get("port")

            if device_uid and port_str:
                # utils.port_to_int 사용하여 포트 번호 추출
                port_num = port_to_int(port_str)

                # 딕셔너리에 해당 디바이스 키가 없으면 생성 (Set을 사용하여 포트 중복 방지)
                if device_uid not in device_usage_map:
                    device_usage_map[device_uid] = set()
                
                # 포트 번호 추가
                device_usage_map[device_uid].add(port_num)

    # 3. Set을 다시 정렬된 List로 변환 (보기 좋게 만들기 위함)
    final_usage_map = {
        dev: sorted(list(ports)) 
        for dev, ports in device_usage_map.items()
    }

    return final_usage_map

def validate_device_existence(device_qubit_configs=None):
    if device_qubit_configs == None:
        device_qubit_configs = get_device_qubit_config()

    device_config = device_qubit_configs["devices"]
    usage_map = device_port_dictionary()

    # 실제 정의된 장비 UID 목록 (shfqc_0 등)
    defined_devices = set(device_config.keys())
    
    # 큐비트 연결에 사용된 장비 UID 목록
    used_devices = set(usage_map.keys())

    # 차집합 연산: 사용되었으나 정의되지 않은 장비 찾기
    missing_devices = list(used_devices - defined_devices)

    return missing_devices==[]

def save_fig_qubit_params(results, figure, exp_name, qbn, experiment_id):
    #실험 result, figure, qubit_params를 한꺼번에 저장하는 함수
    # 현재 스크립트의 위치를 기준으로 경로 설정

    now = datetime.now()
    datestr = now.strftime("%Y-%m-%d")
    timestr = now.strftime("%H%M%S") # 가독성을 위해 언더바(_)는 파일명 조합 때 넣습니다.

    # 폴더 구조: .../EXPERIMENT_ID/exp_name_날짜/
    # 예: .../Exp001/ResSpec_2023-10-27/
    folder_name = f"{exp_name}_{datestr}"
    save_dir = os.path.join(abs_path, "experiment_results", str(experiment_id), folder_name)
    
    # 폴더 생성
    os.makedirs(save_dir, exist_ok=True)

    # 파일 이름: Q{qbn}_{timestr}.png
    # 예: Q1_143005.png
    fig_file_full_name = f"{qbn}_{timestr}.png"
    # 저장
    figure.savefig(os.path.join(save_dir, fig_file_full_name))
    print(f"Figure saved to: {os.path.join(save_dir, fig_file_full_name)}")

    # results_file_full_name = f"Q{qbn}_{timestr}_results.json"
    # 저장
    # results.save_signal_map(os.path.join(save_dir, results_file_full_name))
    # print(f"Results saved to: {os.path.join(save_dir, results_file_full_name)}")

    qubit_parameters_file_full_name = os.path.join(save_dir, f"{qbn}_{timestr}_qubit_parameters.json")
    tuneup_parameters_file_full_name = os.path.join(save_dir, f"{qbn}_{timestr}_tuneup_parameters.json")

    shutil.copy2(QUBIT_PARAMETERS_FILE, qubit_parameters_file_full_name)
    shutil.copy2(TUNEUP_PARAMETERS_FILE, tuneup_parameters_file_full_name)
    



# def save_fig(figure, file_name, exp_name, qbn, experiment_id):
#     # 현재 스크립트의 위치를 기준으로 경로 설정
#     base_path = os.path.dirname(os.path.abspath(file_name))

#     now = datetime.now()
#     datestr = now.strftime("%Y-%m-%d")
#     timestr = now.strftime("%H%M%S") # 가독성을 위해 언더바(_)는 파일명 조합 때 넣습니다.

#     # 폴더 구조: .../EXPERIMENT_ID/exp_name_날짜/
#     # 예: .../Exp001/ResSpec_2023-10-27/
#     folder_name = f"{exp_name}_{datestr}"
#     save_dir = os.path.join(base_path, str(experiment_id), folder_name)
    
#     # 폴더 생성
#     os.makedirs(save_dir, exist_ok=True)

#     # 파일 이름: Q{qbn}_{timestr}.png
#     # 예: Q1_143005.png
#     file_full_name = f"Q{qbn}_{timestr}.png"
    
#     # 저장
#     figure.savefig(os.path.join(save_dir, file_full_name))
#     print(f"Figure saved to: {os.path.join(save_dir, file_full_name)}")


# def save_results(results, file_name, exp_name, qbn, experiment_id):
#     # 현재 스크립트의 위치를 기준으로 경로 설정
#     base_path = os.path.dirname(os.path.abspath(file_name))

#     now = datetime.now()
#     datestr = now.strftime("%Y-%m-%d")
#     timestr = now.strftime("%H%M%S")

#     # 폴더 구조: .../EXPERIMENT_ID/exp_name_날짜/
#     folder_name = f"{exp_name}_{datestr}"
#     save_dir = os.path.join(base_path, str(experiment_id), folder_name)
    
#     # 폴더 생성
#     os.makedirs(save_dir, exist_ok=True)

#     # 파일 이름: Q{qbn}_{timestr}_results.json
#     # 예: Q1_143005_results.json
#     file_full_name = f"Q{qbn}_{timestr}_results.json"
    
#     # 저장
#     results.save(os.path.join(save_dir, file_full_name))
#     print(f"Results saved to: {os.path.join(save_dir, file_full_name)}")