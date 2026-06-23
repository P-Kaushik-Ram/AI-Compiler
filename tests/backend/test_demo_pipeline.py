"""Unit tests verifying the developer demo script executes successfully."""
import pytest

from scripts.demo_pipeline import get_prompt, main, run_pipeline


def test_run_pipeline_returns_complete_ir_and_design_for_valid_prompt() -> None:
    """run_pipeline should return a complete IntentIR and a complete SystemDesign for a clear prompt."""
    intent_ir, system_design = run_pipeline("Build a CRM where users can log in and manage contacts.")

    assert intent_ir.status == "complete"
    assert system_design.status == "complete"
    assert system_design.source_intent_id == intent_ir.intent_id


def test_run_pipeline_handles_empty_prompt_without_raising() -> None:
    """run_pipeline must not raise on an empty prompt; it should propagate Stage 1's rejection gracefully."""
    intent_ir, system_design = run_pipeline("")

    assert intent_ir.status == "rejected"
    assert system_design.status == "rejected"


def test_main_with_cli_prompt_prints_all_sections_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """main() given a CLI prompt should print all three sections and return exit code 0."""
    exit_code = main(["Build a CRM where users can log in and manage contacts."])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "INPUT" in captured
    assert "STAGE 1 - Intent Extraction" in captured
    assert "STAGE 2 - System Design" in captured


def test_main_without_prompt_falls_back_to_interactive_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """main() with no CLI prompt should fall back to input() and still complete successfully."""
    monkeypatch.setattr("builtins.input", lambda _prompt="": "Build a CRM where users can log in and manage contacts.")

    exit_code = main([])

    assert exit_code == 0
    assert "STAGE 2 - System Design" in capsys.readouterr().out


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
