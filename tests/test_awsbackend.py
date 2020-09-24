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
import time
import unittest
import uuid

import boto3
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile, assemble
from qiskit.circuit.measure import measure
from qiskit.providers import JobStatus

from qiskit_aws_braket_provider.awsbackend import AWSBackend
from qiskit_aws_braket_provider.awsprovider import AWSProvider

LOG = logging.getLogger(__name__)


class AWSBackendTests(unittest.TestCase):

    backend_name = 'IonQ Device'

    def setUp(self) -> None:
        logging.basicConfig(format=logging.BASIC_FORMAT, level='INFO')
        self.provider: AWSProvider = AWSProvider(region_name='us-east-1')
        self.backend: AWSBackend = self.provider.get_backend(self.backend_name)

    def test_get_job_data_s3_folder(self):
        key = self.backend._get_job_data_s3_folder('12345')
        self.assertEqual(key, f'results-{self.backend_name}-12345')

    def test_save_job_task_arns(self):
        job_id = str(uuid.uuid4())
        task_arns = ['537a196e-8162-41c6-8c72-a7f8b456da31', '537a196e-8162-41c6-8c72-a7f8b456da32',
                   '537a196e-8162-41c6-8c72-a7f8b456da33', '537a196e-8162-41c6-8c72-a7f8b456da34']
        s3_bucket, s3_folder = self.backend._save_job_task_arns(job_id, task_arns)
        self.assertTrue(
            AWSBackend._exists_file(self.provider._session.client('s3'), s3_bucket, f'{s3_folder}/task_arns.json')
        )
        self.backend._delete_job_task_arns(job_id=job_id, s3_bucket=s3_bucket)

    def test_save_job_data_s3(self):
        creg = ClassicalRegister(2)
        qreg = QuantumRegister(2)
        qc = QuantumCircuit(qreg, creg, name='test')
        qc.h(0)
        qc.cx(0, 1)
        measure(qc, qreg, creg)
        qobj = assemble(10 * [qc])

        extra_data = {
            'test': [
                'yes', 'is', 'there'
            ]
        }

        s3_bucket, s3_key = self.backend._save_job_data_s3(qobj=qobj, s3_bucket=None, extra_data=extra_data)
        self.assertEqual(s3_bucket, self.backend.provider().get_default_bucket())
        self.assertEqual(s3_key, f'results-{self.backend_name}-{qobj.qobj_id}')
        self.assertTrue(
            AWSBackend._exists_file(self.provider._session.client('s3'), s3_bucket, f'{s3_key}/qiskit_qobj_data.json')
        )
        self.backend._delete_job_data_s3(job_id=qobj.qobj_id, s3_bucket=None)

    def test_load_job_task_arns(self):
        job_id = '2020-09-17T18:47:48.653735-60f7a533-a5d5-481c-9671-681f4823ce25'
        arns = self.backend._load_job_task_arns(job_id=job_id)
        self.assertListEqual(
            arns, ['537a196e-8162-41c6-8c72-a7f8b456da31', '537a196e-8162-41c6-8c72-a7f8b456da32',
                   '537a196e-8162-41c6-8c72-a7f8b456da33', '537a196e-8162-41c6-8c72-a7f8b456da34']
        )

    def test_load_job_data_s3(self):
        job_id = '2020-09-17T18:47:48.653735-60f7a533-a5d5-481c-9671-681f4823ce25'
        qobj, extra_data = self.backend._load_job_data_s3(job_id=job_id)
        self.assertEqual(qobj.qobj_id, '66da2c50-2e5c-47aa-81c5-d47a04df804c')
        self.assertTrue('test' in extra_data)
        self.assertListEqual(extra_data['test'], ['yes', 'is', 'there'])

    def test_compile(self):
        creg = ClassicalRegister(2)
        qreg = QuantumRegister(2)
        qc = QuantumCircuit(qreg, creg, name='test')
        qc.h(0)
        qc.cx(0, 1)
        measure(qc, qreg, creg)

        qc_transpiled = transpile(qc, self.backend)
        qobj = assemble(qc_transpiled, self.backend)

        LOG.info(qobj)

    def test_retrieve_job_done(self):
        job_id = '52284ef5-1cf7-4182-9547-5bbc7c5dd9f5'
        job = self.backend.retrieve_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job.job_id(), job_id)
        self.assertEqual(job.status(), JobStatus.DONE)

    def test_retrieve_job_cancelled(self):
        job_id = '66b6a642-7db3-4134-8181-f7039b56fdfd'
        job = self.backend.retrieve_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job.job_id(), job_id)
        self.assertEqual(job.status(), JobStatus.CANCELLED)

    def test_run(self):
        creg = ClassicalRegister(2)
        qreg = QuantumRegister(2)
        qc = QuantumCircuit(qreg, creg, name='test')
        qc.h(0)
        qc.cx(0, 1)
        measure(qc, qreg, creg)

        qc_transpiled = transpile(qc, self.backend)
        qobj = assemble(qc_transpiled, self.backend, shots=1)

        extra_data = {
            'test': [
                'yes', 'is', 'there'
            ]
        }

        job = self.backend.run(qobj, extra_data=extra_data)
        LOG.info(job.job_id())

        self.assertIsNotNone(job)
        self.assertEqual(job.job_id(), qobj.qobj_id)
        self.assertTrue(job.status() in [JobStatus.INITIALIZING, JobStatus.QUEUED])
        while job.status() != JobStatus.QUEUED:
            time.sleep(1)
        job.cancel()
