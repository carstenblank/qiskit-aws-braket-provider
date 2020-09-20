import logging
import unittest

import boto3
from qiskit.result import Result

from aws_braket.awsbackend import AWSBackend
from aws_braket.awsjob import AWSJob, _reverse_and_map
from aws_braket.awsprovider import AWSProvider

LOG = logging.getLogger(__name__)


class AWSJobTests(unittest.TestCase):

    def setUp(self) -> None:
        logging.basicConfig(format=logging.BASIC_FORMAT, level='INFO')
        self.session = boto3.session.Session(region_name='us-east-1')
        self.provider = AWSProvider(self.session)
        self.ionq_backend: AWSBackend = self.provider.get_backend('IonQ Device')

    def test_result(self):
        job_id = '52284ef5-1cf7-4182-9547-5bbc7c5dd9f5'
        job: AWSJob = self.ionq_backend.retrieve_job(job_id=job_id)
        result: Result = job.result()
        counts = result.get_counts()
        counts_get_item = result.get_counts(0)
        self.assertEqual(counts, counts_get_item)
        self.assertEqual(counts['00'], 1)

    def test_reverse_and_map(self):
        mapping = {0: 2, 1: 3, 2: 0, 3:1}
        adjusted_bit_string = _reverse_and_map('dcba', mapping)
        self.assertEqual(adjusted_bit_string, 'badc')
