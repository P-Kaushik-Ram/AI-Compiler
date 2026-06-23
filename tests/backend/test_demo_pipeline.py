"""Unit tests verifying the developer demo script executes successfully."""
import pytest

from scripts.demo_pipeline import get_prompt, main


def test_main_with_cli_prompt_prints_all_stage_sections_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """main() given a CLI prompt should run the full RuntimeService pipeline and print every section."""
    exit_code = main(["Build a CRM where users can log in and manage contacts."])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "INPUT" in captured
    assert "STAGE 1 - Intent Extraction" in captured
    assert "STAGE 2 - System Design" in captured
    assert "STAGE 3 - Schema Generation" in captured
    assert "STAGE 4 - Validation" in captured
    assert "FINAL COMPILATION RESULT" in captured
    assert "succeeded" in captured


def test_main_handles_empty_prompt_without_raising(capsys: pytest.CaptureFixture[str]) -> None:
    """An empty prompt must cascade through every stage to a halted-but-well-formed result, not a crash."""
    exit_code = main([""])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "FINAL COMPILATION RESULT" in captured
    assert "halted" in captured


def test_main_without_prompt_falls_back_to_interactive_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """main() with no CLI prompt should fall back to input() and still complete successfully."""
    monkeypatch.setattr("builtins.input", lambda _prompt="": "Build a CRM where users can log in and manage contacts.")

    exit_code = main([])

    assert exit_code == 0
    assert "STAGE 4 - Validation" in capsys.readouterr().out


def test_get_prompt_returns_cli_value_without_calling_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_prompt should return the CLI-provided value directly, never calling input()."""
    monkeypatch.setattr("builtins.input", lambda _prompt="": (_ for _ in ()).throw(AssertionError("input() was called")))

    assert get_prompt("a provided prompt") == "a provided prompt"


def test_main_handles_keyboard_interrupt_during_interactive_input_gracefully(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """main() should catch a KeyboardInterrupt/EOFError during interactive input and return exit code 1."""

    def _raise_eof(_prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)

    exit_code = main([])

    assert exit_code == 1
    assert "Aborting" in capsys.readouterr().out
