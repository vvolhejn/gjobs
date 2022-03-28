import re
from typing import Optional
import datetime as dt
import functools

import humanize
import rich
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.highlighter import ReprHighlighter
from blessed import Terminal

from gjobs.job_list import JobList
from .util import LOG
from .output_viewer import OutputViewer, N_PREVIEW_LINES
from .parsing_bjobs import parse_run_time

term = Terminal()
DEBUG = False


def humanize_timedelta(seconds):
    return humanize.naturaldelta(dt.timedelta(seconds=int(seconds)))


def add_ellipsis_if_long(s, limit=30):
    if len(s) <= limit:
        return s
    else:
        return s[:limit] + "..."


def format_job_status(job):
    """Display the job status in a nice way."""
    if job["stat"] == "PEND":
        return f"⏳[yellow]{humanize_timedelta(job['pend_time'])}"
    elif job["stat"] == "RUN":
        run_time_seconds = parse_run_time(job["run_time"])

        if run_time_seconds is not None:
            return f"[green]{humanize_timedelta(run_time_seconds)}"
        else:
            LOG.append(f"Could not parse run_time '{job['run_time']}'")
            return "[green]RUN"

    d = {"RUN": "[green]RUN", "EXIT": "[red]EXIT", "DONE": "[white]DONE"}
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
    table.add_column("Name")

    for i, job in enumerate(jobs):
        style = rich.style.Style(bgcolor="rgb(60,60,60)") if i == cursor_index else None

        table.add_row(
            job["jobid"],
            job["submit_time"],
            format_job_status(job),
            add_ellipsis_if_long(job["job_name"]),
            style=style,
        )

    return table


echo = functools.partial(print, end="", flush=True)


def render_output_preview(output_preview, filename, region):
    """
    We get the exact number of preview lines we want, but some of them might be too long
    and get wrapped. In this case, the extra lines overflow at the bottom, but we want
    overflow at the top (and there seems to be no way to fix this natively in Rich).
    To fix this, we cut lines from the top until all lines fit.
    """
    console = rich.console.Console()

    lines = output_preview.split("\n")

    while True:
        if len(lines) == 1:
            # Do not remove the last line even if the line overflows.
            break

        # Subtract 2 from the width because of the panel's frame
        rendered_lines = console.render_lines(
            "\n".join(lines), console.options.update_width(region.width - 2)
        )

        if len(rendered_lines) <= region.height - 2:
            break
        else:
            del lines[0]

    panel = rich.panel.Panel(
        rich.align.Align(ReprHighlighter()("\n".join(lines))),
        title=filename,  # possibly None, in which case no title is used
    )

    return panel


def main():
    cursor = JobTableCursor()
    output_viewer = OutputViewer()
    job_list = JobList()

    def update():
        # LOG.append( dt.datetime.now())
        jobs = job_list.get_jobs()
        cursor.update(jobs)

        job_table_layout = rich.layout.Layout(size=10)
        output_preview_layout = rich.layout.Layout()
        content_layout = Layout()
        content_layout.split_column(job_table_layout, output_preview_layout)

        # Get the height of the output preview part.
        console = rich.console.Console()
        render_map = content_layout.render(console, console.options)
        output_preview_region = render_map[output_preview_layout].region

        filename, output_preview = output_viewer.get_output_preview(
            cursor.get_job(jobs), n_preview_lines=output_preview_region.height
        )

        job_table_layout.update(generate_job_table(jobs, cursor.get_index()))

        output_preview_layout.update(
            render_output_preview(output_preview, filename, output_preview_region)
        )

        if DEBUG:
            log_panel = rich.layout.Layout(
                rich.panel.Panel(
                    "\n".join([str(x) for x in LOG[-10:]]), title="Debug log"
                ),
                size=5 + 2,
            )
            layout = Layout()
            layout.split_column(content_layout, log_panel)
        else:
            layout = content_layout

        return layout

    with term.cbreak(), term.hidden_cursor():
        with Live(
            update(), refresh_per_second=8, screen=True, auto_refresh=False
        ) as live:
            input_key = None

            while (input_key or "").upper() != "Q":
                input_key = term.inkey(timeout=0.5)

                if input_key.code == term.KEY_UP:
                    cursor.move_index(-1)
                elif input_key.code == term.KEY_DOWN:
                    cursor.move_index(+1)
                elif input_key.upper() == "L":
                    # Open the output using `less`
                    current_job = cursor.get_job(job_list.get_jobs())
                    output_viewer.open_output_fullscreen(current_job)

                live.update(update())
                live.refresh()

                # time.sleep(0.4)

    live.console.print(LOG)


if __name__ == "__main__":
    main()
