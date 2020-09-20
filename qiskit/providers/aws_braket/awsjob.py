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
from collections import Counter
from datetime import datetime
from typing import List, Optional, Dict

from braket.aws import AwsQuantumTask
from braket.tasks import GateModelQuantumTaskResult
from qiskit.providers import BaseJob, JobStatus
from qiskit.qobj import QasmQobj, QasmQobjExperiment, QasmQobjInstruction
from qiskit.result import Result
from qiskit.result.models import ExperimentResult, ExperimentResultData

from . import awsbackend

logger = logging.getLogger(__name__)


def _reverse_and_map(bit_string: str, mapping: Dict[int, int]):
    result_bit_string = len(bit_string) * ['x']
    for i, c in enumerate(reversed(bit_string)):
        result_bit_string[mapping[i]] = c
    # qiskit is Little Endian, braket is Big Endian, so we don't do a re-reversed here
    result = "".join(reversed(result_bit_string))
    return result


def map_measurements(counts: Counter, qasm_experiment: QasmQobjExperiment) -> Dict[str, int]:
    # Need to get measure mapping
    instructions: List[QasmQobjInstruction] = [i for i in qasm_experiment.instructions if i.name == 'measure']
    mapping = dict([(q, m) for i in instructions for q, m in zip(i.qubits, i.memory)])
    mapped_counts = dict((_reverse_and_map(k, mapping)[::-1], v) for k, v in counts.items())  # must be reversed from Big Endian to Little Endian
    return mapped_counts


class AWSJob(BaseJob):

    _extra_data: dict
    _s3_bucket: str
    _qobj: QasmQobj
    _job_id: str
    _tasks: List[AwsQuantumTask]
    _backend: 'awsbackend.AWSBackend'

    def __init__(self, job_id: str, qobj: QasmQobj, backend: 'awsbackend.AWSBackend', tasks: List[AwsQuantumTask],
                 extra_data: Optional[dict] = None, s3_bucket: str = None) -> None:
        super().__init__(backend, job_id)
        self._tasks = tasks
        self._extra_data = extra_data
        self._date_of_creation = datetime.now()
        self._qobj = qobj
        self._job_id = job_id
        self._s3_bucket = s3_bucket

    @property
    def shots(self) -> int:
        return self._qobj.config.shots

    @property
    def extra_data(self) -> dict:
        return self._extra_data

    @property
    def date_of_creation(self) -> datetime:
        return self._date_of_creation

    @property
    def tasks(self) -> List[AwsQuantumTask]:
        return self._tasks

    def submit(self):
        logger.warning("job.submit() is deprecated. Please use AWSBackend.run() to submit a job.", DeprecationWarning, stacklevel=2)

    def result(self):
        experiment_results: List[ExperimentResult] = []
        task: AwsQuantumTask
        qasm_experiment: QasmQobjExperiment
        for task, qasm_experiment in zip(self._tasks, self._qobj.experiments):
            result: GateModelQuantumTaskResult = task.result()
            counts: Dict[str, int] = map_measurements(result.measurement_counts, qasm_experiment)
            data = ExperimentResultData(
                counts=dict(counts)
            )
            experiment_result = ExperimentResult(
                shots=self.shots,
                success=task.state() == 'COMPLETED',
                header=qasm_experiment.header,
                status=task.state(),
                data=data
            )
            experiment_results.append(experiment_result)
        qiskit_result = Result(
            backend_name=self._backend.name(),
            backend_version=self._backend.version(),
            qobj_id=self._qobj.qobj_id,
            job_id=self._job_id,
            success=self.status(),
            results=experiment_results
        )
        return qiskit_result

    def cancel(self):
        for task in self._tasks:
            try:
                task.cancel()
            except Exception as ex:
                logger.error(f"While cancelling Job {self.job_id()}, could not cancel task {task.id}. Reason: {ex}")

    def status(self):
        # FIXME: this is likely to change soon
        states = [t.state() for t in self._tasks]
        status: JobStatus = JobStatus.INITIALIZING
        if all([s == 'CREATED' for s in states]):
            status = JobStatus.INITIALIZING
        elif all([s == 'QUEUED' for s in states]):
            status = JobStatus.QUEUED
        elif any([s == 'RUNNING' for s in states]):
            status = JobStatus.RUNNING
        elif all([s == 'COMPLETED' for s in states]):
            status = JobStatus.DONE
        elif any([s == 'FAILED' for s in states]):
            status = JobStatus.ERROR
        elif any([s == 'CANCELLED' for s in states]):
            status = JobStatus.CANCELLED
        return status
