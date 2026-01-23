#%%
import utils
from laboneq.simple import *

print(utils.validate_device_existence())
from sources.calibration_helpers import calibrate_devices

device_setup = calibrate_devices(measure_type = "spec_square")
session = Session(device_setup=device_setup)
session.connect()

#%%
test_exp = Experiment(
    uid="test_exp",
    signals=[

    ],
)

test_pulse = pulse_library.const(uid = "test_pulse", length = 100e-9, amplitude=0.5)

with test_exp.section(uid="drive_sequence"):
    
    # device_setup에 등록된 큐비트(logical signal group)들을 가져옵니다.
    # 예: logical_signal_groups.keys() -> ["q0", "q1", ...]
    for qubit_name in device_setup.logical_signal_groups.keys():
        
        # 실험에서 사용할 신호 ID 지정 (예: "drive_q0")
        exp_signal_id = f"drive_{qubit_name}"
        
        # Experiment에 해당 신호가 사용됨을 알림
        experiment_signal = ExperimentSignal(exp_signal_id)
        test_exp.signals.append(experiment_signal)

        # 각 큐비트별 섹션 생성 (순차적 실행)
        with test_exp.section(uid=f"shoot_{qubit_name}"):
            # 해당 큐비트의 드라이브 라인으로 펄스 재생
            test_exp.play(signal=exp_signal_id, pulse=test_pulse)
            
            # 다음 큐비트로 넘어가기 전 약간의 완화 시간(Relaxation) 부여
            test_exp.delay(signal=exp_signal_id, time=100e-9)

signal_map = {}

for qubit_name in device_setup.logical_signal_groups.keys():
    exp_signal_id = f"drive_{qubit_name}"
    
    # 작성하신 calibrate_devices 함수에서 정의한 logical signal 이름("drive_line")을 참조
    # 경로: /logical_signal_groups/{qubit}/drive_line
    logical_signal = device_setup.logical_signal_groups[qubit_name].logical_signals["drive_line"]
    
    signal_map[exp_signal_id] = logical_signal

# 매핑 적용
test_exp.set_signal_map(signal_map)


# 5. 세션 연결 및 실행
# do_emulation=True로 설정하면 실제 장비 없이 코드 로직을 검증할 수 있습니다.
session = Session(device_setup=device_setup)
session.connect()

# 실험 컴파일 및 실행
results = session.run(exp)

print("Experiment execution completed.")