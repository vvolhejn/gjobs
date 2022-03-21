import glob
import os
import signal
import subprocess

from .util import LOG
from .parsing_bjobs import parse_run_time

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
            run_time =  parse_run_time(job["run_time"])

            if run_time and run_time >= 10:
                return self.get_running_output_file(job["jobid"])
            else:
                # For the first few seconds of a job's runtime,
                # the file might not exist yet.
                return None
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

    def open_output_fullscreen(self, job):
        output_file = self.get_output_file(job)
        if output_file:
            old_action = signal.signal(signal.SIGINT, signal.SIG_IGN)

            command = ["less", "-r"]

            if job["stat"] == "RUN":
                # Tail the file (wait for incoming data) if the job is still running
                command.append("+F")
            else:
                # Jump to the end.
                command.append("+G")

            subprocess.run(command + [output_file])
            signal.signal(signal.SIGINT, old_action)
