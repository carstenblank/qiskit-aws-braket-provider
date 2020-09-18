import logging
import unittest

import boto3

from aws_braket.awsbackend import AWSBackend
from aws_braket.awsprovider import AWSProvider

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
