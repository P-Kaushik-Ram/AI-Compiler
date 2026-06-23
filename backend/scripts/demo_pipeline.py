"""Developer demo: run a prompt through the complete compiler pipeline via RuntimeService.

This script does not implement any compiler or orchestration logic itself — it only calls
the existing ``RuntimeService.run()`` and prints its output, so it can never drift from the
real pipeline behavior. It displays a summary for each of the four stages RuntimeService
orchestrates (Intent Extraction, System Design, Schema Generation, Validation) followed by
the final CompilationResult.

Usage:
    python backend/scripts/demo_pipeline.py "Build a CRM with login and contacts."
    python backend/scripts/demo_pipeline.py        # prompts interactively
"""
import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from pydantic import BaseModel  # noqa: E402

from app.models.runtime import CompilationResult, StageSummary  # noqa: E402
from app.services.runtime import RuntimeService  # noqa: E402

try:
    from rich.console import Console
    from rich.pretty import Pretty

    _console: "Console | None" = Console()
except ImportError:
    _console = None

SECTION_WIDTH = 34

STAGE_TITLES: dict[str, str] = {
    "intent_extraction": "STAGE 1 - Intent Extraction",
    "system_design": "STAGE 2 - System Design",
    "schema_generation": "STAGE 3 - Schema Generation",
    "validation": "STAGE 4 - Validation",
}


def print_section(title: str, content: object | None = None) -> None:
    """Print a banner-delimited section with an optional pretty-printed body.

    Uses ``rich`` for colorized, structured output when it is installed; otherwise
    falls back to plain indented JSON so the script works with zero extra dependencies.
    """
    banner = "=" * SECTION_WIDTH
    if isinstance(content, BaseModel):
        content = content.model_dump()

    if _console is not None:
        _console.print(banner)
        _console.print(title)
        _console.print(banner)
        if isinstance(content, dict):
            _console.print(Pretty(content))
        elif content is not None:
            _console.print(content)
    else:
        print(banner)
        print(title)
        print(banner)
        if isinstance(content, dict):
            print(json.dumps(content, indent=2, default=str))
        elif content is not None:
            print(content)
    print()


def format_stage_summary(summary: StageSummary) -> dict[str, object]:
    """Reduce a StageSummary to the handful of fields worth showing a developer at a glance."""
    return {
        "status": summary.status,
        "confidence": summary.confidence,
        "duration_ms": summary.duration_ms,
        "summary": summary.summary,
    }


def format_final_result(result: CompilationResult) -> dict[str, object]:
    """Reduce a CompilationResult to its top-level outcome, omitting the (already-shown) artifacts."""
    return {
        "compilation_id": result.compilation_id,
        "overall_status": result.overall_status,
        "final_decision": result.final_decision,
        "total_duration_ms": result.total_duration_ms,
        "error": result.error,
    }


def get_prompt(provided_prompt: str | None) -> str:
    """Return the prompt to run: the CLI-provided value if given, otherwise interactive input."""
    if provided_prompt is not None:
        return provided_prompt
    return input("Enter a prompt describing the system you want to build: ")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the demo script."""
    parser = argparse.ArgumentParser(
        description="Run a prompt through the full compiler pipeline (Intent Extraction, "
        "System Design, Schema Generation, and Validation) via RuntimeService."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="The natural-language prompt to compile. If omitted, you will be prompted interactively.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse arguments, run the full pipeline via RuntimeService, and print each section.

    Returns 0 whenever RuntimeService produces a result at all (including 'halted' outcomes,
    e.g. for an empty or vague prompt — those are valid pipeline outcomes, not script errors)
    and 1 if interactive input fails or RuntimeService itself reports overall_status='errored'.
    """
    args = build_arg_parser().parse_args(argv)

    try:
        prompt = get_prompt(args.prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nNo prompt provided. Aborting.")
        return 1

    print_section("INPUT", prompt if prompt else "(empty prompt)")

    result = RuntimeService().run(prompt=prompt)

    for stage_summary in result.stage_summaries:
        title = STAGE_TITLES.get(stage_summary.stage_name, stage_summary.stage_name)
        print_section(title, format_stage_summary(stage_summary))

    print_section("FINAL COMPILATION RESULT", format_final_result(result))

    return 1 if result.overall_status == "errored" else 0


if __name__ == "__main__":
    sys.exit(main())
