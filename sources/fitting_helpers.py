import matplotlib.pyplot as plt
from laboneq.simple import *
import numpy as np

##----------------
##  global functions
##----------------

def input_signal_to_power(range_in , input_signals, acquisition_type = "SPECTROSCOPY", path = "RF"):
    #acqusition_type : "SPECTROSCOPY", "INTEGRATION", "RAW"
    #path : "RF", "LF"
    #power : [dbm]
    if acquisition_type == "RAW":
        voltage_range = power_to_voltage(range_in)
        if path == "RF":
            return voltage_range*input_signals*2**0.5
        if path == "LF":
            return voltage_range*input_signals
    elif acquisition_type == "SPECTROSCOPY":
        return input_signals
    elif acquisition_type == "INTEGRATION":
        return input_signals

def power_to_voltage(power):
    # power : [dbm]
    # voltage : [V] : peak voltage
    voltage = 10**((power-10)/20)
    return voltage

def voltage_to_power(voltage):
    # power : [dbm]
    # voltage : [V] : peak voltage
    power = 20*np.log10(voltage)+10
    return power
##----------------
##  time of flight
## ---------------
def analyze_tof_signal(raw_data, delay_axis, time_axis):
    """
    Raw Data의 면적(적분값)을 계산하여 최적의 Port Delay를 찾습니다.
    
    Args:
        raw_data (np.array): (Delay_Points, Time_Samples) 형태의 복소수 데이터
        delay_axis (np.array): Port Delay 축 데이터
        time_axis (np.array): Raw Trace 시간 축 데이터
        
    Returns:
        dict: 최적값 및 분석 결과를 담은 딕셔너리
    """
    # 1. 진폭(절댓값) 계산
    data_abs = np.abs(raw_data)
    
    # 2. 각 Delay 단계별 Raw Trace의 넓이(적분) 계산
    # axis=1 (시간축) 방향으로 다 더함
    integrated_area = np.sum(data_abs, axis=1)
    
    # 3. 넓이가 최대가 되는 인덱스 찾기
    max_idx = np.argmax(integrated_area)
    
    # 4. 최적의 Delay 값과 그때의 Trace 추출
    optimal_delay = delay_axis[max_idx]
    optimal_trace = data_abs[max_idx]
    max_area_value = integrated_area[max_idx]
    
    return {
        "integrated_area": integrated_area,
        "max_idx": max_idx,
        "optimal_delay": optimal_delay,
        "optimal_trace": optimal_trace,
        "max_area_value": max_area_value,
        "data_abs": data_abs
    }

def time_of_flight_figure(results, qubit, device):
    handle = f"{qubit}_acquire_handle"
    # LabOne Q 결과에서 데이터와 축 추출
    # 결과 형상 가정: (Sweep_Count, Sample_Count)
    raw_data = results.get_data(handle) 
    
    #device의 range in으로 부터 나중에 데이터 voltage로 변환
    range_in = results.device_setup.get_calibration().get(f"/logical_signal_groups/{qubit}/acquire_line").range
    # 축 정보 가져오기 (LabOne Q 버전에 따라 get_axis 반환값이 다를 수 있음)
    # 일반적으로 axis[0]: Sweep Axis (Delay), axis[1]: Grid Axis (Time)
    axes = results.get_axis(handle)
    delay_axis = axes[0]
    time_axis = axes[1]

    # 분석 수행
    analysis = analyze_tof_signal(raw_data, delay_axis, time_axis)
    
    # 그래프 그리기 (3행 1열)
    fig, ax = plt.subplots(3, 1, figsize=(10, 15), constrained_layout=True)
    
    # [1] Heatmap: Delay vs Raw Time
    # pcolormesh가 pcolor보다 빠름
    c = ax[0].pcolormesh(time_axis / 2 , delay_axis * 1e9, analysis["data_abs"], shading='auto', cmap='viridis')
    ax[0].set_title(f"[{device}] Time of Flight Raw Traces")
    ax[0].set_xlabel("Raw Trace Time [ns]")
    ax[0].set_ylabel("Port Delay [ns]")
    fig.colorbar(c, ax=ax[0], label="|Amplitude|")
    
    # 최적 위치 표시 (수평선)
    ax[0].axhline(analysis["optimal_delay"] * 1e9, color='r', linestyle='--', label="Optimal Delay")
    ax[0].legend()

    # [2] Integration Area vs Port Delay
    ax[1].plot(delay_axis * 1e9, analysis["integrated_area"], 'o-', markersize=4)
    ax[1].set_title("Signal Area (Integration) vs Port Delay")
    ax[1].set_xlabel("Port Delay [ns]")
    ax[1].set_ylabel("Integrated Area [a.u.]")
    ax[1].grid(True, alpha=0.3)
    
    # 최적점 강조
    ax[1].plot(analysis["optimal_delay"] * 1e9, analysis["max_area_value"], 'rx', markersize=10, 
               label=f"Max at {analysis['optimal_delay']*1e9:.1f} ns")
    ax[1].legend()

    # [3] Optimal Raw Trace (넓이가 최대일 때의 데이터)
    ax[2].plot(time_axis /2 , analysis["optimal_trace"], 'b-', label=f"Delay = {analysis['optimal_delay']*1e9:.1f} ns")
    ax[2].set_title(f"Raw Trace at Optimal Delay")
    ax[2].set_xlabel("Raw Trace Time [ns]")
    ax[2].set_ylabel("|Amplitude| [a.u.]")
    ax[2].grid(True, alpha=0.3)
    ax[2].legend()

    return fig, analysis["optimal_delay"]


##----------------
##  res_spec
## ---------------
















































































