import os
import random
import datetime

from . import parsing_bjobs, parsing_logs
from .util import PeriodicTimer, LOG


def job_fixtures():
    with open(
        os.path.join(os.path.dirname(__file__), "../bjobs_example_output.json")
    ) as f:
        res = parsing_bjobs.parse_bjobs_output(f.read())
        res[0]["jobid"] = str(int(res[0]["jobid"]) + random.randint(0, 100))
        return res


class JobList:
    def __init__(self):
        self.bjobs_timer = PeriodicTimer(datetime.timedelta(seconds=5))
        self.running_jobs = []

    def get_jobs(self):
        if self.bjobs_timer.should_do_now():
            self.running_jobs = parsing_bjobs.parse_bjobs()

        # if running_jobs:
        # running_jobs += [running_jobs[0], running_jobs[0]]

        jobs = self.running_jobs
        # jobs += job_fixtures()

        jobs.sort(key=lambda x: -int(x["jobid"]))
        return jobs
