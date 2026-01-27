from laboneq.simple import *

def play_pulse_on_qubit(exp : Experiment, qubit_name, line_type, pulse, phase=0, amplitude=None, **kwargs):
    """
    exp: 실험 객체
    qubit_name: 'q0', 'q1' 등
    line_type: 'drive', 'measure', 'flux' 등 (device_setup의 logical signal 이름과 매칭)
    """
    # 1. 고유한 신호 ID 생성 (예: q0_drive)
    signal_id = f"{qubit_name}_{line_type}_signal"
    
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

def auto_map_signals(exp:Experiment, device_setup:DeviceSetup):
    """
    Experiment에 등록된 신호 이름을 파싱하여 DeviceSetup과 자동으로 매핑합니다.
    
    [Naming Convention]
    - Experiment Signal: "{qubit}_{type}_signal"  (예: q0_drive_signal)
    - Logical Signal:    "{type}_line"            (예: drive_line)
    
    위 규칙에 따라 q0_drive_signal -> q0 그룹의 drive_line으로 매핑됩니다.
    """
    signal_map = {}
    
    for sig_name in exp.signals.keys():
        # 1. "_signal"로 끝나는지 확인 (규칙 검사)
        if not sig_name.endswith("_signal"):
            print(f"[AutoMap] Skip: '{sig_name}' does not end with '_signal'")
            continue
            
        # 2. 접미사 "_signal" 제거 및 큐비트 이름 분리
        # "q0_drive_signal" -> "q0_drive"
        core_name = sig_name.rsplit("_signal", 1)[0]
        
        # 첫 번째 언더바(_)를 기준으로 큐비트 이름과 타입 분리
        # "q0_drive" -> ["q0", "drive"]
        # 만약 "q0_drive_ef"라면 -> ["q0", "drive_ef"] 가 됩니다.
        parts = core_name.split("_", 1)
        
        if len(parts) != 2:
            print(f"[AutoMap] Warning: Cannot parse qubit name from '{sig_name}'")
            continue
            
        qubit_name = parts[0]  # 예: "q0"
        sig_type = parts[1]    # 예: "drive" (또는 "drive_ef")
        
        # 3. Logical Signal 이름 생성 ("_line" 붙이기)
        # "drive" -> "drive_line"
        logical_sig_name = f"{sig_type}_line"
        
        # 4. Device Setup에서 찾아서 매핑
        try:
            # 해당 큐비트 그룹 찾기
            lsg = device_setup.logical_signal_groups[qubit_name]
            
            # 해당 라인 찾기
            if logical_sig_name in lsg.logical_signals:
                signal_map[sig_name] = lsg.logical_signals[logical_sig_name]
                # print(f"[AutoMap] Mapped: {sig_name} -> {qubit_name}/{logical_sig_name}")
            else:
                print(f"[AutoMap] Error: Logical signal '{logical_sig_name}' not found in group '{qubit_name}'")
                
        except KeyError:
            print(f"[AutoMap] Error: Qubit group '{qubit_name}' not found in device_setup")

    # 5. 매핑 적용
    exp.set_signal_map(signal_map)
    print("Automatic signal mapping completed.")