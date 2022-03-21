import os
import re

SEARCH_PATHS = [os.path.expanduser("~")]


def find_log_files(additional_search_paths=None):
    search_paths = SEARCH_PATHS
    if additional_search_paths:
        search_paths += additional_search_paths

    all_files = []

    for path in search_paths:
        files = [os.path.join(path, f) for f in os.listdir(path)]
        files = [f for f in files if re.match(r"lsf.o[0-9]*", f)]
        all_files += files

    return all_files