def find_oscillation_frequency_and_phase(data, time):
    w = np.fft.fft(data)
    f = np.fft.fftfreq(len(data), time[1] - time[0])
    mask = f > 0
    w, f = w[mask], f[mask]
    abs_w = np.abs(w)
    freq = 2 * np.pi * f[np.argmax(abs_w)]
    phase = 2 * np.pi - (time[np.argmax(data)] * freq)
    return freq, phase

def rotate_iq_by_pca(I, Q):
    """
    IQ cloud를 PCA로 분석해서 가장 큰 분산 방향(주축)을 rotated-I 축으로 두도록 회전.
    Returns:
        I_rot, Q_rot, theta(rad), center(I0,Q0)
    """
    I = np.asarray(I)
    Q = np.asarray(Q)

    # center
    I0, Q0 = np.mean(I), np.mean(Q)
    X = np.vstack([I - I0, Q - Q0])  # shape (2, N)

    # covariance & eig
    C = np.cov(X)
    eigvals, eigvecs = np.linalg.eigh(C)  # ascending
    v = eigvecs[:, np.argmax(eigvals)]    # principal axis (2,)

    # principal axis angle
    theta = np.arctan2(v[1], v[0])  # angle of principal axis vs +I

    # rotate by -theta so principal axis aligns with +I_rot
    ct, st = np.cos(-theta), np.sin(-theta)
    R = np.array([[ct, -st],
                  [st,  ct]])

    Xr = R @ X
    I_rot, Q_rot = Xr[0, :], Xr[1, :]
    return I_rot, Q_rot, theta, (I0, Q0)

def sorted_mesh(xvals, yvals, zvals):
    """
    Prepare the x, y, z arrays to be plotted with matplotlib pcolormesh.

    Ensures that the z values are sorted according to the values in xvals and yvals and
    creates np.meshgrid from xvals and yvals.

    Args:
        xvals: array of the values to be plotted on the x-axis: typically the real-time
            sweep points
        yvals: array of the values to be plotted on the y-axis: typically the near-time
            sweep points
        zvals: array of the values to be plotted on the z-axis: typically the data

    Returns:
        the x, y, and z values to be passed directly to pcolormesh

    """
    # First, we need to sort the data as otherwise we get odd plotting
    # artefacts. An example is e.g., plotting a fourier transform
    sorted_x_arguments = xvals.argsort()
    xvals = xvals[sorted_x_arguments]
    sorted_y_arguments = yvals.argsort()
    yvals = yvals[sorted_y_arguments]
    zvals_srt = zvals[:,  sorted_x_arguments]
    zvals_srt = zvals_srt[sorted_y_arguments, :]

    xgrid, ygrid = np.meshgrid(xvals, yvals)

    return xgrid, ygrid, zvals_srt

def plot_iq_plane_ax(
    ax,
    I,
    Q,
    title=None,
    equal_axis=True,
    center=True,
    grid=True,
    s=10,
    alpha=0.7,
):
    """
    Plot IQ data on a given matplotlib axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axis to draw on
    I, Q : array-like
        IQ data
    title : str, optional
        Title of the subplot
    equal_axis : bool
        Enforce equal aspect ratio (I and Q scale)
    center : bool
        Center axes around (0, 0)
    grid : bool
        Show grid
    s : float
        Marker size
    alpha : float
        Marker transparency
    """

    # Scatter plot
    ax.scatter(I, Q, s=s, alpha=alpha)

    # Labels
    ax.set_xlabel("I")
    ax.set_ylabel("Q")

    # Title
    if title is not None:
        ax.set_title(title)

    # Equal aspect ratio (CRITICAL for IQ)
    if equal_axis:
        ax.set_aspect("equal", adjustable="box")

    # Center axes around origin with equal limits
    if center:
        lim = np.max(np.abs(np.concatenate([I, Q])))
        if lim > 0:
            ax.set_xlim(-lim, lim)
            ax.set_ylim(-lim, lim)

    # Grid
    if grid:
        ax.grid(True)

    return ax


