from laboneq_applications.qpu_types.tunable_transmon import TunableTransmonQubit, TunableTransmonOperations, TunableTransmonQubitParameters
from laboneq.dsl.quantum import QuantumElement, QuantumParameters, QuantumOperations
from laboneq.simple import *
import attrs
from typing import ClassVar, Dict
from laboneq.core.utilities.dsl_dataclass_decorator import classformatter

@classformatter
@attrs.define()
class QDLTransmonParameters(TunableTransmonQubitParameters):
    drive_device: str | None = None
    drive_port: int | None = None
    measure_device: str | None = None
    flux_device: str | None = None
    flux_port: int | None = None

@classformatter
@attrs.define()
class QDLTransmon(TunableTransmonQubit):
    PARAMETERS_TYPE: ClassVar[type[QuantumParameters]] = QDLTransmonParameters


class QDLTransmonOperations(TunableTransmonOperations):
    QUBIT_TYPES = QDLTransmon
    

    # @dsl.quantum_operation
    # def arbitrary_gate(
    #     self,
    #     q: Transmon,
    # ) -> None:
    #     dsl.play(q, )


# # 1. 물리적 파라미터 (JSON의 "parameters" 부분)
# @attrs.define
# class PhysicalParams:
#     freq: float = 5.0e9
#     freq_ef: float = 5.0e9
#     T1: float = 1e-05
#     T2: float = 2e-05
#     T2_echo: float = 1e-05

# # 2. 구동 펄스 파라미터 (JSON의 "operations" 내부의 값들)
# @attrs.define
# class DriveParams:
#     type: str = "parametric"
#     amp_spectroscopy: float = 0.1
#     pulse_length: float = 2e-08
#     amp_pi: float = 1.0
#     amp_half_pi: float = 0.5
#     freq_detuning: float = 0.0
#     beta: float = 0.0

# # 3. 측정 파라미터 (JSON의 "measures" 내부의 값들)
# @attrs.define
# class MeasureParams:
#     acquire_type: str = "SPECTROSCOPY"
#     type: str = "parametric"
#     freq: float | None = None
#     port_delay: float = 0.0
#     pulse_amp: float = 0.0
#     pulse_length: float = 1.0e-6
#     integration_length: float = 2.0e-6
#     # 필요한 필드 추가... (threshold, integration_phase 등)
#     threshold: list[float] = attrs.field(factory=list) 
#     # 나머지 필드는 생략하거나 필요시 추가
#     save_address: str | None = None

# # Operations 그룹 ("operations" 키에 대응)
# @attrs.define
# class OperationGroup:
#     # drive와 ef_drive는 구조가 같으므로 같은 클래스(DriveParams) 사용
#     drive: DriveParams = attrs.field(factory=DriveParams)
#     ef_drive: DriveParams = attrs.field(factory=DriveParams)

# # Measures 그룹 ("measures" 키에 대응)
# @attrs.define
# class MeasureGroup:
#     # JSON 키 이름 그대로 변수명 지정
#     spec_square: MeasureParams = attrs.field(factory=MeasureParams)
#     inte_square: MeasureParams = attrs.field(factory=MeasureParams)
#     inte_discriminator: MeasureParams = attrs.field(factory=MeasureParams)

# @attrs.define
# class QDLTransmonParameter(QuantumParameters):
#     # JSON: "parameters" -> Python: static
#     information: PhysicalParams = attrs.field(factory=PhysicalParams)
    
#     # JSON: "operations" -> Python: operations
#     operations: OperationGroup = attrs.field(factory=OperationGroup)
    
#     # JSON: "measures" -> Python: measures
#     measures: MeasureGroup = attrs.field(factory=MeasureGroup)
