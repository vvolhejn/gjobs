import os
import random

from . import parsing

SEARCH_PATHS = [os.path.expanduser("~")]


def job_fixtures():
    with open(
        os.path.join(os.path.dirname(__file__), "../bjobs_example_output.json")
    ) as f:
        res = parsing.parse_bjobs_output(f.read())
        res[0]["jobid"] = str(int(res[0]["jobid"]) + random.randint(0, 100))
        return res


class JobList:
    def __init__(self):
        self.search_paths = SEARCH_PATHS.copy()

    def get_jobs(self):

        running_jobs = parsing.parse_bjobs()
        # if running_jobs:
        # running_jobs += [running_jobs[0], running_jobs[0]]
        running_jobs += job_fixtures()

        jobs = running_jobs
        jobs.sort(key=lambda x: -int(x["jobid"]))
        return jobs
