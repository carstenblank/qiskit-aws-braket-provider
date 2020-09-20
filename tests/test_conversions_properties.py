import logging
import unittest

import boto3
from braket.aws import AwsDevice
from qiskit.providers.aer.noise import NoiseModel
from qiskit.providers.aer.noise.device import basic_device_gate_errors, basic_device_readout_errors
from qiskit.providers.models import BackendProperties

from aws_braket.conversions_configuration import aws_device_2_configuration
from aws_braket.conversions_properties import aws_ionq_to_properties, aws_rigetti_to_properties, \
    aws_simulator_to_properties

LOG = logging.getLogger(__name__)


class TranspilationTests(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(format=logging.BASIC_FORMAT, level='INFO')

    def _test_noise_model(self, backend_properties: BackendProperties):
        noise_model: NoiseModel = NoiseModel()
        for qubits, error in basic_device_readout_errors(backend_properties):
            noise_model.add_readout_error(error, qubits)
        for name, qubits, error in basic_device_gate_errors(properties=backend_properties):
            noise_model.add_quantum_error(error, name, qubits)

        LOG.info(noise_model)

    def test_aws_ionq_to_properties(self):
        self.session = boto3.session.Session(region_name='us-west-1')
        aws_device = AwsDevice.get_devices(names=['IonQ Device'])[0]
        configuration = aws_device_2_configuration(aws_device)

        from braket.device_schema.ionq import IonqDeviceCapabilities
        self.assertIsInstance(aws_device.properties, IonqDeviceCapabilities)
        backend_properties: BackendProperties = aws_ionq_to_properties(aws_device.properties, configuration)

        self.assertIsInstance(backend_properties, BackendProperties)
        self._test_noise_model(backend_properties)

    def test_aws_rigetti_to_properties(self):
        self.session = boto3.session.Session(region_name='us-west-1')
        aws_device = AwsDevice.get_devices(names=['Aspen-8'])[0]
        configuration = aws_device_2_configuration(aws_device)

        from braket.device_schema.rigetti import RigettiDeviceCapabilities
        self.assertIsInstance(aws_device.properties, RigettiDeviceCapabilities)
        backend_properties: BackendProperties = aws_rigetti_to_properties(aws_device.properties, configuration)

        self.assertIsInstance(backend_properties, BackendProperties)
        self._test_noise_model(backend_properties)

    def test_aws_simulator_to_properties(self):
        self.session = boto3.session.Session(region_name='us-west-1')
        aws_device = AwsDevice.get_devices(names=['SV1'])[0]
        configuration = aws_device_2_configuration(aws_device)

        from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities
        self.assertIsInstance(aws_device.properties, GateModelSimulatorDeviceCapabilities)
        backend_properties: BackendProperties = aws_simulator_to_properties(aws_device.properties, configuration)

        self.assertIsInstance(backend_properties, BackendProperties)
        self._test_noise_model(backend_properties)
