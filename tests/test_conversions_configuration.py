import logging
import unittest

import boto3
from braket.aws import AwsDevice
from qiskit.providers.models import QasmBackendConfiguration

from aws_braket.conversions_configuration import aws_device_2_configuration

LOG = logging.getLogger(__name__)


class TranspilationTests(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(format=logging.BASIC_FORMAT, level='INFO')

    def test_convert_experiment_ionq(self):
        self.session = boto3.session.Session(region_name='us-west-1')
        aws_device = AwsDevice.get_devices(names=['IonQ Device'])[0]
        configuration: QasmBackendConfiguration = aws_device_2_configuration(aws_device)
        self.assertIsInstance(configuration, QasmBackendConfiguration)

    def test_convert_experiment_aspen8(self):
        self.session = boto3.session.Session(region_name='us-west-1')
        aws_device = AwsDevice.get_devices(names=['Aspen-8'])[0]
        configuration = aws_device_2_configuration(aws_device)
        self.assertIsInstance(configuration, QasmBackendConfiguration)

    def test_convert_experiment_sv1(self):
        self.session = boto3.session.Session(region_name='us-west-1')
        aws_device = AwsDevice.get_devices(names=['SV1'])[0]
        configuration = aws_device_2_configuration(aws_device)
        self.assertIsInstance(configuration, QasmBackendConfiguration)
