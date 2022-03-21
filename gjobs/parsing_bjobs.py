import subprocess
import re
import sys
import json

from .bjobs_fields import bjobs_fields

# These don't work on Euler for whatever reason
EXCLUDED_FIELDS = [
    "suspend_reason",
    "resume_reason",
    "kill_issue_host",
    "suspend_issue_host",
    "resume_issue_host",
    "ask_hosts",
]
DEFAULT_WIDTH = 50


def filter_fields(excluded):
    return [f for f in bjobs_fields if f["name"] not in excluded]


def make_command(excluded_fields):
    fields = filter_fields(excluded_fields)

    format = []
    for field in fields:
        width = field["width"] or DEFAULT_WIDTH
        format.append(f"{field['name']}:{width}")
        #
        # if field["width"]:
        #     format.append(f"{field['name']}:{field['width']}")
        # else:
        #     format.append(f"{field['name']}")

    format = " ".join(format)
    return ["bjobs", "-a", "-o", format, "-json"]


def run_bjobs():
    for i in range(50):
        cmd = make_command(EXCLUDED_FIELDS)

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr = res.stderr.decode("utf-8")

        if "not a valid field name" in stderr:
            match = re.search(r"<(.*)>", stderr)
            assert match is not None, f"unexpected error: {stderr}"

            bad_field = match.groups()[0]
            EXCLUDED_FIELDS.append(bad_field)

            # We can find excluded fields on the fly, but it's a bit wasteful.
            print(
                f"Excluding field {bad_field}, please update EXCLUDED_FIELDS",
                file=sys.stderr,
            )
        else:
            output = res.stdout.decode("utf-8")
            return output

    assert False, "Too many invalid fields or stuck in a loop"


def dict_keys_to_lowercase(d):
    items = []

    for k, v in d.items():
        try:
            k = k.lower()
        except AttributeError as e:
            raise ValueError(f"Dictionary contains non-string keys: {d}")

        items.append((k.lower(), v))

    return dict(items)


def parse_bjobs_output(raw_output):
    data = json.loads(raw_output)

    if data["JOBS"] == 0:
        return []

    jobs = [dict_keys_to_lowercase(job) for job in data["RECORDS"]]

    return jobs


def parse_bjobs():
    raw_output = run_bjobs()
    # print(raw_output)
    return parse_bjobs_output(raw_output)


def parse_run_time(run_time_string):
    """
    The field is job["run_time"].
    e.g.
    >>> parse_run_time("25 second(s)")
    25
    """

    match = re.match(r"([0-9]*) second\(s\)", run_time_string)
    if match:
        t = match.groups()[0]
        return int(t)
    else:
        return None


if __name__ == "__main__":
    jobs = parse_bjobs()
    print(jobs)