def res_spec_fit_plot(results, qubit_params, qbn):
    device = qubit_params[f"Q{qbn}"]["DRV"]["device"]
    port = qubit_params[f"Q{qbn}"]["DRV"]["port"]
    # --- 1. 데이터 추출 및 전처리 ---
    handle = results.experiment.uid

    # 데이터를 한 번만 가져옵니다 (속도 및 일관성 향상)
    raw_data = results.get_data(handle)

    mag = np.abs(raw_data)
    phase = np.angle(raw_data)
    phase = np.unwrap(phase)

    # 주파수 축 계산 (GHz 변환)
    res_axis = results.get_axis(handle)
    lo_freq = qubit_params["QA"][device]["LO"]
    
    freqs = (res_axis[0] + lo_freq) / 1e9

    # --- 2. Fitting 준비 및 실행 ---
    # Guess 값 설정 (단위 주의)
    width_guess = (freqs[-1] - freqs[0]) * 0.02 # 전체 범위의 10% 정도로 추정
    pos_guess = freqs[np.argmin(mag)]          # Magnitude가 최소인 지점 (Dip)
    amp_guess = -(np.max(mag) - np.min(mag))   # Dip의 깊이 (음수)
    offset_guess = np.median(mag)              # 베이스라인

    # Fit 실행 (사용자의 fit_mods 모듈이 있다고 가정)
    try:
        popt, pcov = fit_mods.lorentzian.fit(freqs, mag, width_guess, pos_guess, amp_guess, offset_guess)
        f0 = popt[1] # Resonance Frequency (GHz)
        fit_curve = fit_mods.lorentzian(freqs, *popt)
        fit_label = f"Fit $f_0$ = {f0:.6f} GHz"
        fit_success = True
    except Exception as e:
        print(f"Fitting failed: {e}")
        f0 = pos_guess # 실패 시 guess 값을 반환하거나 예외 처리
        fit_curve = np.zeros_like(freqs)
        fit_label = "Fit Failed"
        fit_success = False

    # --- 3. Plotting (개선된 부분) ---
    # sharex=True를 통해 x축(주파수)을 공유합니다.
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 8), constrained_layout=True)
    # 상단 그래프: Magnitude & Fit
    ax1.set_title(f"Pulsed Resonator Spectroscopy Q{qbn}")
    ax1.plot(freqs, mag, '.', color='navy', alpha=0.3, label='Raw Data') # 원본 데이터는 점으로 표현
    if fit_success:
        ax1.plot(freqs, fit_curve, 'r-', linewidth=2, label=fit_label)   # Fit 결과는 선으로 표현
    ax1.set_ylabel("Magnitude $|S_{21}|$ (a.u.)", fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='best')
    # 하단 그래프: Phase
    ax2.plot(freqs, phase, color='darkorange', linewidth=1.5)
    ax2.set_ylabel("Phase (rad)", fontsize=12)
    ax2.set_xlabel("Frequency (GHz)", fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.6)
    # Phase 그래프에 Resonance Frequency 지점 표시 (옵션)
    if fit_success:
        ax2.axvline(x=f0, color='red', linestyle='--', alpha=0.5, label=f'$f_0$')
    # 결과 반환 (f0는 Hz 단위로 변환하여 반환)
    plt.legend()
    plt.show()

    return fig, f0 * 1e9

