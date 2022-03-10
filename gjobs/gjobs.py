import re
from typing import Optional
import datetime as dt
import subprocess

import humanize
import rich
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from blessed import Terminal

from gjobs.job_list import JobList
from .util import LOG
from .output_viewer import OutputViewer

term = Terminal()


def humanize_timedelta(seconds):
    return humanize.naturaldelta(dt.timedelta(seconds=int(seconds)))


def format_job_status(job):
    """Display the job status in a nice way."""
    if job["stat"] == "PEND":
        return f"[yellow]{humanize_timedelta(job['pend_time'])}"
    elif job["stat"] == "RUN":
        match = re.match(r"([0-9]*) second\(s\)", job["run_time"])
        if match:
            t = match.groups()[0]
            return f"[green]{humanize_timedelta(t)}"
        else:
            LOG.append(f"Could not parse run_time '{job['run_time']}'")
            return "[green]RUN"

    d = {"RUN": "[green]RUN", "EXIT": "[red]EXIT"}
    return d.get(job["stat"], job["stat"])


class JobTableCursor:
    def __init__(self):
        self.index = 0
        self.n_jobs = 0

    def update(self, jobs):
        self.n_jobs = len(jobs)
        return self.get_index()

    def get_index(self):
        if self.index >= self.n_jobs:
            self.index = self.n_jobs - 1
        self.index = max(0, self.index)

        return self.index

    def move_index(self, difference):
        self.index += difference
        self.get_index()  # to clamp

    def get_job(self, jobs) -> Optional[dict]:
        if self.index < len(jobs):
            return jobs[self.index]
        else:
            return None


def generate_job_table(jobs, cursor_index) -> Table:
    """Make a new table."""

    table = Table()
    table.add_column("ID")
    table.add_column("Submitted")
    table.add_column("Status")

    for i, job in enumerate(jobs):
        style = (
            rich.style.Style(bgcolor="rgb(100,100,100)") if i == cursor_index else None
        )

        table.add_row(
            job["jobid"],
            job["submit_time"],
            format_job_status(job),
            style=style,
        )

    return table


def main():
    cursor = JobTableCursor()
    output_viewer = OutputViewer()
    job_list = JobList()

    def update():
        # LOG.append( dt.datetime.now())
        jobs = job_list.get_jobs()

        cursor.update(jobs)

        log_panel = rich.panel.Panel("\n".join([str(x) for x in LOG[-10:]]))

        content_layout = Layout()
        content_layout.split_row(
            generate_job_table(jobs, cursor.get_index()),
            rich.align.Align(
                output_viewer.generate_view(cursor.get_job(jobs)),
                vertical="bottom",  # TODO: make this work
            ),
        )

        layout = Layout()
        layout.split_column(content_layout, log_panel)

        return layout

    with term.cbreak(), term.hidden_cursor():
        with Live(update(), refresh_per_second=8, screen=True) as live:
            input_key = None

            while (input_key or "").upper() != "Q":
                input_key = term.inkey(timeout=2)

                if input_key.code == term.KEY_UP:
                    cursor.move_index(-1)
                elif input_key.code == term.KEY_DOWN:
                    cursor.move_index(+1)
                elif input_key.upper() == "L":
                    LOG.append("L")
                    # TODO: make `less` work
                    live.stop()
                    subprocess.run(["less", "lsf.o207039063"])

                live.update(update())

                # time.sleep(0.4)

    live.console.print(LOG)


if __name__ == "__main__":
    main()
