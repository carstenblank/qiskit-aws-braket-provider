import logging
from typing import Iterable

import braket.circuits.gates as gates
from braket.circuits import Instruction, Circuit
from qiskit.qobj import QasmQobj, QasmQobjExperiment, QasmQobjInstruction

logger = logging.getLogger(__name__)

_qiskit_2_braket_conversion = {
    # "u1": U1Gate,
    # "u2": U2Gate,
    # "u3": U3Gate,
    "x": gates.X,
    "y": gates.Y,
    "z": gates.Z,
    "t": gates.T,
    "tdg": gates.Ti,
    "s": gates.S,
    "sdg": gates.Si,
    "sx": gates.V,
    "sxdg": gates.Vi,
    "swap": gates.Swap,
    "rx": gates.Rx,
    # "rxx": RXXGate,
    "ry": gates.Ry,
    "rz": gates.Rz,
    # "rzz": RZZGate,
    "id": gates.I,
    "h": gates.H,
    "cx": gates.CNot,
    "cy": gates.CY,
    "cz": gates.CZ,
    # "ch": CHGate,
    # "crx": CRXGate,
    # "cry": CRYGate,
    # "crz": CRZGate,
    # "cu1": CU1Gate,
    # "cu3": CU3Gate,
    "ccx": gates.CCNot,
    "cswap": gates.CSwap
}


def convert_experiment(experiment: QasmQobjExperiment) -> Circuit:
    qc = Circuit()

    qasm_obj_instruction: QasmQobjInstruction
    for qasm_obj_instruction in experiment.instructions:
        name = qasm_obj_instruction.name
        if name == 'measure':
            pass
        else:
            params = []
            if hasattr(qasm_obj_instruction, 'params'):
                params = qasm_obj_instruction.params
            gate = _qiskit_2_braket_conversion[name](*params)
            instruction = Instruction(operator=gate, target=qasm_obj_instruction.qubits)
            qc += instruction

    return qc


def convert_qasm_qobj( qobj: QasmQobj) -> Iterable[Circuit]:
    experiment: QasmQobjExperiment
    for experiment in qobj.experiments:
        yield convert_experiment(experiment)