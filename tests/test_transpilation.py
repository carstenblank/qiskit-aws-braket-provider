import logging
import unittest
from typing import Dict

import numpy
import qiskit
from braket.circuits import Circuit, QubitSet, Qubit
from braket.devices import LocalSimulator
from braket.tasks import GateModelQuantumTaskResult
from braket.tasks.local_quantum_task import LocalQuantumTask
from qiskit.providers.aer.backends.aerbackend import AerBackend
from qiskit.result import Result

from aws_braket.transpilation import convert_experiment

LOG = logging.getLogger(__name__)


class TranspilationTests(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(format=logging.BASIC_FORMAT, level='INFO')

    def test_convert_experiment(self):
        creg = qiskit.ClassicalRegister(3)
        qreg = qiskit.QuantumRegister(3)
        qc = qiskit.QuantumCircuit(qreg, creg, name='test')
        qc.h(0)
        qc.cx(0, 1)
        qc.ry(theta=numpy.pi/2, qubit=2)
        qc.ccx(0, 2, 1)
        qiskit.circuit.measure.measure(qc, qreg, creg)
        # qiskit.circuit.measure.measure(qc, qreg[0:2], creg[1:3])
        # qiskit.circuit.measure.measure(qc, qreg[2], creg[0])

        qc_transpiled = qiskit.transpile(qc, basis_gates=['u1', 'u2', 'u3', 'cx', 'id'])
        qobj = qiskit.assemble(qc_transpiled, shots=100000)

        aws_qc: Circuit = convert_experiment(qobj.experiments[0])

        logging.info('Qiskit Circuit:\n' + str(qc.draw()))
        logging.info('Qiskit Circuit (transpiled):\n' + str(qc_transpiled.draw(fold=200)))
        logging.info('Braket Circuit:\n' + str(aws_qc.diagram()))

        measured_qubits = set([rt.target.item_list[0] for rt in aws_qc.result_types])
        self.assertTrue(set(range(3)) == measured_qubits)

        backend: AerBackend = qiskit.Aer.get_backend('qasm_simulator')
        qiskit_result: Result = backend.run(qobj).result()

        sim = LocalSimulator()
        task: LocalQuantumTask = sim.run(aws_qc, shots=100000)
        braket_result: GateModelQuantumTaskResult = task.result()
        qiskit_counts: Dict[str, int] = qiskit_result.get_counts()
        braket_counts = braket_result.measurement_counts
        # Braket has Big Endian, while qiskit uses Little Endian
        self.assertTrue(qiskit_counts.keys() == set([k[::-1] for k in braket_counts.keys()]))
        self.assertTrue(all(numpy.abs(c/100000 - 0.25) < 1e-2 for c in qiskit_counts.values()))
        self.assertTrue(all(numpy.abs(c/100000 - 0.25) < 1e-2 for c in braket_counts.values()))
