import time
import traceback
from threading import Thread
from typing import Dict

from PyQt5.QtCore import QThread, pyqtSignal

from utils.logger import logger


class JobThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, target, args, callback):
        super().__init__()
        self.target = target
        self.args = args
        self.finished.connect(callback)
        self.name = f"Job-{hash(self)}*{int(time.mktime(time.localtime()))}"

    def run(self):
        result = self.target(*self.args)
        self.finished.emit(result)


class AsyncJobPool:
    def __init__(self):
        self.jobs: Dict[str, JobThread] = {}
        self.monitor_thread = Thread(target=self.monitor_jobs)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def add_job(self, target, args, callback):
        new_job = JobThread(target, args, callback)
        new_job.start()
        self.jobs[new_job.name] = new_job
        return new_job.name

    def remove_job(self, job_name):
        try:
            job = self.jobs.pop(job_name, None)
            if job is not None:
                job.terminate()
        except Exception as e:
            logger.error(f"Error removing job: {e}")
            logger.error(traceback.print_exc())
            return False
        return True

    def monitor_jobs(self):
        while True:
            time.sleep(5)
            finished_jobs = []
            for name, thread in self.jobs.items():
                if thread.isFinished():
                    finished_jobs.append(name)
            for name in finished_jobs:
                self.remove_job(name)
