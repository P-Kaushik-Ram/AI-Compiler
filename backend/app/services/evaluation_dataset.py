"""Streaming JSONL dataset loading for the Evaluation Framework.

Every function here is lazy: parsing one line, or one file, never requires the rest of the
dataset to be in memory. A malformed line yields a ``DatasetError`` instead of raising, so one
bad row never aborts an otherwise-valid dataset stream.
"""
import json
from pathlib import Path
from typing import Iterable, Iterator, TextIO

from pydantic import ValidationError

from app.models.evaluation import DatasetCase, DatasetError


def parse_dataset_line(line: str, line_number: int) -> DatasetCase | DatasetError:
    """Parse one JSONL line into a DatasetCase, or a DatasetError if it is blank or malformed."""
    stripped = line.strip()
    if not stripped:
        return DatasetError(case_id=None, raw_line_number=line_number, error="Blank line.")

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return DatasetError(case_id=None, raw_line_number=line_number, error=f"Invalid JSON: {exc}")

    try:
        return DatasetCase.model_validate(payload)
    except ValidationError as exc:
        case_id = payload.get("case_id") if isinstance(payload, dict) else None
        return DatasetError(case_id=case_id, raw_line_number=line_number, error=f"Invalid DatasetCase: {exc}")


def iter_dataset_cases(lines: Iterable[str]) -> Iterator[DatasetCase | DatasetError]:
    """Lazily parse an iterable of JSONL lines into DatasetCase/DatasetError items, one at a time."""
    for line_number, line in enumerate(lines, start=1):
        yield parse_dataset_line(line, line_number)


def open_dataset_file(path: str | Path) -> TextIO:
    """Open a JSONL dataset file for streaming line-by-line reading.

    Raises OSError immediately (at call time) if the file cannot be opened, so a caller that
    wants to handle that failure gracefully (e.g. EvaluationService.run_benchmark_from_path)
    can wrap just this call, rather than the failure being deferred to first iteration.
    """
    return open(path, "r", encoding="utf-8")


def _drain_and_close(file_handle: TextIO) -> Iterator[DatasetCase | DatasetError]:
    """Yield parsed items from an already-open file handle, closing it once exhausted or abandoned."""
    try:
        yield from iter_dataset_cases(file_handle)
    finally:
        file_handle.close()


def iter_dataset_cases_from_path(path: str | Path) -> Iterator[DatasetCase | DatasetError]:
    """Open a JSONL file eagerly and lazily yield parsed DatasetCase/DatasetError items.

    The file is opened immediately (raising OSError here if it cannot be), then streamed and
    closed automatically once the returned iterator is exhausted.
    """
    file_handle = open_dataset_file(path)
    return _drain_and_close(file_handle)
