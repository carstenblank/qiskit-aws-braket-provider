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

from qiskit_aws_braket_provider.awsbackend import AWSBackend
from qiskit_aws_braket_provider.awsprovider import AWSProvider

LOG = logging.getLogger(__name__)


class AWSProviderTests(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(format=logging.BASIC_FORMAT, level='INFO')
        self.session = boto3.session.Session(region_name='us-east-1')

    def test_backends(self):
        provider = AWSProvider(self.session)
        backends = provider.backends()
        LOG.info(backends)

    def test_get_backend_ionq(self):
        provider = AWSProvider(self.session)
        ionq_backend: AWSBackend = provider.get_backend('IonQ Device')
        LOG.info(ionq_backend)

    def test_get_backend_aspen8(self):
        provider = AWSProvider(self.session)
        ionq_backend: AWSBackend = provider.get_backend('Aspen-8')
        LOG.info(ionq_backend)

    def test_get_backend_simulator(self):
        provider = AWSProvider(self.session)
        ionq_backend: AWSBackend = provider.get_backend('SV1')
        LOG.info(ionq_backend)
