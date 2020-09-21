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
from typing import List

from boto3 import Session
from braket.aws import AwsDevice, AwsSession
from braket.device_schema.dwave import DwaveDeviceCapabilities
from qiskit.providers import BaseProvider

from . import awsbackend

logger = logging.getLogger(__name__)


class AWSProvider(BaseProvider):

    _aws_session: AwsSession
    _session: Session

    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = session
        self._aws_session = AwsSession(boto_session=session)

    def backends(self, name=None, **kwargs) -> List['awsbackend.AWSBackend']:
        devices: List[AwsDevice] = AwsDevice.get_devices(names=[name] if name else None, aws_session=self._aws_session)
        backends = [awsbackend.AWSBackend(a, provider=self) for a in devices
                    if not isinstance(a.properties, DwaveDeviceCapabilities)]
        return backends

    def get_s3_client(self):
        return self._session.client('s3')

    def get_default_bucket(self):
        return f'amazon-braket-{self._get_account_id()}'

    def _get_account_id(self):
        return self._session.client('sts').get_caller_identity().get('Account')
