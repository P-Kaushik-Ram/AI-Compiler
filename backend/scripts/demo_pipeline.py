"""Developer demo: run a prompt through Stage 1 (Intent Extraction) and Stage 2 (System Design).

This script does not implement any compiler logic itself — it only calls the existing
``IntentExtractionService`` and ``SystemDesignService`` directly and pretty-prints their
output, so it can never drift from the real pipeline behavior.

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

from app.models.intent import IntentIR  # noqa: E402
from app.models.system_design import SystemDesign  # noqa: E402
from app.services.intent_extraction import IntentExtractionService  # noqa: E402
from app.services.system_design import SystemDesignService  # noqa: E402

try:
    from rich.console import Console
    from rich.pretty import Pretty

    _console: "Console | None" = Console()
except ImportError:
    _console = None

SECTION_WIDTH = 34


def print_section(title: str, content: object | None = None) -> None:
    """Print a banner-delimited section with an optional pretty-printed body.

    Uses ``rich`` for colorized, structured output when it is installed; otherwise
    falls back to plain indented JSON so the script works with zero extra dependencies.
    """
    banner = "=" * SECTION_WIDTH
    if _console is not None:
        _console.print(banner)
        _console.print(title)
        _console.print(banner)
        if isinstance(content, (IntentIR, SystemDesign)):
            _console.print(Pretty(content.model_dump()))
        elif content is not None:
            _console.print(content)
    else:
        print(banner)
        print(title)
        print(banner)
        if isinstance(content, (IntentIR, SystemDesign)):
            print(json.dumps(content.model_dump(), indent=2, default=str))
        elif content is not None:
            print(content)
    print()


def get_prompt(provided_prompt: str | None) -> str:
    """Return the prompt to run: the CLI-provided value if given, otherwise interactive input."""
    if provided_prompt is not None:
        return provided_prompt
    return input("Enter a prompt describing the system you want to build: ")


def run_pipeline(prompt: str) -> tuple[IntentIR, SystemDesign]:
    """Run the prompt through Stage 1 and Stage 2 in sequence and return both results."""
    intent_ir = IntentExtractionService().extract(prompt)
    system_design = SystemDesignService().build(intent_ir)
    return intent_ir, system_design


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the demo script."""
    parser = argparse.ArgumentParser(
        description="Run a prompt through the Intent Extraction and System Design compiler stages."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="The natural-language prompt to compile. If omitted, you will be prompted interactively.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse arguments, run the pipeline, and print each stage's output.

    Returns 0 on a successful run (regardless of whether the IR or design ended up
    'complete', 'needs_clarification', or 'rejected' — those are valid outcomes, not
    errors) and 1 if an unexpected error or interactive input failure occurs.
    """
    args = build_arg_parser().parse_args(argv)

    try:
        prompt = get_prompt(args.prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nNo prompt provided. Aborting.")
        return 1

    print_section("INPUT", prompt if prompt else "(empty prompt)")

    try:
        intent_ir, system_design = run_pipeline(prompt)
    except Exception as exc:  # noqa: BLE001 - surface any pipeline failure as a clean message
        print_section("ERROR", f"The pipeline failed unexpectedly: {exc}")
        return 1

    print_section("STAGE 1 - Intent Extraction", intent_ir)
    print_section("STAGE 2 - System Design", system_design)
    return 0


if __name__ == "__main__":
    sys.exit(main())
