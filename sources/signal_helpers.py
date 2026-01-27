from laboneq.simple import *

def play_pulse_on_qubit(exp : Experiment, qubit_name, line_type, pulse, phase=0, amplitude=None):
    """
    exp: 실험 객체
    qubit_name: 'q0', 'q1' 등
    line_type: 'drive', 'measure', 'flux' 등 (device_setup의 logical signal 이름과 매칭)
    """
    # 1. 고유한 신호 ID 생성 (예: q0_drive)
    signal_id = f"{qubit_name}_{line_type}"
    
    # 2. 신호가 실험에 등록되어 있는지 확인하고, 없으면 생성 (Lazy Loading)
    if signal_id not in exp.signals:
        exp.signals[signal_id] = ExperimentSignal(signal_id)
        # print(f"DEBUG: New signal registered -> {signal_id}")

    # 3. 펄스 재생
    # amplitude가 None이면 pulse 객체의 기본값 사용, 아니면 오버라이드
    if amplitude is not None:
        exp.play(signal=signal_id, pulse=pulse, phase=phase, amplitude=amplitude)
    else:
        exp.play(signal=signal_id, pulse=pulse, phase=phase)
        
    return signal_id # 필요하면 ID 반환

def auto_map_signals(exp : Experiment, device_setup:DeviceSetup):
    """
    exp.signals에 등록된 신호 이름(예: 'q0_drive_line')을 파싱해서
    device_setup의 실제 포트와 연결해주는 함수
    """
    signal_map = {}
    
    for sig_name in exp.signals.keys():
        # 이름 규칙: "{qubit_name}_{line_type}" (예: "q0_drive_line")
        # 문자열을 분리 (첫 번째 언더바 기준)
        parts = sig_name.split('_', 1)
        if len(parts) != 2:
            continue # 규칙에 안 맞으면 패스
            
        q_name, line_type = parts[0], parts[1] # q0, drive_line
        
        # device_setup에서 해당 큐비트의 logical signal 찾기
        try:
            lsg = device_setup.logical_signal_groups[q_name]
            logical_sig = lsg.logical_signals[line_type]
            signal_map[sig_name] = logical_sig
            # print(f"Mapped: {sig_name} -> {q_name}/{line_type}")
        except KeyError:
            print(f"Warning: Could not map signal '{sig_name}'. Check naming convention.")

    exp.set_signal_map(signal_map)