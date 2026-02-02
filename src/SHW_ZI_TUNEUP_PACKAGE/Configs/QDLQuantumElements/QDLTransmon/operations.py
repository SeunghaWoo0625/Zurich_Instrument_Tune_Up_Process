from laboneq.dsl.quantum import QuantumOperations
from . import QDLTransmon, QDLTransmonParameters

class QDLTransmonOperations(QuantumOperations):
    QUBIT_TYPES = QDLTransmon
    
    # common angles used by rx, ry and rz.
    _PI = np.pi
    _PI_BY_2 = np.pi / 2
