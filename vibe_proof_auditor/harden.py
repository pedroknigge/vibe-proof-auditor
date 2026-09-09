#!/usr/bin/env python3
"""Autonomous Remediation (v1.0.1): Run the audit remediation loop through a chosen harness (`agy`, `grok`, `claude`, `cursor`).

Executes closed-loop remediation where the agent writes tests, patches code, and verifies execution autonomously.

Extracts the fenced Remediation Prompt from a vibe-proof report and either
prints the command for the chosen adapter or executes it. Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from vibe_proof_auditor.scorelib import VERSION

PROMPT_HEADING = "## Remediation Prompt"

def extract_remediation_prompt(markdown: str) -> str:
    lines = markdown.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(PROMPT_HEADING):
            start = i + 1
            break
    if start is None:
        raise ValueError(f"no `{PROMPT_HEADING}` section found — run an audit first")

    fence_open = None
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            fence_open = i + 1
            break
    if fence_open is None:
        raise ValueError("Remediation Prompt section has no fenced code block")

    body: list[str] = []
    for i in range(fence_open, len(lines)):
        if lines[i].strip().startswith("```"):
            text = "\n".join(body).strip()
            if not text:
                raise ValueError("Remediation Prompt fence is empty")
            return text
        body.append(lines[i])
    raise ValueError("Remediation Prompt fence never closed")

def build_adapter_argv(
    adapter: str,
    prompt: str,
    *,
    project: Path,
    model: str | None,
    effort: str | None,
    skip_permissions: bool,
) -> list[str]:
    if adapter == "agy":
        argv = ["agy", "--print", "--add-dir", str(project.resolve())]
        if model:
            argv.extend(["--model", model])
        if effort:
            argv.extend(["--effort", effort])
        if skip_permissions:
            argv.append("--dangerously-skip-permissions")
        argv.append(prompt)
        return argv
    elif adapter == "grok":
        argv = ["grok", "-p", prompt, "--cwd", str(project.resolve()), "--always-approve", "--no-auto-update"]
        if model:
            argv.extend(["--model", model])
        return argv
    elif adapter == "claude":
        argv = ["claude", "-p", prompt, "--cwd", str(project.resolve()), "--acceptEdits"]
        if model:
            argv.extend(["--model", model])
        return argv
    elif adapter == "cursor":
        argv = ["cursor-agent", "-p", prompt, "--cwd", str(project.resolve()), "--mode", "auto-edit"]
        if model:
            argv.extend(["--model", model])
        return argv
    else:
        raise ValueError(f"Unknown adapter: {adapter}")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Harden a repo using the vibe-proof remediation prompt via a chosen AI adapter."
    )
    parser.add_argument(
        "report",
        type=Path,
        help="Path to vibe-proof-audit-report.md",
    )
    parser.add_argument(
        "--adapter",
        default="agy",
        choices=("agy", "grok", "claude", "cursor"),
        help="The harness to execute the agentic CI loop (default: agy)",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Repo root for --add-dir (default: report parent directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command; do not execute",
    )
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print only the extracted remediation prompt",
    )
    parser.add_argument("--model", default=None, help="Pass through model flag")
    parser.add_argument(
        "--effort",
        default=None,
        choices=("low", "medium", "high"),
        help="Pass through to agy --effort",
    )
    parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Pass through to agy (off by default)",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)

    report = args.report.expanduser().resolve()
    if not report.is_file():
        print(f"error: report not found: {report}", file=sys.stderr)
        return 1

    try:
        prompt = extract_remediation_prompt(report.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.print_prompt:
        print(prompt)
        return 0

    project = (args.project or report.parent).expanduser().resolve()
    if not project.is_dir():
        print(f"error: project dir not found: {project}", file=sys.stderr)
        return 1

    adapter = args.adapter
    binary = "cursor-agent" if adapter == "cursor" else adapter
    exe = shutil.which(binary)
    if exe is None:
        print(f"error: `{binary}` not on PATH. Install {adapter} CLI, then re-run.\\nFallback: copy the Remediation Prompt from the report into any agent.", file=sys.stderr)
        return 1

    argv_cmd = build_adapter_argv(
        adapter,
        prompt,
        project=project,
        model=args.model,
        effort=args.effort,
        skip_permissions=args.dangerously_skip_permissions,
    )

    if args.dry_run:
        preview = " ".join(argv_cmd[:-1]) + f" <<PROMPT ({len(prompt)} chars)"
        print(preview)
        print(prompt)
        print("PROMPT")
        return 0

    env = os.environ.copy()
    print(f"harden via {args.adapter} → {project}", file=sys.stderr)
    proc = subprocess.run(argv_cmd, cwd=str(project), env=env, check=False)
    return int(proc.returncode)

if __name__ == "__main__":
    raise SystemExit(main())

