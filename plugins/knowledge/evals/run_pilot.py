"""Run one native plugin evaluation case after an explicit --run.

Without --run, print the command only. Keep reports local and out of git.
The pilot checks the measurement setup; it is not a benchmark refresh.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from child_environment import child_environment, claude_command, settings_record

PLUGIN = Path(__file__).resolve().parents[1]


def command(executable: str, output: Path, claude_defaults: bool = False) -> list[str]:
    return claude_command(executable, claude_defaults) + [
        "plugin", "eval", str(PLUGIN),
        "--case", "pilot-fee-correction", "--runs", "1", "--ablation", "none",
        "--model", "sonnet", "--judge-model", "opus",
        "--scaffold", "--trust-plugin", "--no-publish", "--keep-temp",
        "--output-dir", str(output), "--json", str(output / "aggregate-result.json"),
        "--allow-tools", "Bash",
    ]


def preserve_traces(output: Path) -> None:
    """Copy native traces as data before temporary run folders are removed."""
    report_path = output / "aggregate-result.json"
    if not report_path.is_file():
        return
    from transcripts import preserve
    preserve(report_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Start one live case, with model grading.")
    parser.add_argument("--help-cli", action="store_true", help="Read native CLI help; start no model.")
    parser.add_argument("--claude-defaults", action="store_true",
                        help="Ignore settings files and inherited model, provider, and API credentials in child processes.")
    parser.add_argument("--output", type=Path, default=PLUGIN / "evals/results/pilot")
    args = parser.parse_args()
    executable = shutil.which("claude")
    if not executable:
        parser.error("Install Claude Code before running this command.")
    env = child_environment(args.claude_defaults)
    if args.help_cli:
        return subprocess.run(claude_command(executable, args.claude_defaults) + ["plugin", "eval", "--help"],
                              env=env, check=False).returncode
    output = args.output.resolve()
    argv = command(executable, output, args.claude_defaults)
    if not args.run:
        print(json.dumps(argv, indent=2))
        return 0
    # A prior result is evidence. Each attempt gets a fresh directory.
    output.mkdir(parents=True, exist_ok=False)
    (output / "experiment.json").write_text(json.dumps(settings_record(args.claude_defaults), indent=2) + "\n")
    with (output / "stdout.txt").open("w") as stdout, (output / "stderr.txt").open("w") as stderr:
        try:
            result = subprocess.run(argv, env=env, stdout=stdout, stderr=stderr, timeout=600, check=False)
        except subprocess.TimeoutExpired:
            print(f"Pilot timed out. Read {output / 'stderr.txt'}", file=sys.stderr)
            return 1
    preserve_traces(output)
    print(f"Pilot exit code: {result.returncode}. Results: {output}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
