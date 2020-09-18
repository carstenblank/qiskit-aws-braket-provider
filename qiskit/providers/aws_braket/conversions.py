import inspect
import itertools
import logging
from datetime import datetime
from typing import List, Type, Dict, Optional

import qiskit
from braket.aws import AwsDevice
from braket.circuits import Gate, ResultType
from braket.device_schema import DeviceCapabilities, DeviceActionType, JaqcdDeviceActionProperties
from braket.device_schema.ionq import IonqDeviceCapabilities
from qiskit.circuit.library import SXGate, SXdgGate
from qiskit.converters.ast_to_dag import AstInterpreter
from qiskit.providers import BaseBackend
from qiskit.providers.models import QasmBackendConfiguration, GateConfig, BackendProperties
from qiskit.providers.models.backendproperties import Nduv

logger = logging.getLogger(__name__)

# TODO: find missing mappings
_known_maps = {
    'i': 'id', 'cnot': 'cx', 'ccnot': 'ccx', 'si': 'sdg', 'ti': 'tdg', 'v': 'sx', 'vi': 'sxdg',
    'xx': None, 'xy': None, 'yy': None, 'zz': None,
    'cphaseshift': None, 'cphaseshift00': None, 'cphaseshift01': None, 'cphaseshift10': None, 'iswap': None,
    'pswap': None, 'phaseshift': None, 'unitary': None
}

_qiskit_not_standard_extension: Dict[str, Type[Gate]] = {
    'sx': SXGate,
    'sxdg': SXdgGate
}


def get_qiskit_gate(gate_name: str) -> Type[Gate]:
    if gate_name in AstInterpreter.standard_extension:
        gate: Type[Gate] = AstInterpreter.standard_extension[gate_name]
    elif gate_name in _qiskit_not_standard_extension:
        gate: Type[Gate] = _qiskit_not_standard_extension[gate_name]
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
    if isinstance(properties, IonqDeviceCapabilities):
        num_qubits = properties.paradigm.qubitCount

    basis_gates = [_known_maps.get(g, g) for g in basis_gates_aws]
    basis_gates = [b for b in basis_gates if b]  # FIXME: print out as warning any that cannot be translated.
    gates = [gate_name_2_gate_config(g) for g in basis_gates]

    # Coupling
    connectivity: dict = {}
    is_fully_connected = False
    if isinstance(properties, IonqDeviceCapabilities):
        connectivity = properties.paradigm.connectivity.connectivityGraph
        is_fully_connected = properties.paradigm.connectivity.fullyConnected

    if is_fully_connected:
        coupling = [[q1, q2] for q1, q2 in itertools.product(range(num_qubits), range(num_qubits)) if q1 != q2]
    else:
        coupling = list(connectivity)  # FIXME

    # Add coupling information
    for gate in gates:
        if gate.name == 'cx':
            gate.coupling_map = coupling
        else:
            gate.coupling_map = [[q] for q in range(num_qubits)]

    configuration: QasmBackendConfiguration = QasmBackendConfiguration(
        backend_name=backend_name,
        backend_version=backend_version,
        n_qubits=num_qubits,
        basis_gates=basis_gates,
        gates=gates,
        local=False,
        simulator=False,
        conditional=False,
        open_pulse=False,
        memory=False,
        max_shots=max_shots,
        coupling_map=coupling,
        max_experiments=1
    )
    return configuration


def aws_to_properties(properties: DeviceCapabilities, configuration: QasmBackendConfiguration) -> BackendProperties:
    updated_time: Optional[datetime] = properties.service.updatedAt
    general: List[Nduv] = []
    qubits: List[List[Nduv]] = []
    gates: List[qiskit.providers.models.backendproperties.Gate] = []
    # TODO: check units!!
    if isinstance(properties, IonqDeviceCapabilities):
        # per qubit: T1, T2, frequency, anharmonicity, readout_error, prob_meas0_prep1, prob_meas1_prep0
        # (if possible)
        qubits = [
            [
                Nduv(date=updated_time, name='T1', unit='ms', value=properties.provider.timing.get('T1')),
                Nduv(date=updated_time, name='T2', unit='ms', value=properties.provider.timing.get('T2'))
            ]
            for _ in range(configuration.n_qubits)
        ]

        # use native gates and all qubits possibilities: set gate_error and gate_length as parameters (Nduv)
        def get_fidelities(qubits):
            return properties.provider.fidelity.get('1Q' if len(qubits) == 1 else '2Q', {'mean': None}) \
                .get('mean')

        def get_timings(qubits):
            return properties.provider.timing.get('1Q' if len(qubits) == 1 else '2Q')

        gates = [
            qiskit.providers.models.backendproperties.Gate(
                gate=b.name,
                qubits=qubits,
                parameters=[
                    Nduv(date=updated_time, name='gate_error', unit='', value=get_fidelities(qubits)),
                    Nduv(date=updated_time, name='gate_length', unit='ms', value=get_timings(qubits))
                ])
            for b in configuration.gates for qubits in b.coupling_map
        ]

        # General Measurements maybe of interest / any other interesting measurement (like cross-talk)
        general = [
            Nduv(date=updated_time, name='spam_fidelity', unit='',
                 value=properties.provider.fidelity.get('spam', {'mean': None}).get('mean')),
            Nduv(date=updated_time, name='readout_time', unit='ms', value=properties.provider.timing.get('readout')),
            Nduv(date=updated_time, name='reset_time', unit='ms', value=properties.provider.timing.get('reset'))
        ]

    backend_properties: BackendProperties = BackendProperties(
        backend_name=configuration.name,
        backend_version=configuration.arn,
        last_update_date=updated_time,
        qubits=qubits,
        gates=gates,
        general=general
    )
    return backend_properties
