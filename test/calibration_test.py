#%%
import sources.utils as utils
from laboneq.simple import *
import numpy as np
import matplotlib.pyplot as plt

print(utils.validate_device_existence())
from sources.calibration_helpers import calibrate_devices

device_setup = calibrate_devices(measure_type = "spec_square")
session = Session(device_setup=device_setup)
session.connect(do_emulation = False)
print(device_setup)
#%%

# 실험에서 사용할 신호 ID 지정 (예: "drive_q0")
exp_signal_id = f"drive_d1"

# acquire 정의
acquire_id =  f"acquire_d1"

test_exp = Experiment(
    uid="test_exp",
    signals=[ExperimentSignal(exp_signal_id),
             ExperimentSignal(acquire_id)],
)

phase = np.pi

delay_sweep = LinearSweepParameter(uid="delay_sweeper",
                                            start=0e-9, 
                                            stop=1000e-9, 
                                            count=100, 
                                            axis_name="delay (s)")


test_pulse = pulse_library.const(uid = "test_pulse", length = 100e-9, amplitude=0.5)

signal_map = {}

with test_exp.acquire_loop_rt(
uid= "measure",
count = 1000,
acquisition_type=AcquisitionType.SPECTROSCOPY,
):
    with test_exp.sweep(uid = "delay_sweep",parameter = delay_sweep):

        # device_setup에 등록된 큐비트(logical signal group)들을 가져옵니다.
        # 예: logical_signal_groups.keys() -> ["q0", "q1", ...]
        for qubit_name in device_setup.logical_signal_groups.keys():
            

            # 각 큐비트별 섹션 생성 (순차적 실행)
            with test_exp.section(uid=f"shoot_{qubit_name}"):
                # 해당 큐비트의 드라이브 라인으로 펄스 재생
                test_exp.play(signal=exp_signal_id, pulse=test_pulse, phase=phase)
                test_exp.delay(signal = exp_signal_id, time = delay_sweep)
                test_exp.reserve(signal=exp_signal_id)

            with test_exp.section(uid=f"acquire_{qubit_name}_section", play_after = f"shoot_{qubit_name}"):
                test_exp.play(signal="measure", pulse=test_pulse, phase=phase_sweep)
                test_exp.acquire(signal = "acquire", 
                                handle = acquire_id,
                                kernel=test_pulse,
                                )
                # 다음 큐비트로 넘어가기 전 약간의 완화 시간(Relaxation) 부여
                test_exp.reserve(signal=acquire_id)



print(qubit_name)

logical_signal = device_setup.logical_signal_groups[qubit_name].logical_signals["drive_line"]
signal_map[exp_signal_id] = logical_signal


logical_signal = device_setup.logical_signal_groups[qubit_name].logical_signals["acquire_line"]
signal_map[acquire_id] = logical_signal

# 매핑 적용
test_exp.set_signal_map(signal_map)

# 5. 세션 연결 및 실행
# do_emulation=True로 설정하면 실제 장비 없이 코드 로직을 검증할 수 있습니다.
compiled_exp = session.compile(test_exp)
show_pulse_sheet("pulse_show", compiled_exp)

# 실험 컴파일 및 실행
results = session.run(test_exp)

print("Experiment execution completed.")
# %%# -------------------------------------------------------------------------
# 6. 결과 Plotting
# -------------------------------------------------------------------------
def plot_delay_sweep_results(results, qubit_list):
    """
    각 큐비트별 Delay Sweep 결과를 Plotting 합니다.
    """
    # Sweep 축 데이터 가져오기 (Delay 시간)
    # axis_grid는 [qubit_handle][0] 처럼 접근 가능합니다.
    # 모든 큐비트가 같은 sweep을 공유하므로 첫 번째 큐비트의 축 정보를 씁니다.
    first_handle = f"acquire_{qubit_list[0]}"
    delay_axis = results.get_axis(first_handle)[0] 
    
    num_qubits = len(qubit_list)
    fig, axes = plt.subplots(num_qubits, 1, figsize=(8, 4 * num_qubits), constrained_layout=True)
    
    if num_qubits == 1:
        axes = [axes] # 큐비트가 1개일 때를 위해 리스트로 변환

    for idx, qubit_name in enumerate(qubit_list):
        handle = f"acquire_{qubit_name}"
        
        # 데이터 가져오기 (Complex number)
        data = results.get_data(handle)
        
        # Spectroscopy 결과는 보통 복소수이므로 Magnitude(절댓값)과 Phase를 봅니다.
        # 또는 I/Q 값을 볼 수도 있습니다. 여기서는 Magnitude를 그립니다.
        magnitude = np.real(data)
        
        ax = axes[idx]
        ax.plot(delay_axis * 1e9, magnitude, 'o-', label=f'Magnitude')
        
        ax.set_title(f"Qubit: {qubit_name}")
        ax.set_xlabel("Delay (ns)")
        ax.set_ylabel("Amplitude (a.u.)")
        ax.grid(True)
        ax.legend()

    plt.show()

# Plot 함수 실행
plot_delay_sweep_results(results, ["d1"])
# %%
