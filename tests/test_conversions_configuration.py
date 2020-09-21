# Copyright 2020 Carsten Blank
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import unittest

import boto3
from braket.aws import AwsDevice
from qiskit.providers.models import QasmBackendConfiguration

from qiskit_aws_braket_provider.conversions_configuration import aws_device_2_configuration

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
