import glob
import os

from .util import LOG

# TODO: load and display job output while running
#   open the files and keep loading the data while available
#   or ideally run `less` in a subwindow?


class OutputViewer:
    LSBATCH_DIR = "/cluster/shadow/.lsbatch"

    def __init__(self):
        self.id_to_file = {}

    @staticmethod
    def _find_running_output_file(job_id):
        """Does not try to use cached results."""
        LOG.append(f"Globbing for {job_id}")
        candidates = glob.glob(f"/cluster/shadow/.lsbatch/*{job_id}.out")
        if len(candidates) > 1:
            LOG.append(f"Warning: more than one output file found? {candidates}")

        if candidates:
            return candidates[0]
        else:
            return None

    def get_running_output_file(self, job_id):
        if job_id in self.id_to_file:
            # This can also be None, if we've tried to find this before and didn't succeed
            return self.id_to_file[job_id]
        else:
            res = self._find_running_output_file(job_id)
            # again - possibly None!
            self.id_to_file[job_id] = res

            return res

    def get_finished_output_file(self, job):
        if job.get("exec_cwd") and job.get("output_file"):
            return os.path.join(job["exec_cwd"], job["output_file"])
        else:
            return None

    def get_output_file(self, job):
        if job["stat"] == "RUN":
            return self.get_running_output_file(job["jobid"])
        elif job["stat"] == "PEND":
            return None
        elif job["stat"] in ["DONE", "EXIT"]:
            return self.get_finished_output_file(job)
        else:
            LOG.append(f'Unknown job status {job["stat"]}')
            return None

    def generate_view(self, job):
        output_file = self.get_output_file(job)
        if output_file is None:
            return "(no file to view)"

        try:
            with open(output_file) as f:
                head = []
                for i in range(50):
                    try:
                        head.append(next(f))
                    except StopIteration:
                        break

            head_joined = "".join(head)

            return f"{output_file}:\n{head_joined}"
        except FileNotFoundError:
            return f"Couldn't find file {output_file}"