def qubit_spec_fit_plot(results, qubit_params, qbn):
    handle = results.experiment.uid
    device = qubit_params[f"Q{qbn}"]["DRV"]["device"]
    port = qubit_params[f"Q{qbn}"]["DRV"]["port"]

    data = results.get_data(handle)
    I = np.real(data)
    Q = np.imag(data)
    I_rot, Q_rot, theta, (I0, Q0) = rotate_iq_by_pca(I, Q)

    res_axis = results.get_axis(handle)

    # 🔹 하나의 figure
    fig = plt.figure(figsize=(10, 8), constrained_layout=True)
    gs = fig.add_gridspec(2, 2)

    ax_iq = fig.add_subplot(gs[0, 0])
    ax_iq_rot = fig.add_subplot(gs[0, 1])
    ax_spec = fig.add_subplot(gs[1, :])

    # --- IQ planes ---
    plot_iq_plane_ax(ax_iq, I, Q, title="Original IQ")
    plot_iq_plane_ax(ax_iq_rot, I_rot, Q_rot, title="Rotated IQ (PCA)")

    # --- Spectroscopy ---
    freqs = (res_axis[0] + qubit_params["SG"][device]["LO"][port // 2]) / 1e9

    width_guess = (freqs[-1] - freqs[0]) * 0.1
    offset_guess = np.median(I_rot)
    
    y_max = np.max(I_rot)
    y_min = np.min(I_rot)
    offset_guess = np.median(I_rot)
    if abs(y_max - offset_guess) > abs(y_min - offset_guess):
        # peak
        amp_guess = y_max - offset_guess
        pos_guess = freqs[np.argmax(I_rot)]
    else:
        # dip
        amp_guess = y_min - offset_guess   # 음수!
        pos_guess = freqs[np.argmin(I_rot)]

    ax_spec.plot(freqs, I_rot, label="Data")
    ax_spec.set_ylabel("Transmission |S21| (a.u.)")
    ax_spec.set_xlabel("Frequency (GHz)")
    ax_spec.set_title(f"Pulsed Qubit Spectroscopy Q{qbn}")

    popt, pcov = fit_mods.lorentzian.fit(
        freqs, I_rot,
        width_guess, pos_guess, amp_guess, offset_guess
    )

    f0 = round(popt[1], 7)

    ax_spec.plot(
        freqs,
        fit_mods.lorentzian(freqs, *popt),
        "r-",
        label=f"f = {f0} GHz\nγ = {popt[0]:.7f}"
    )
    ax_spec.legend()

    plt.show()
    
    return fig, f0 * 1e9

def res_spec_amp_fit_plot(results, qubit_params, qbn):
    """
    2D resonator spectroscopy vs power 결과를 플롯하고,
    각 amplitude에서 frequency cut에 대해 Lorentzian fit으로 center frequency를 구해
    amplitude에 따른 center frequency도 함께 플롯한다.

    또한 각 amplitude에 해당하는 1D frequency-spectroscopy + fit 플롯들을 생성/저장한다.

    마지막에는 2D plot에서 ginput으로 점 1개를 선택하게 하고
    (selected_amp, selected_freq)를 리턴한다.
    """

    # 저장 폴더 준비
    out_dir = "res_spec_power"
    os.makedirs(out_dir, exist_ok=True)

    handle = results.experiment.uid

    # axis[0] = amplitude sweep, axis[1] = frequency sweep (IF, Hz) 라고 가정
    amp_vals = results.get_axis(handle)[0]
    amp_name = results.get_axis_name(handle)[0]
    freqs_no_lo = results.get_axis(handle)[1]          # Hz
    freqs_Hz = freqs_no_lo + qubit_params["QA"]["LO"]  # 실제 RO 주파수 (Hz)
    freqs_GHz = freqs_Hz / 1e9

    # 데이터 (amplitude x frequency), 복소 -> 절댓값
    data = results.get_data(handle)      # shape ~ (n_amp, n_freq)
    data_abs = np.abs(data)

    # ---------- 1) 2D heatmap 플롯 ----------
    fig_map, ax_map = plt.subplots(constrained_layout=True)
    xvals, yvals, zvals = sorted_mesh(freqs_GHz, amp_vals, data_abs)

    mesh = ax_map.pcolormesh(xvals, yvals, zvals, cmap="magma", shading="auto")
    ax_map.set_title(f"Pulsed Resonator Spectroscopy v Power Q{qbn}")
    ax_map.set_xlabel("Readout Frequency, $f_{\\mathrm{RO}}$ (GHz)")
    ax_map.set_ylabel(amp_name)
    cbar = fig_map.colorbar(mesh)
    cbar.set_label("Signal Magnitude, $|S_{21}|$ (a.u.)")

    # 기존 RO freq (GHz) 위치에 세로선
    ax_map.axvline(
        x=qubit_params[f"Q{qbn}"]["RO"]["freq"] / 1e9,
        color="w",
        linestyle="--",
        linewidth=0.3,
    )

    # 2D heatmap 저장
    fig_map_path = os.path.join(out_dir, f"Q{qbn}_res_spec_power_map.png")
    fig_map.savefig(fig_map_path, dpi=150)

    # ---------- 2) 각 amplitude에서 1D cut + Lorentzian fit ----------
    center_freqs_GHz = []

    for i_amp, amp_val in enumerate(amp_vals):
        y_row = data_abs[i_amp, :]  # 해당 amplitude에서 frequency 방향 cut

        # resonator dip 가정: 최소값 근처에서 fit
        width_guess = 0.1  # GHz 단위 대략적인 추정치
        pos_guess = freqs_GHz[np.argmin(y_row)]
        amp_guess = -np.max(y_row) * width_guess
        offset_guess = np.median(y_row)

        try:
            # fit_mods.lorentzian.fit(x, y, width, pos, amp, offset)
            popt, pcov = fit_mods.lorentzian.fit(
                freqs_GHz, y_row, width_guess, pos_guess, amp_guess, offset_guess
            )
            f0 = popt[1]  # center frequency (GHz)
        except Exception as e:
            f0 = np.nan

        center_freqs_GHz.append(f0)

        # --- 각 amplitude별 1D plot 생성 및 저장 ---
        fig_cut, ax_cut = plt.subplots(constrained_layout=True)
        ax_cut.plot(freqs_GHz, y_row, "b.", label="data")

        if not np.isnan(f0):
            y_fit = fit_mods.lorentzian(freqs_GHz, *popt)
            ax_cut.plot(freqs_GHz, y_fit, "r-", label=f"fit, f0={f0:.6f} GHz")

        ax_cut.set_title(f"Q{qbn} - Amp = {amp_val:.4g}")
        ax_cut.set_xlabel("Frequency (GHz)")
        ax_cut.set_ylabel("Transmission $|S_{21}|$ (a.u.)")
        ax_cut.legend()

        # figure 보여주기 (non-blocking)
        plt.show(block=False)

        # 저장
        fig_cut_path = os.path.join(
            out_dir,
            f"Q{qbn}_amp_{i_amp:02d}_{amp_val:.4g}.png"
        )
        fig_cut.savefig(fig_cut_path, dpi=150)

    center_freqs_GHz = np.array(center_freqs_GHz)

    # ---------- 3) amplitude vs center frequency 플롯 ----------
    fig_cf, ax_cf = plt.subplots(constrained_layout=True)
    ax_cf.plot(amp_vals, center_freqs_GHz, "o-")
    ax_cf.set_xlabel(amp_name)
    ax_cf.set_ylabel("Center frequency $f_0$ (GHz)")
    ax_cf.set_title(f"Resonator center frequency vs power Q{qbn}")

    plt.show(block=False)

    # 저장
    fig_cf_path = os.path.join(out_dir, f"Q{qbn}_center_freq_vs_power.png")
    fig_cf.savefig(fig_cf_path, dpi=150)

    # ---------- 4) 2D heatmap에서 ginput으로 점 선택 ----------
    print("2D spectroscopy map에서 (frequency, amplitude) 한 점을 클릭하세요.")
    # ginput 대상 figure를 heatmap으로 확실히 지정
    plt.figure(fig_map.number)
    selected_points = plt.ginput(1, timeout=-1)  # -1: 무제한 기다림

    if selected_points:
        selected_freq, selected_amp = selected_points[0]
        print(f"Selected Frequency: {selected_freq} GHz, Selected Amplitude: {selected_amp}")
    else:
        print("아무 점도 선택되지 않았습니다. NaN을 반환합니다.")
        selected_freq = np.nan
        selected_amp = np.nan

    # heatmap figure도 화면에 남겨두고 싶으면 닫지 말고, 닫고 싶으면 아래 주석 해제
    # plt.close(fig_map)

    # 기존 호출부와 호환: fig, selected_amp, selected_freq 리턴
    return fig_map, selected_amp, selected_freq

def rabi_amp_fit_plot(results, qubit_params, qbn):
    handle = results.experiment.uid
    data = results.get_data(handle)
    rabi_amp = results.get_axis(handle)[0]

    I = np.real(data)
    Q = np.imag(data)

    # --- IQ rotation ---
    I_rot, Q_rot, theta, (I0, Q0) = rotate_iq_by_pca(I, Q)

    # 🔹 하나의 figure
    fig = plt.figure(figsize=(10, 8), constrained_layout=True)
    gs = fig.add_gridspec(2, 2)

    ax_iq     = fig.add_subplot(gs[0, 0])
    ax_iq_rot = fig.add_subplot(gs[0, 1])
    ax_rabi   = fig.add_subplot(gs[1, :])

    # --- IQ planes ---
    plot_iq_plane_ax(ax_iq, I, Q, title="Original IQ")
    plot_iq_plane_ax(ax_iq_rot, I_rot, Q_rot, title="Rotated IQ (PCA)")

    # ---- Rabi fitting on rotated I ----
    offset_guess = np.mean(I_rot)

    # amplitude guess: peak / dip 자동 대응
    if abs(np.max(I_rot) - offset_guess) > abs(np.min(I_rot) - offset_guess):
        amp_guess = np.max(I_rot) - offset_guess
    else:
        amp_guess = np.min(I_rot) - offset_guess

    freq_guess, phase_guess = find_oscillation_frequency_and_phase(
        I_rot - offset_guess, rabi_amp
    )

    popt, pcov = fit_mods.oscillatory.fit(
        rabi_amp,
        I_rot,
        freq_guess,
        phase_guess,
        amp_guess,
        offset_guess,
    )

    # phase wrap
    popt[1] = np.mod(popt[1], 2 * np.pi)

    pi_pulse   = round(np.pi / popt[0], 5)
    first_peak = round((2 * np.pi - popt[1]) / popt[0], 5)

    # --- Plot Rabi ---
    ax_rabi.set_title(f"Rabi Amplitude Measurement Q{qbn}")
    ax_rabi.plot(rabi_amp, I_rot, ".k", markersize=4, label="Rotated I")
    ax_rabi.plot(
        rabi_amp,
        fit_mods.oscillatory(rabi_amp, *popt),
        "r-",
        label=f"π amp = {pi_pulse}, first peak = {first_peak}"
    )

    ax_rabi.set_xlabel("Qubit Drive Pulse Amplitude (a.u.)")
    ax_rabi.set_ylabel("Rotated I signal (a.u.)")
    ax_rabi.legend()

    plt.show()

    return fig, pi_pulse, first_peak

def T1_T2_fit_plot(type, results, qbn):
    handle = results.experiment.uid
    data = results.get_data(handle)
    delay_time = results.get_axis(handle)[0] / 1e-6
    
    fig = plt.figure(constrained_layout=True)
    plt.plot(delay_time, data, ".k")

    popt, pcov = fit_mods.exponential_decay.fit(delay_time, data, 1 / 2 / 5, 0, 0)
    decay_rate = round(1/popt[0], 3)

        
    if type == "T1":
        label_str = rf"T1 = {decay_rate} $\mu$s"
        plt.title(f"T1 Measurement Q{qbn}")
        plt.ylabel("Signal Magnitude, $|S_{21}|$ (a.u.)")
        plt.xlabel(r"Time Delay After X180 ($\mu$s)")
    elif type == "T2":
        label_str = rf"T2 = {decay_rate} $\mu$s"
        plt.title(f"T2 Hahn Echo Measurement Q{qbn}")
        plt.ylabel("Signal Magnitude, $|S_{21}|$ (a.u.)")
        plt.xlabel(r"Time Delay between x90 and X180 ($\mu$s)")
    

    delay_plot = np.linspace(delay_time[0], delay_time[-1], 5 * len(delay_time))
    plt.plot(delay_plot, fit_mods.exponential_decay(delay_plot, *popt), "-r", label=label_str)
    plt.legend()
    plt.show()

    return fig, round(decay_rate*1e-6, 9)


def ramsey_fit_plot(qubit, results, qbn):
    handle = results.experiment.uid
    ramsey_delay = results.get_axis(handle)[0] / 1e-6

    data = results.get_data(handle)
    I = np.real(data)
    Q = np.imag(data)

    I_rot, Q_rot, theta, (I0, Q0) = rotate_iq_by_pca(I, Q)
    ramsey_1d = I_rot

    # guesses
    amp_guess = (np.max(ramsey_1d) - np.min(ramsey_1d)) / 2
    offset_guess = np.mean(ramsey_1d)
    decay_rate_guess = qubit["metadata"]["T1"]
    freq_guess, phase_guess = find_oscillation_frequency_and_phase(ramsey_1d - offset_guess, ramsey_delay)

    fig, axes = plt.subplots(2, 1, figsize=(16, 10), constrained_layout=True)

    # (2,1,1) IQ plane (equal scale)
    axes[0].plot(I, Q, ".", markersize=3, label="Ramsey IQ (raw)")
    axes[0].set_xlabel("I")
    axes[0].set_ylabel("Q")
    axes[0].set_aspect("equal", adjustable="box")

    xmin, xmax = I.min(), I.max()
    ymin, ymax = Q.min(), Q.max()
    span = max(xmax - xmin, ymax - ymin)
    xmid, ymid = (xmin + xmax) / 2, (ymin + ymax) / 2
    axes[0].set_xlim(xmid - span/2, xmid + span/2)
    axes[0].set_ylim(ymid - span/2, ymid + span/2)
    axes[0].legend(title=f"PCA θ={theta:.3f} rad")

    # (2,1,2) rotated I′ + fit
    axes[1].plot(ramsey_delay, ramsey_1d, ".k", markersize=3, label="Rotated I′")

    try:
        popt, pcov = fit_mods.oscillatory_decay.fit(
            ramsey_delay, ramsey_1d,
            freq_guess, phase_guess, decay_rate_guess,
            amp_guess, offset_guess
        )

        f_ramsey = round(popt[0] / (2*np.pi), 8)
        T2_star  = round(1 / popt[2] / 1e6, 8)

        axes[1].plot(
            ramsey_delay,
            fit_mods.oscillatory_decay(ramsey_delay, *popt),
            "-r",
            label=f"Ramsey Frequency = {f_ramsey} (MHz)\nT2* = {T2_star} ($\\mu$s)"
        )
        axes[1].legend()

    except RuntimeError:
        print("Fitting is not available. Introduce detuning frequency f_detuning to fit data.")
        T2_star = 0
        f_ramsey = 0

    axes[1].set_title(f"Ramsey Measurement T2* Q{qbn} (Rotated I′)")
    axes[1].set_xlabel("Time Delay between X90 Pulses ($\\mu$s)")
    axes[1].set_ylabel("Rotated I′ (a.u.)")

    plt.show()
    return fig, T2_star, f_ramsey * 1e6


def IQ_fit_plot(results, handles, qbn):
    experiment_handles = []
    I = []
    Q = []
    for handle in handles:
        ex_handle = results.experiment.uid + handle
        experiment_handles.append(ex_handle)
        I.append(np.real(results.get_data(ex_handle)))
        Q.append(np.imag(results.get_data(ex_handle)))
    
    (Ig_rotated, Qg_rotated), (Ie_rotated, Qe_rotated), angle = IQ_rotation(
        Ig, Qg, Ie, Qe
    )

    fit = minimize(_false,
        0.5 * (np.mean(Ig_rotated) + np.mean(Ie_rotated)),
        (Ig_rotated, Ie_rotated),
        method="Nelder-Mead",
    )
    threshold = fit.x[0]

    gg = np.sum(Ig_rotated < threshold) / len(Ig_rotated)
    ge = np.sum(Ig_rotated > threshold) / len(Ig_rotated)
    eg = np.sum(Ie_rotated < threshold) / len(Ie_rotated)
    ee = np.sum(Ie_rotated > threshold) / len(Ie_rotated)

    fidelity = 100 * (gg + ee) / 2

    fig, axes = plot_IQblobs(Ig_rotated, Qg_rotated, Ie_rotated, Qe_rotated, qbn)
    print(
            f"""
        Fidelity Matrix:
        -----------------
        | {gg:.3f} | {ge:.3f} |
        ----------------
        | {eg:.3f} | {ee:.3f} |
        -----------------
        IQ plane rotated by: {180 / np.pi * angle:.1f}{chr(176)}
        Threshold: {threshold:.3e}
        Fidelity: {fidelity:.1f}%
        """
        )
        
    return fig, threshold, fidelity



# def IQ_ef_fit_plot(results, handles, qbn):
#     handle_g = results.experiment.uid + handles[0]
#     handle_e = results.experiment.uid + handles[1]
#     handle_f = results.experiment.uid + handles[2]

#     Ig = np.real(results.get_data(handle_g))
#     Qg = np.imag(results.get_data(handle_g))
#     Ie = np.real(results.get_data(handle_e))
#     Qe = np.imag(results.get_data(handle_e))
#     If = np.real(results.get_data(handle_f))
#     Qf = np.imag(results.get_data(handle_f))


#     (Ig_rotated, Qg_rotated), (Ie_rotated, Qe_rotated), (If_rotated, Qf_rotated), angle = IQ_rotation(
#         Ig, Qg, Ie, Qe, If, Qf
#     )

#     fit = minimize(_false,
#         0.5 * (np.mean(Ig_rotated) + np.mean(Ie_rotated)),
#         (Ig_rotated, Ie_rotated),
#         method="Nelder-Mead",
#     )
#     threshold = fit.x[0]

#     gg = np.sum(Ig_rotated < threshold) / len(Ig_rotated)
#     ge = np.sum(Ig_rotated > threshold) / len(Ig_rotated)
#     eg = np.sum(Ie_rotated < threshold) / len(Ie_rotated)
#     ee = np.sum(Ie_rotated > threshold) / len(Ie_rotated)
    
#     fidelity = 100 * (gg + ee) / 2

#     fig, axes = plot_ef_IQblobs(Ig_rotated, Qg_rotated, Ie_rotated, Qe_rotated, qbn)
#     print(
#             f"""
#         Fidelity Matrix:
#         -----------------
#         | {gg:.3f} | {ge:.3f} |
#         ----------------
#         | {eg:.3f} | {ee:.3f} |
#         -----------------
#         IQ plane rotated by: {180 / np.pi * angle:.1f}{chr(176)}
#         Threshold: {threshold:.3e}
#         Fidelity: {fidelity:.1f}%
#         """
#         )
        
#     return fig, threshold, fidelity


# def plot_IQblobs(Ig_rotated, Qg_rotated, Ie_rotated, Qe_rotated, qbn, threshold=None):
#     fig, axes = plt.subplots(3, 1, figsize=(4, 6), sharex=True,
#                              gridspec_kw={'height_ratios': [3, 1, 1]})
#     axes[0].plot(Ig_rotated, Qg_rotated, ".", alpha=0.2, label="Ground", markersize=4)
#     axes[0].plot(Ie_rotated, Qe_rotated, ".", alpha=0.2, label="Excited", markersize=4)
#     if threshold !=None:
#         axes[0].axvline(x=threshold, color="k", ls="-", alpha=0.7)
#     axes[0].axis("equal")
#     axes[0].grid()
#     axes[0].legend(["Ground", "Excited"])
#     axes[0].set_ylabel("Q quadrature [Arb. Units]")
#     axes[0].set_title(f"IQ blobs_Q{qbn}")

#     xlim_IQ = np.array(axes[0].get_xlim())
#     bin = np.linspace(xlim_IQ[0], xlim_IQ[1], 50)
#     hist1 = np.histogram(Ig_rotated, bins=bin)
#     hist2 = np.histogram(Ie_rotated, bins=bin)

#     acum1 = np.cumsum(hist1[0]) / len(Ig_rotated)
#     acum2 = np.cumsum(hist2[0]) / len(Ig_rotated)

#     axes[1].hist(Ig_rotated, bins=50, alpha=0.75, label="Ground", )
#     axes[1].hist(Ie_rotated, bins=50, alpha=0.75, label="Excited")
#     if threshold != None:
#         axes[1].axvline(x=threshold, color="k", ls="-", alpha=0.7)
#     axes[1].set_ylabel("Counts")
#     axes[1].grid()

#     # Accumulation
#     axes[2].plot(hist1[1][1:], acum1)
#     axes[2].plot(hist2[1][1:], acum2)
#     if threshold != None:
#         axes[2].axvline(x=threshold, color="k", ls="-", alpha=0.7)
#     axes[2].set_ylabel('Cum. Prob.')
#     axes[2].set_xlabel("I quadrature [Arb. Units]")
#     axes[2].grid()
#     axes[2].set_ylim([-0.1, 1.1])
#     fig.tight_layout()
#     plt.show()
#     return fig, axes

# def plot_ef_IQblobs(Ig_rotated, Qg_rotated, Ie_rotated, Qe_rotated, If_rotated, Qf_rotated, qbn, threshold=None):
#     fig, axes = plt.subplots(3, 1, figsize=(4, 6), sharex=True,
#                              gridspec_kw={'height_ratios': [3, 1, 1]})
#     axes[0].plot(Ig_rotated, Qg_rotated, ".", alpha=0.2, label="Ground", markersize=4)
#     axes[0].plot(Ie_rotated, Qe_rotated, ".", alpha=0.2, label="Excited", markersize=4)
#     if threshold !=None:
#         axes[0].axvline(x=threshold, color="k", ls="-", alpha=0.7)
#     axes[0].axis("equal")
#     axes[0].grid()
#     axes[0].legend(["Ground", "Excited"])
#     axes[0].set_ylabel("Q quadrature [Arb. Units]")
#     axes[0].set_title(f"IQ blobs_Q{qbn}")

#     xlim_IQ = np.array(axes[0].get_xlim())
#     bin = np.linspace(xlim_IQ[0], xlim_IQ[1], 50)
#     hist1 = np.histogram(Ig_rotated, bins=bin)
#     hist2 = np.histogram(Ie_rotated, bins=bin)

#     acum1 = np.cumsum(hist1[0]) / len(Ig_rotated)
#     acum2 = np.cumsum(hist2[0]) / len(Ig_rotated)

#     axes[1].hist(Ig_rotated, bins=50, alpha=0.75, label="Ground", )
#     axes[1].hist(Ie_rotated, bins=50, alpha=0.75, label="Excited")
#     if threshold != None:
#         axes[1].axvline(x=threshold, color="k", ls="-", alpha=0.7)
#     axes[1].set_ylabel("Counts")
#     axes[1].grid()

#     # Accumulation
#     axes[2].plot(hist1[1][1:], acum1)
#     axes[2].plot(hist2[1][1:], acum2)
#     if threshold != None:
#         axes[2].axvline(x=threshold, color="k", ls="-", alpha=0.7)
#     axes[2].set_ylabel('Cum. Prob.')
#     axes[2].set_xlabel("I quadrature [Arb. Units]")
#     axes[2].grid()
#     axes[2].set_ylim([-0.1, 1.1])
#     fig.tight_layout()
#     plt.show()
#     return fig, axes




def _false(threshold, Ig, Ie):
    if np.mean(Ig) < np.mean(Ie):
        num_false = np.sum(Ig > threshold) + np.sum(Ie < threshold)
    else:
        num_false = np.sum(Ig < threshold) + np.sum(Ie > threshold)
    return num_false

def IQ_rotation(Ig, Qg, Ie, Qe):
    angle = np.arctan2(np.mean(Qe) - np.mean(Qg), np.mean(Ig) - np.mean(Ie))
    C = np.cos(angle)
    S = np.sin(angle)
    # Condition for having e > Ig
    if np.mean((Ig - Ie) * C - (Qg - Qe) * S) > 0:
        angle += np.pi
        C = np.cos(angle)
        S = np.sin(angle)

    Ig_rotated = Ig * C - Qg * S
    Qg_rotated = Ig * S + Qg * C

    Ie_rotated = Ie * C - Qe * S
    Qe_rotated = Ie * S + Qe * C

    return (Ig_rotated, Qg_rotated), (Ie_rotated, Qe_rotated), angle


def DRAG_cal_fit_plot(results, handles, qbn):
    handle_0 = results.experiment.uid + handles[0]
    handle_1 = results.experiment.uid + handles[1]

    # axis (beta sweep)
    q_scale = np.array(results.get_axis(handle_0)[0])

    # raw complex data
    raw_X180Y90 = np.array(results.get_data(handle_0))
    raw_Y90X180 = np.array(results.get_data(handle_1))
    
    I_X180Y90 = np.real(np.array(results.get_data(handle_0)))
    Q_X180Y90 = np.real(np.array(results.get_data(handle_0)))
    I_Y90X180 = np.real(np.array(results.get_data(handle_1)))
    Q_Y90X180 = np.real(np.array(results.get_data(handle_1)))
    
    I_rot_X180Y90, Q_rot_X180Y90, _, _ = rotate_iq_by_pca(np.real(raw_X180Y90), np.imag(raw_X180Y90))
    I_rot_Y90X180, Q_rot_Y90X180, _, _ = rotate_iq_by_pca(np.real(raw_Y90X180), np.imag(raw_Y90X180))


    print("q_scale shape:", q_scale.shape)
    print("I0 shape:", I_rot_X180Y90.shape, "I1 shape:", I_rot_Y90X180.shape)

    # =====================================================
    # DRAG beta 계산: I vs beta 선형 피팅 교차점 기준
    # =====================================================
    s0, b0, *_ = linregress(q_scale, I_rot_X180Y90)
    s1, b1, *_ = linregress(q_scale, I_rot_Y90X180)

    # 두 직선 교차점
    beta_opt = (b1 - b0) / (s0 - s1)

    # beta_opt에 가장 가까운 index (IQ plot에서 강조용)
    idx_opt = np.argmin(np.abs(q_scale - beta_opt))

    # =========================================
    # 2) I vs beta  /  3) Q vs beta
    # =========================================
    fig, axes = plt.subplots(2, 1, figsize=(8, 12))

    # (2) I vs beta
    axI = axes[0]
    axI.plot(q_scale, I_rot_X180Y90, ".-", label="X180Y90")
    axI.plot(q_scale, I_rot_Y90X180, ".-", label="Y90X180")
    axI.axvline(beta_opt, linestyle="--", label=f"beta_opt = {beta_opt:.4g}")
    axI.set_xlabel("Q Scale (beta)")
    axI.set_ylabel("rotated I (a.u.)")
    axI.set_title(f"rotated I signal vs beta (Q{qbn})")
    axI.legend()

    # IQ Plane plot
    ax_iq = axes[1]
    ax_iq.plot(I_X180Y90, Q_X180Y90, ".g", label="X180Y90")
    ax_iq.plot(I_Y90X180, Q_Y90X180, ".b", label="Y90X180")

    ax_iq.set_xlabel("I")
    ax_iq.set_ylabel("Q")
    ax_iq.set_title(f"IQ plane (Q{qbn})")
    ax_iq.legend()
    ax_iq.set_aspect("equal", "box")
    
    plt.tight_layout()
    plt.show()


    print(f"Selected qscale (DRAG beta value from I vs beta) = {beta_opt}")
    return fig, beta_opt


def DRAG_cal_fit_plot_past(results, handles, qbn):
    handle_0 = results.experiment.uid + handles[0]
    handle_1 = results.experiment.uid + handles[1]

    # axis (beta sweep)
    q_scale = np.array(results.get_axis(handle_0)[0])

    # raw data
    raw0 = np.array(results.get_data(handle_0))
    raw1 = np.array(results.get_data(handle_1))

    # shot 방향 평균 (shape: (n_points,))
    if raw0.ndim > 1:
        y0 = np.abs(raw0.mean(axis=0))
        y1 = np.abs(raw1.mean(axis=0))
    else:
        y0 = np.abs(raw0)
        y1 = np.abs(raw1)

    print("q_scale shape:", q_scale.shape)
    print("y0 shape:", y0.shape, "y1 shape:", y1.shape)

    # 선형 피팅
    s0, b0, *_ = linregress(q_scale, y0)
    s1, b1, *_ = linregress(q_scale, y1)

    y_fit_0 = s0 * q_scale + b0
    y_fit_1 = s1 * q_scale + b1

    # 두 직선 교차점으로 beta 계산
    beta_opt = (b1 - b0) / (s0 - s1)

    fig = plt.figure()
    plt.plot(q_scale, y0, ".g", label=handle_0)
    plt.plot(q_scale, y1, ".b", label=handle_1)
    plt.plot(q_scale, y_fit_0, "g")
    plt.plot(q_scale, y_fit_1, "b")
    plt.axvline(beta_opt, linestyle="--", label=f"beta_opt = {beta_opt:.4g}")
    plt.ylabel("A (a.u.)")
    plt.xlabel("Q Scale (beta)")
    plt.legend()
    plt.show()

    print(f"Selected qscale (DRAG beta value) = {beta_opt}")
    return fig, beta_opt



def NPulse_Amplification_fit_plot(results, qbn):
    handle = results.experiment.uid
    N = results.get_axis(handle)[0]
    
    I = np.real(results.get_data(handle))
    Q = np.imag(results.get_data(handle))
    
    
    # rotate IQ -> (I_rot, Q_rot)
    I_rot, Q_rot, theta, (I0, Q0) = rotate_iq_by_pca(I, Q)

    # ---- plotting ----
    fig, axes = plt.subplots(2, 1, figsize=(16, 10), constrained_layout=True)

    # (2,1,1) IQ plane
    axes[0].plot(I, Q, ".", markersize=3, label="NPulse Amplification (raw IQ)")
    axes[0].set_xlabel("I")
    axes[0].set_ylabel("Q")
    axes[0].set_aspect("equal", adjustable="box")

    # equal scale
    xmin, xmax = I.min(), I.max()
    ymin, ymax = Q.min(), Q.max()
    span = max(xmax - xmin, ymax - ymin)
    xmid, ymid = (xmin + xmax) / 2, (ymin + ymax) / 2
    axes[0].set_xlim(xmid - span/2, xmid + span/2)
    axes[0].set_ylim(ymid - span/2, ymid + span/2)

    axes[0].legend(title=f"PCA θ = {theta:.3f} rad")

    # (2,1,2) rotated I′
    axes[1].plot(N, I_rot, ".k", markersize=4, label="Rotated I'")
    axes[1].set_title(f"X Pi & X -Pi Repetition Q{qbn}")
    axes[1].set_xlabel("Repetition N")
    axes[1].set_ylabel("Rotated I′")
    axes[1].legend()

    plt.show()

    return fig
