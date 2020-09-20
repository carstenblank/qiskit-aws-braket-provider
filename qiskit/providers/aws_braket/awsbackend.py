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
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Union, Tuple

from botocore.response import StreamingBody
from braket.aws import AwsDevice, AwsQuantumTask, AwsSession
from braket.circuits import Circuit
from braket.device_schema import DeviceCapabilities
from braket.device_schema.ionq import IonqDeviceCapabilities
from braket.device_schema.rigetti import RigettiDeviceCapabilities
from braket.device_schema.simulators import GateModelSimulatorDeviceCapabilities
from qiskit.providers import BaseBackend, JobStatus
from qiskit.providers.models import QasmBackendConfiguration, BackendProperties, BackendStatus
from qiskit.qobj import QasmQobj

from . import awsjob
from . import awsprovider
from .conversions_configuration import aws_device_2_configuration
from .conversions_properties import aws_ionq_to_properties, aws_rigetti_to_properties, aws_simulator_to_properties
from .transpilation import convert_qasm_qobj

logger = logging.getLogger(__name__)


class AWSBackend(BaseBackend):

    _aws_device: AwsDevice
    _configuration: QasmBackendConfiguration
    _provider: 'awsprovider.AWSProvider'

    def __init__(self, aws_device: AwsDevice, provider: 'awsprovider.AWSProvider' = None):
        super().__init__(aws_device_2_configuration(aws_device), provider)
        self._aws_device = aws_device
        self._run = aws_device.run

    def properties(self) -> BackendProperties:
        properties: DeviceCapabilities = self._aws_device.properties
        if isinstance(properties, IonqDeviceCapabilities):
            return aws_ionq_to_properties(properties, self._configuration)
        if isinstance(properties, RigettiDeviceCapabilities):
            return aws_rigetti_to_properties(properties, self._configuration)
        if isinstance(properties, GateModelSimulatorDeviceCapabilities):
            return aws_simulator_to_properties(properties, self._configuration)

    def status(self) -> BackendStatus:
        pass

    def _get_job_data_s3_folder(self, job_id):
        return f"results-{self.name()}-{job_id}"

    @staticmethod
    def _exists_file(s3_client, s3_bucket: str, file: str):
        result: dict = s3_client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=file
        )
        # TODO: error handling
        return result['KeyCount'] != 0

    def _save_job_task_arns(self, job_id: str, task_arns: List[str],
                            s3_bucket: Optional[str] = None) -> AwsSession.S3DestinationFolder:
        used_s3_bucket = s3_bucket or self._provider.get_default_bucket()
        s3_client = self._provider.get_s3_client()
        file = f'{self._get_job_data_s3_folder(job_id=job_id)}/task_arns.json'
        if AWSBackend._exists_file(s3_client, used_s3_bucket, file):
            raise ValueError(f"An object '{file}' does already exist in the bucket {used_s3_bucket}")
        result = s3_client.put_object(Body=json.dumps(task_arns).encode(), Bucket=used_s3_bucket, Key=file)
        # TODO: error handling
        return used_s3_bucket, self._get_job_data_s3_folder(job_id=job_id)

    def _delete_job_task_arns(self, job_id: str, s3_bucket: Optional[str] = None):
        used_s3_bucket = s3_bucket or self._provider.get_default_bucket()
        s3_client = self._provider.get_s3_client()
        file = f'{self._get_job_data_s3_folder(job_id=job_id)}/task_arns.json'
        if not AWSBackend._exists_file(s3_client, used_s3_bucket, file):
            raise ValueError(f"An object '{file}' does not exist in the bucket {used_s3_bucket}")
        result: dict = s3_client.delete_object(Bucket=used_s3_bucket, Key=file)
        # TODO: error handling

    def _load_job_task_arns(self, job_id: str, s3_bucket: Optional[str] = None) -> List[str]:
        used_s3_bucket = s3_bucket or self._provider.get_default_bucket()
        s3_client = self._provider.get_s3_client()
        file = f'{self._get_job_data_s3_folder(job_id=job_id)}/task_arns.json'

        if not AWSBackend._exists_file(s3_client, used_s3_bucket, file):
            raise ValueError(f"An object '{file}' does not exist in the bucket {used_s3_bucket}")

        result: dict = s3_client.get_object(Bucket=used_s3_bucket, Key=file)
        # TODO: error handling
        streaming_body: StreamingBody = result['Body']
        data: bytes = streaming_body.read()
        task_arns = json.loads(data.decode())
        return task_arns

    def _save_job_data_s3(self, qobj: QasmQobj, s3_bucket: Optional[str] = None,
                          extra_data: Optional[dict] = None) -> AwsSession.S3DestinationFolder:
        used_s3_bucket: str = s3_bucket or self._provider.get_default_bucket()
        s3_client = self._provider.get_s3_client()
        file = f'{self._get_job_data_s3_folder(job_id=qobj.qobj_id)}/qiskit_qobj_data.json'
        if AWSBackend._exists_file(s3_client, used_s3_bucket, file):
            raise ValueError(f"An object '{file}' already exists at the bucket {used_s3_bucket}")

        body = {
            'qobj_id': qobj.qobj_id,
            'qobj': qobj.to_dict()
        }
        if extra_data:
            body['extra_data'] = extra_data

        result = s3_client.put_object(Body=json.dumps(body).encode(), Bucket=used_s3_bucket, Key=file)
        # TODO: error handling
        return used_s3_bucket, self._get_job_data_s3_folder(job_id=qobj.qobj_id)

    def _delete_job_data_s3(self, job_id: str, s3_bucket: Optional[str] = None):
        used_s3_bucket = s3_bucket or self._provider.get_default_bucket()
        s3_client = self._provider.get_s3_client()
        file = f'{self._get_job_data_s3_folder(job_id=job_id)}/qiskit_qobj_data.json'
        if not AWSBackend._exists_file(s3_client, used_s3_bucket, file):
            raise ValueError(f"An object '{file}' does not exist in the bucket {used_s3_bucket}")
        result: dict = s3_client.delete_object(Bucket=used_s3_bucket, Key=file)
        # TODO: error handling

    def _load_job_data_s3(self, job_id: str, s3_bucket: Optional[str] = None) -> Tuple[QasmQobj, dict]:
        used_s3_bucket = s3_bucket or self._provider.get_default_bucket()
        s3_client = self._provider.get_s3_client()
        file = f'{self._get_job_data_s3_folder(job_id=job_id)}/qiskit_qobj_data.json'
        if not AWSBackend._exists_file(s3_client, used_s3_bucket, file):
            raise ValueError(f"An object '{file}' does not exist in the bucket {used_s3_bucket}")

        result: dict = s3_client.get_object(Bucket=used_s3_bucket, Key=file)
        # TODO: error handling

        streaming_body: StreamingBody = result['Body']
        data: bytes = streaming_body.read()
        stored_experiment_data = json.loads(data.decode())
        assert 'qobj' in stored_experiment_data
        qobj_raw = stored_experiment_data['qobj']
        qobj = QasmQobj.from_dict(qobj_raw)
        extra_data = stored_experiment_data.get('extra_data', {})

        return qobj, extra_data

    def _create_task(self, job_id: str, qc: Circuit, shots: int, s3_bucket: Optional[str] = None) -> AwsQuantumTask:
        used_s3_bucket: str = s3_bucket or self._provider.get_default_bucket()
        task: AwsQuantumTask = self._aws_device.run(
            task_specification=qc,
            s3_destination_folder=(used_s3_bucket, self._get_job_data_s3_folder(job_id)),
            shots=shots
        )
        return task

    def jobs(
            self,
            limit: int = 10,
            skip: int = 0,
            status: Optional[Union[JobStatus, str, List[Union[JobStatus, str]]]] = None,
            job_name: Optional[str] = None,
            start_datetime: Optional[datetime] = None,
            end_datetime: Optional[datetime] = None,
            job_tags: Optional[List[str]] = None,
            job_tags_operator: Optional[str] = "OR",
            descending: bool = True,
            db_filter: Optional[Dict[str, Any]] = None
    ) -> List['awsjob.AWSJob']:
        # TODO: use job tags as meta data on s3, else use the method of active_jobs
        pass

    def active_jobs(self, limit: int = 10) -> List['awsjob.AWSJob']:
        client = self._provider._aws_session.braket_client
        task_arns = []
        nextToken = 'init'
        while nextToken is not None:
            result: dict = client.search_quantum_tasks(
                filters=[{
                    'name': self.name(),
                    'operator': 'EQUAL',
                    'values': ['CREATED', 'QUEUED', 'RUNNING']
                    }
                ],
                maxResults=limit,
                nextToken=None if nextToken == 'init' or nextToken is None else nextToken
            )
            # TODO: build all task_arns, query s3 for all keys with task_arns.json, see to which task a job associated, load the jobs via job_id
        pass

    def retrieve_job(self, job_id: str, s3_bucket: Optional[str] = None) -> 'awsjob.AWSJob':
        qobj, extra_data = self._load_job_data_s3(job_id=job_id, s3_bucket=s3_bucket)
        arns = self._load_job_task_arns(job_id=job_id, s3_bucket=s3_bucket)
        tasks = [AwsQuantumTask(arn=arn) for arn in arns]
        job = awsjob.AWSJob(
            job_id=job_id,
            qobj=qobj,
            tasks=tasks,
            extra_data=extra_data,
            s3_bucket=s3_bucket,
            backend=self
        )
        return job

    def run(self, qobj: QasmQobj, s3_bucket: Optional[str] = None, extra_data: Optional[dict] = None):
        s3_location: AwsSession.S3DestinationFolder = self._save_job_data_s3(qobj, s3_bucket=s3_bucket, extra_data=extra_data)

        # If we get here, then we can continue with running, else ValueError!
        circuits: List[Circuit] = list(convert_qasm_qobj(qobj))
        shots = qobj.config.shots
        shots = 1  # TODO: remove once you feel safe!

        tasks: List[AwsQuantumTask] = []
        try:
            for circuit in circuits:
                task = self._aws_device.run(
                    task_specification=circuit,
                    s3_destination_folder=s3_location,
                    shots=shots
                )
                tasks.append(task)
        except Exception as ex:
            logger.error(f'During creation of tasks an error occurred: {ex}')
            logger.error(f'Cancelling all tasks {len(tasks)}!')
            for task in tasks:
                logger.error(f'Attempt to cancel {task.id}...')
                task.cancel()
                logger.error(f'State of {task.id}: {task.state()}.')
            raise ex
        task_arns = [t.id for t in tasks]
        self._save_job_task_arns(job_id=qobj.qobj_id, task_arns=task_arns, s3_bucket=s3_location[0])

        job = awsjob.AWSJob(
            job_id=qobj.qobj_id,
            qobj=qobj,
            tasks=tasks,
            extra_data=extra_data,
            s3_bucket=s3_location[0],
            backend=self
        )
        return job
