"""Unit tests for the streaming JSONL dataset loader."""
import pytest

from app.models.evaluation import DatasetCase, DatasetError
from app.services.evaluation_dataset import (
    iter_dataset_cases,
    iter_dataset_cases_from_path,
    parse_dataset_line,
)


def test_parse_dataset_line_returns_a_dataset_case_for_valid_json() -> None:
    """A well-formed JSONL line should parse into a DatasetCase."""
    line = '{"case_id": "c1", "prompt": "Build a CRM.", "category": "crm"}'

    result = parse_dataset_line(line, line_number=1)

    assert isinstance(result, DatasetCase)
    assert result.case_id == "c1"
    assert result.category == "crm"


def test_parse_dataset_line_returns_dataset_error_for_invalid_json() -> None:
    """A line that isn't valid JSON at all should produce a DatasetError, not raise."""
    result = parse_dataset_line("{not valid json", line_number=3)

    assert isinstance(result, DatasetError)
    assert result.raw_line_number == 3
    assert "Invalid JSON" in result.error


def test_parse_dataset_line_returns_dataset_error_for_schema_violation() -> None:
    """Valid JSON that doesn't satisfy DatasetCase's required fields should produce a DatasetError."""
    line = '{"case_id": "c2"}'  # missing required "prompt"

    result = parse_dataset_line(line, line_number=5)

    assert isinstance(result, DatasetError)
    assert result.case_id == "c2"
    assert result.raw_line_number == 5


def test_parse_dataset_line_treats_a_blank_line_as_a_dataset_error() -> None:
    """A blank line should be reported as a DatasetError rather than silently skipped or crashing."""
    result = parse_dataset_line("   \n", line_number=2)

    assert isinstance(result, DatasetError)
    assert "Blank line" in result.error


def test_iter_dataset_cases_yields_one_item_per_line_lazily() -> None:
    """iter_dataset_cases should yield a mix of DatasetCase and DatasetError, one per input line."""
    lines = [
        '{"case_id": "c1", "prompt": "Build a CRM."}',
        "not json",
        '{"case_id": "c2", "prompt": "Build a to-do app."}',
    ]

    results = list(iter_dataset_cases(lines))

    assert isinstance(results[0], DatasetCase)
    assert isinstance(results[1], DatasetError)
    assert isinstance(results[2], DatasetCase)
    assert results[1].raw_line_number == 2


def test_iter_dataset_cases_from_path_streams_a_real_file(tmp_path) -> None:
    """Loading from an actual JSONL file on disk should yield the same parsed items as in-memory lines."""
    dataset_file = tmp_path / "dataset.jsonl"
    dataset_file.write_text(
        '{"case_id": "c1", "prompt": "Build a CRM."}\n{"case_id": "c2", "prompt": "Build a shop."}\n',
        encoding="utf-8",
    )

    results = list(iter_dataset_cases_from_path(dataset_file))

    assert len(results) == 2
    assert all(isinstance(item, DatasetCase) for item in results)
    assert [item.case_id for item in results] == ["c1", "c2"]


def test_iter_dataset_cases_from_path_raises_immediately_for_a_missing_file(tmp_path) -> None:
    """Opening a nonexistent dataset file should raise OSError at call time, not on first iteration."""
    missing_path = tmp_path / "does_not_exist.jsonl"

    with pytest.raises(OSError):
        iter_dataset_cases_from_path(missing_path)
