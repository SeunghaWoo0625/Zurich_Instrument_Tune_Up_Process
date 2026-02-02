from laboneq import dsl
from laboneq.dsl.quantum import QuantumElement, QuantumParameters


@classformatter
@attrs.define
class QDLTransmon(QuantumElement):
    PARAMETERS_TYPE = QDLTransmonParameters




@classformatter
@attrs.define
class QDLTransmonParameters(QuantumParameters):
    ge_T1: float = 0  # noqa: N815
    ge_T2: float = 0  # noqa: N815
    ge_T2_star: float = 0  # noqa: N815
    ef_T1: float = 0  # noqa: N815
    ef_T2: float = 0  # noqa: N815
    ef_T2_star: float = 0  # noqa: N815
