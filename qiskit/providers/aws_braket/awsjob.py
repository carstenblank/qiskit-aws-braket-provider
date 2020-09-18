import logging
from datetime import datetime
from typing import List, Optional

from braket.aws import AwsQuantumTask
from braket.tasks import GateModelQuantumTaskResult
from qiskit.providers import BaseJob, JobStatus
from qiskit.qobj import QasmQobj
from qiskit.result import Result
from qiskit.result.models import ExperimentResult, ExperimentResultData

from . import awsbackend

logger = logging.getLogger(__name__)


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
        result: GateModelQuantumTaskResult = self._task.result()
        counts = result.measurement_counts
        # Must interpret the measurement here
        # self._qasm_experiment
        data = ExperimentResultData(
            counts=dict(counts)
        )
        experiment_results: List[ExperimentResult] = [
            ExperimentResult(
                shots=self.shots,
                success=self._task.state() == '',  # TODO
                header=self._qasm_experiment.header,
                status=self._task.state(),
                data=data
            )
        ]
        qiskit_result = Result(
            backend_name=self._backend.name(),
            backend_version=self._backend.version(),
            qobj_id='',
            job_id=self._job_id,
            success=self._task.state() == '',  # TODO
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
