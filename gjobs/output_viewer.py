import glob
import os
import signal
import subprocess
from typing import Tuple, Optional

from .util import LOG
from .parsing_bjobs import parse_run_time

# TODO: load and display job output while running
#   open the files and keep loading the data while available
#   or ideally run `less` in a subwindow?

N_PREVIEW_LINES = 15


class OutputViewer:
    LSBATCH_DIR = "/cluster/shadow/.lsbatch"

    def __init__(self):
        self.id_to_file = {}

    @staticmethod
    def _find_running_output_file(job_id):
        """Does not try to use cached results."""
        # LOG.append(f"Globbing for {job_id}")
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
        # See https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=execution-about-job-states
        # for info about job states

        if job["stat"] in ["RUN", "USUSP", "SSUSP"]:
            run_time = parse_run_time(job["run_time"])

            if run_time and run_time >= 10:
                return self.get_running_output_file(job["jobid"])
            else:
                # For the first few seconds of a job's runtime,
                # the file might not exist yet.
                return None
        elif job["stat"] in ["PEND", "PSUSP"]:
            return None
        elif job["stat"] in ["DONE", "EXIT"]:
            return self.get_finished_output_file(job)
        else:
            LOG.append(f'Unknown job status {job["stat"]}')
            return None

    def get_output_preview(
        self, job, n_preview_lines=N_PREVIEW_LINES
    ) -> Tuple[Optional[str], str]:
        if job is None:
            # Happens when there are no jobs at all.
            return None, "(no jobs)"

        output_file = self.get_output_file(job)
        if output_file is None:
            return None, f"(no output file available for job {job['jobid']})"

        try:
            with open(output_file, "rb") as f:
                output_preview = tail(f, lines=n_preview_lines)

            return output_file, output_preview
        except FileNotFoundError:
            return output_file, f"Couldn't find {output_file}"

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


def tail(f, lines=20):
    # https://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-similar-to-tail
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)  # seek to the end
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = []
    while lines_to_go > 0 and block_end_byte > 0:
        if block_end_byte - BLOCK_SIZE > 0:
            f.seek(block_number * BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # Can read the entirety of the file
            f.seek(0, 0)
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count(b"\n")
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = b"".join(reversed(blocks))

    res_bytes = b"\n".join(all_read_text.splitlines()[-total_lines_wanted:])
    return res_bytes.decode("utf-8", errors="replace")
