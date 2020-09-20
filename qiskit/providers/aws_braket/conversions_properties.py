import logging
from datetime import datetime
from typing import List, Dict

import pint
import qiskit
from braket.device_schema import DeviceCapabilities
from braket.device_schema.ionq import IonqDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities
from qiskit.providers import BaseBackend
from qiskit.providers.models import QasmBackendConfiguration, BackendProperties
from qiskit.providers.models.backendproperties import Nduv

logger = logging.getLogger(__name__)
units = pint.UnitRegistry()


# noinspection PyTypeChecker
def aws_ionq_to_properties(properties: IonqDeviceCapabilities, configuration: QasmBackendConfiguration) -> BackendProperties:
    updated_time: datetime = properties.service.updatedAt or datetime.now()
    general: List[Nduv] = []
    qubits: List[List[Nduv]] = []
    gates: List[qiskit.providers.models.backendproperties.Gate] = []
    # FIXME: qiskit has an absolutely rediculous unit conversion mechanism,
    #  see qiskit.providers.models.backendproperties.BackendProperties._apply_prefix,
    #  which means that since we have seconds (s) we need to convert them to milli-seconds otherwise we get a
    #  BackendPropertyError raised.

    # per qubit: T1, T2, frequency, anharmonicity, readout_error, prob_meas0_prep1, prob_meas1_prep0
    # (if possible)
    qubits = [
        [
            Nduv(date=updated_time, name='T1', unit='ms',
                 value=(properties.provider.timing.get('T1') * units.seconds).m_as(units.milliseconds)),
            Nduv(date=updated_time, name='T2', unit='ms',
                 value=(properties.provider.timing.get('T2') * units.seconds).m_as(units.milliseconds))
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
                Nduv(date=updated_time, name='gate_error', unit='',
                     value=1 - get_fidelities(qubits)),
                Nduv(date=updated_time, name='gate_length', unit='ms',
                     value=(get_timings(qubits) * units.seconds).m_as(units.milliseconds))
            ])
        for b in configuration.gates for qubits in b.coupling_map
    ]

    # General Measurements maybe of interest / any other interesting measurement (like cross-talk)
    general = [
        Nduv(date=updated_time, name='spam_fidelity', unit='',
             value=properties.provider.fidelity.get('spam', {'mean': None}).get('mean')),
        Nduv(date=updated_time, name='readout_time', unit='ms',
             value=(properties.provider.timing.get('readout') * units.seconds).m_as(units.milliseconds)),
        Nduv(date=updated_time, name='reset_time', unit='ms',
             value=(properties.provider.timing.get('reset') * units.seconds).m_as(units.milliseconds))
    ]

    backend_properties: BackendProperties = BackendProperties(
        backend_name=configuration.backend_name,
        backend_version=configuration.backend_version,
        last_update_date=updated_time,
        qubits=qubits,
        gates=gates,
        general=general
    )
    return backend_properties


# noinspection PyTypeChecker
def aws_rigetti_to_properties(properties: RigettiDeviceCapabilities, configuration: QasmBackendConfiguration) -> BackendProperties:
    updated_time: datetime = properties.service.updatedAt or datetime.now()
    general: List[Nduv] = []
    qubits: Dict[str, List[Nduv]] = {}
    gates: List[qiskit.providers.models.backendproperties.Gate] = []

    specs: Dict[str, Dict[str, Dict[str, float]]] = properties.provider.specs

    # TODO: check units!!

    # per qubit: T1, T2, frequency, anharmonicity, readout_error, prob_meas0_prep1, prob_meas1_prep0
    # (if possible)
    one_qubit_specs: Dict[str, Dict[str, float]] = specs['1Q']
    two_qubit_specs: Dict[str, Dict[str, float]] = specs['2Q']
    qubits_dict = dict([
        (q, [  # The default cannot be 0.0 exactly... TODO: find out what a good default value could be
            Nduv(date=updated_time, name='T1', unit='ms', value=(q_specs.get('T1', 1e-9) * units.seconds).m_as(units.milliseconds)),
            Nduv(date=updated_time, name='T2', unit='ms', value=(q_specs.get('T2', 1e-9) * units.seconds).m_as(units.milliseconds)),
            Nduv(date=updated_time, name='readout_error', unit='', value=q_specs.get('fRO')),
        ])
        for q, q_specs in one_qubit_specs.items()
    ])
    qubits = list(qubits_dict.values())

    # use native gates and all qubits possibilities: set gate_error and gate_length as parameters (Nduv)
    def get_fidelities(qubits):
        if len(qubits) == 1:
            q = configuration.coupling_canonical_2_device[qubits[0]]
            stats: Dict[str, float] = one_qubit_specs[q]
            return stats.get('f1Q_simultaneous_RB')
        else:
            q = "-".join([configuration.coupling_canonical_2_device[q] for q in sorted(qubits)])
            stats: Dict[str, float] = two_qubit_specs[q]
            return stats.get('fCZ')

    gates = [
        qiskit.providers.models.backendproperties.Gate(
            gate=b.name,
            qubits=q,
            parameters=[
                Nduv(date=updated_time, name='gate_error', unit='', value=1 - get_fidelities(q)),
                Nduv(date=updated_time, name='gate_length', unit='ns', value=60 if len(q) == 1 else 160 if len(q) else None)
            ])
        for b in configuration.gates for q in b.coupling_map
    ]

    # General Measurements maybe of interest / any other interesting measurement (like cross-talk)
    general = []

    backend_properties: BackendProperties = BackendProperties(
        backend_name=configuration.backend_name,
        backend_version=configuration.backend_version,
        last_update_date=updated_time,
        qubits=qubits,
        gates=gates,
        general=general
    )
    # backend_properties._qubits = qubits
    return backend_properties


# noinspection PyTypeChecker
def aws_simulator_to_properties(properties: GateModelSimulatorDeviceCapabilities, configuration: QasmBackendConfiguration) -> BackendProperties:
    updated_time: datetime = properties.service.updatedAt or datetime.now()
    general: List[Nduv] = []
    qubits: List[List[Nduv]] = []
    gates: List[qiskit.providers.models.backendproperties.Gate] = []

    backend_properties: BackendProperties = BackendProperties(
        backend_name=configuration.backend_name,
        backend_version=configuration.backend_version,
        last_update_date=updated_time,
        qubits=qubits,
        gates=gates,
        general=general
    )
    return backend_properties


# noinspection PyTypeChecker
def aws_general_to_properties(properties: DeviceCapabilities, configuration: QasmBackendConfiguration) -> BackendProperties:
    updated_time: datetime = properties.service.updatedAt or datetime.now()
    general: List[Nduv] = []
    qubits: List[List[Nduv]] = []
    gates: List[qiskit.providers.models.backendproperties.Gate] = []

    backend_properties: BackendProperties = BackendProperties(
        backend_name=configuration.name,
        backend_version=configuration.arn,
        last_update_date=updated_time,
        qubits=qubits,
        gates=gates,
        general=general
    )
    return backend_properties
