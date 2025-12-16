import os
import json
from datetime import datetime 
from laboneq.simple import *

global abs_path

QUBIT_CONFIG_FILE = "/qubit_parameters.json"
TUNEUP_CONFIG_FILE = "/tuneup_parameters.json"

def get_qubit_params(file_name):
    path = os.path.dirname(os.path.abspath(file_name))
    qubit_param_f_path = path+QUBIT_CONFIG_FILE
    with open(qubit_param_f_path) as f:
        qubit_params = json.load(f)
    return qubit_params, qubit_param_f_path

def update_qubit_params(qubit_params, qubit_param_f_path):
    with open(qubit_param_f_path, 'w') as f:
        json.dump(qubit_params, f, indent=2)
    return None

def get_tuneup_params(file_name):
    path = os.path.dirname(os.path.abspath(file_name))
    tuneup_param_f_path = path+TUNEUP_CONFIG_FILE
    with open(tuneup_param_f_path) as f:
        tuneup_params = json.load(f)
    return tuneup_params, tuneup_param_f_path

def update_tuneup_params(tuneup_params, tuneup_param_f_path):
    with open(tuneup_param_f_path, 'w') as f:
        json.dump(tuneup_params, f, indent=2)
    return None

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

def save_fig_qubit_params(results, figure, qubit_params, file_name, exp_name, qbn, experiment_id):
        # 현재 스크립트의 위치를 기준으로 경로 설정
    base_path = os.path.dirname(os.path.abspath(file_name))

    now = datetime.now()
    datestr = now.strftime("%Y-%m-%d")
    timestr = now.strftime("%H%M%S") # 가독성을 위해 언더바(_)는 파일명 조합 때 넣습니다.

    # 폴더 구조: .../EXPERIMENT_ID/exp_name_날짜/
    # 예: .../Exp001/ResSpec_2023-10-27/
    folder_name = f"{exp_name}_{datestr}"
    save_dir = os.path.join(base_path, str(experiment_id), folder_name)
    
    # 폴더 생성
    os.makedirs(save_dir, exist_ok=True)

    # 파일 이름: Q{qbn}_{timestr}.png
    # 예: Q1_143005.png
    fig_file_full_name = f"Q{qbn}_{timestr}.png"
    # 저장
    figure.savefig(os.path.join(save_dir, fig_file_full_name))
    print(f"Figure saved to: {os.path.join(save_dir, fig_file_full_name)}")

    # results_file_full_name = f"Q{qbn}_{timestr}_results.json"
    # 저장
    # results.save_signal_map(os.path.join(save_dir, results_file_full_name))
    # print(f"Results saved to: {os.path.join(save_dir, results_file_full_name)}")

    qubit_parameters_file_full_name = f"Q{qbn}_{timestr}_qubit_parameters.json"
    # 저장
    with open(os.path.join(save_dir, qubit_parameters_file_full_name), 'w') as f:
        json.dump(qubit_params, f, indent=2)
    return None
