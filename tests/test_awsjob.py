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
from qiskit.result import Result

from qiskit_aws_braket_provider.awsbackend import AWSBackend
from qiskit_aws_braket_provider.awsjob import AWSJob, _reverse_and_map
from qiskit_aws_braket_provider.awsprovider import AWSProvider

LOG = logging.getLogger(__name__)


class AWSJobTests(unittest.TestCase):

    def _load_backend(self):
        self.provider = AWSProvider(region_name='us-east-1')
        self.ionq_backend: AWSBackend = self.provider.get_backend('IonQ Device')

    def setUp(self) -> None:
        logging.basicConfig(format=logging.BASIC_FORMAT, level='INFO')

    def test_result(self):
        self._load_backend()
        job_id = '52284ef5-1cf7-4182-9547-5bbc7c5dd9f5'
        job: AWSJob = self.ionq_backend.retrieve_job(job_id=job_id)
        result: Result = job.result()
        counts = result.get_counts()
        counts_get_item = result.get_counts(0)
        self.assertEqual(counts, counts_get_item)
        self.assertEqual(counts['00'], 1)

    def test_reverse_and_map(self):
        mapping = {0: 2, 1: 3, 2: 0, 3:1}
        adjusted_bit_string = _reverse_and_map('abcd', mapping)
        self.assertEqual(adjusted_bit_string, 'badc')

    def test_reverse_and_map_less(self):
        mapping = {1: 1, 3: 0}
        adjusted_bit_string = _reverse_and_map('abcd', mapping)
        self.assertEqual(adjusted_bit_string, 'bd')
