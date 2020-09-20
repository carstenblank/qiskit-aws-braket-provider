import inspect
import itertools
import logging
from typing import List, Type, Dict

import pint
from braket.aws import AwsDevice
from braket.circuits import ResultType
from braket.device_schema import DeviceCapabilities, DeviceActionType, JaqcdDeviceActionProperties, \
    GateModelQpuParadigmProperties
from braket.device_schema.simulators import GateModelSimulatorParadigmProperties
from qiskit.circuit.library import SXGate, SXdgGate
from qiskit.converters.ast_to_dag import AstInterpreter
from qiskit.providers.models import QasmBackendConfiguration, GateConfig

logger = logging.getLogger(__name__)
units = pint.UnitRegistry()

# TODO: find missing mappings
_known_maps = {
    'i': 'id',
    'cnot': 'cx',
    'ccnot': 'ccx',
    'si': 'sdg',
    'ti': 'tdg',
    'v': 'sx',
    'vi': 'sxdg',
    'xx': None,
    'xy': None,
    'yy': None,
    'zz': None,
    'cphaseshift': None,
    'cphaseshift00': None,
    'cphaseshift01': None,
    'cphaseshift10': None,
    'iswap': None,
    'pswap': None,
    'phaseshift': None,
    'unitary': None
}

# TODO: complete!
_native_two_qubit_gates = ['cx']
_native_three_qubit_gates = []

_qiskit_not_standard_extension: Dict[str, Type] = {
    'sx': SXGate,
    'sxdg': SXdgGate
}


def get_qiskit_gate(gate_name: str) -> Type:
    if gate_name in AstInterpreter.standard_extension:
        gate: Type = AstInterpreter.standard_extension[gate_name]
    elif gate_name in _qiskit_not_standard_extension:
        gate: Type = _qiskit_not_standard_extension[gate_name]
    else:
        raise ValueError(f'Gate {gate_name} not known.')
    return gate


def gate_name_2_gate_config(gate_name: str):
    gate = get_qiskit_gate(gate_name)

    signature = inspect.signature(gate.__init__)
    parameters = [p for p, v in signature.parameters.items()
                  if p != 'self' and v.default == inspect.Parameter.empty]
    documentation = gate._define.__doc__ if hasattr(gate, '_define') else None
    gate_config = GateConfig(
        gate_name, parameters=parameters, qasm_def=documentation.strip() if documentation else None
    )
    return gate_config


def get_gate_coupling(connectivity: dict, num_qubits: int) -> List[List[int]]:
    # FIXME: strictly speaking, only those tuples that connect to each other can be used as native n-qubit
    #  gates, so we need to filter out those, that don't have a connection within each other.
    raw_coupling = [(int(q1), [[int(s) for s in q] for q in itertools.combinations(qs, num_qubits - 1)]) for q1, qs in connectivity.items()]
    coupling_map = [[q1] + q2 for q1, qs in raw_coupling for q2 in qs]
    return coupling_map


def apply_coupling_map(c_map: Dict[int,List[int]], mapping: Dict[int, int]) -> Dict[int, List[int]]:
    return dict(
        [(mapping[k], [mapping[e] for e in v]) for k, v in c_map.items()]
    )


def aws_device_2_configuration(aws_device: AwsDevice) -> QasmBackendConfiguration:
    configuration: QasmBackendConfiguration
    properties: DeviceCapabilities = aws_device.properties
    basis_gates_aws: List[str] = []
    result_types_aws: List[ResultType] = []
    if DeviceActionType.JAQCD in properties.action:
        # noinspection PyTypeChecker
        action_properties: JaqcdDeviceActionProperties = properties.action[DeviceActionType.JAQCD]
        basis_gates_aws = action_properties.supportedOperations
        result_types_aws = action_properties.supportedResultTypes

    # Basics
    num_qubits = 0
    backend_name = aws_device.name
    backend_version = aws_device.arn
    max_shots = properties.service.shotsRange[1]

    connectivity: dict = {}
    is_fully_connected = False
    is_simulator = False
    native_gate_set = ['u1', 'u2', 'u3', 'cx', 'id']  # use the qiskit / IBMQ default
    if hasattr(properties, 'paradigm'):
        if isinstance(properties.paradigm, GateModelQpuParadigmProperties):
            num_qubits = properties.paradigm.qubitCount
            connectivity = properties.paradigm.connectivity.connectivityGraph
            is_fully_connected = properties.paradigm.connectivity.fullyConnected
            # TODO: one day we will get data here and then do nifty things.
            # native_gate_set = properties.paradigm.nativeGateSet
            # if len(native_gate_set) == 0:
            #     native_gate_set = []
        if isinstance(properties.paradigm, GateModelSimulatorParadigmProperties):
            num_qubits = properties.paradigm.qubitCount
            is_simulator = True
            is_fully_connected = True

    basis_gates = [_known_maps.get(g, g) for g in native_gate_set]
    basis_gates = [b for b in basis_gates if b]  # FIXME: print out as warning any that cannot be translated.
    gates = [gate_name_2_gate_config(g) for g in basis_gates]

    # Coupling
    # We need to map any arbitrary qubit numbering to a canonical mapping
    from_device_2_canonical = dict([(q, i) for i, q in enumerate(connectivity.keys())])
    from_canonical_2_device = dict([(i, q) for i, q in enumerate(connectivity.keys())])
    if is_fully_connected:
        coupling = [[q1, q2] for q1, q2 in itertools.product(range(num_qubits), range(num_qubits)) if q1 != q2]
    else:
        # CouplingMap()
        coupling = [[int(k), int(c)]
                    for k, connections in apply_coupling_map(connectivity, from_device_2_canonical).items()
                    for c in connections]

    # Add coupling information
    coupling_map_1 = [[q] for q in set([q for q_list in coupling for q in q_list])]
    coupling_map_2 = get_gate_coupling(apply_coupling_map(connectivity, from_device_2_canonical), 2)
    # TODO: for another time maybe
    # coupling_map_3 = get_gate_coupling(connectivity, 3)
    for gate in gates:
        if gate.name in _native_two_qubit_gates:
            gate.coupling_map = coupling_map_2
        else:
            gate.coupling_map = coupling_map_1

    configuration: QasmBackendConfiguration = QasmBackendConfiguration(
        backend_name=backend_name,
        backend_version=backend_version,
        n_qubits=num_qubits,
        basis_gates=basis_gates,
        gates=gates,
        local=False,
        simulator=is_simulator,
        conditional=False,
        open_pulse=False,
        memory=False,
        max_shots=max_shots,
        coupling_map=coupling,
        max_experiments=None,
        coupling_device_2_canonical=from_device_2_canonical,
        coupling_canonical_2_device=from_canonical_2_device
    )
    return configuration
