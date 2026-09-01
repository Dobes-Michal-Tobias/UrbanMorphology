"""Incremental, crash-safe I/O helpers.

Convention (see principles.md): long-running loops (training, API calls,
data collection) must write each result to disk as it's produced, not just
at the end — so a crash/interrupt after N steps doesn't lose N steps of
work. Use `append_row_csv` for that, and `tqdm`/`iter_progress` for
progress bars around the loop.
"""

import csv
from pathlib import Path
from typing import Iterable, Sequence

from tqdm.auto import tqdm


def append_row_csv(path: Path, row: dict) -> None:
    """Append one row to a CSV, writing the header only if the file is new.

    Assumes every call for a given `path` uses the same set of keys.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def iter_progress(iterable: Iterable, desc: str = "", total: int | None = None):
    """Thin wrapper around tqdm so the whole project uses one progress-bar style."""
    return tqdm(iterable, desc=desc, total=total)


def already_done_ids(path: Path, id_column: str) -> set:
    """Read an existing results CSV and return the set of ids already processed.

    Useful to resume a long loop (training/inference/API calls) after a crash
    instead of redoing finished work.
    """
    path = Path(path)
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row[id_column] for row in reader}
