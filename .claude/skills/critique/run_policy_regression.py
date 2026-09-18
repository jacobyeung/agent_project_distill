#!/usr/bin/env python3
"""Behavioral regression test for the dual-critique policy."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


VERDICT_RE = re.compile(r"^## Verdict: (PASS|REVISE|REJECT)\s*$", re.MULTILINE)
CAP_EXPECTED = {
    "launch_allowed": False,
    "package_disposition": "NO_GO_LAUNCH_PACKAGE_ONLY",
    "mechanism_status": "UNTESTED",
    "add_to_tried_rejected": False,
    "fresh_gate_requires": "SUBSTANTIVE_REPAIR_OR_NEW_EVIDENCE",
}


def run_codex(
    prompt: str,
    output_path: Path,
    log_path: Path,
    repo: Path,
    model: str,
    effort: str,
) -> None:
    command = [
        "codex",
        "exec",
        "-m",
        model,
        "-c",
        f"model_reasoning_effort={effort}",
        "-s",
        "read-only",
        "--ephemeral",
        "-C",
        str(repo),
        "-o",
        str(output_path),
    ]
    completed = subprocess.run(
        command,
        cwd=repo,
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode:
        log_path.write_text(completed.stdout[-20_000:], encoding="utf-8")
        raise RuntimeError(f"codex exited {completed.returncode}; see {log_path}")


def parse_single_verdict(text: str) -> str:
    matches = VERDICT_RE.findall(text)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one verdict heading, found {matches}")
    return matches[0]


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("cap review emitted no JSON object")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("cap review output is not a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--model", default="gpt-6-astra")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent
    repo = skill_dir.parents[2]
    prompt_template = (skill_dir / "CRITIQUE_PROMPT.md").read_text(encoding="utf-8")
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    cases = json.loads(args.cases.resolve().read_text(encoding="utf-8"))

    output_path = args.out.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    runs_dir = output_path.parent / f"{output_path.stem}_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    def review_case(case: dict[str, str]) -> dict[str, Any]:
        case_id = case["id"]
        stipulated_brief = (
            "POLICY REGRESSION FIXTURE. Treat the following statements as stipulated verified "
            "facts solely for testing the verdict policy; do not search the repository to "
            "challenge the fixture facts.\n\n"
            + case["brief"]
        )
        prompt = prompt_template.replace("{IDEA_BRIEF}", stipulated_brief).replace(
            "{ROUND1_CONTEXT}", "None; independent synthetic policy fixture."
        )
        final_path = runs_dir / f"{case_id}.md"
        log_path = runs_dir / f"{case_id}.log"
        try:
            run_codex(prompt, final_path, log_path, repo, args.model, args.effort)
            actual = parse_single_verdict(final_path.read_text(encoding="utf-8"))
            error = None
        except Exception as exc:  # Report all fixture failures together.
            actual = None
            error = str(exc)
        return {
            "id": case_id,
            "expected": case["expected"],
            "actual": actual,
            "passed": actual == case["expected"],
            "error": error,
            "output": str(final_path.relative_to(repo)),
        }

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(review_case, case): case["id"] for case in cases}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["id"])

    cap_prompt = f"""Apply the following dual-critique skill exactly.

<skill>
{skill_text}
</skill>

Synthetic history: the same launch package received REVISE in rounds 1, 2, and 3. The remaining
issue is fixable missing mandatory provenance. The mechanism has never run and has no empirical
rejection. State the required terminal disposition.

Return only one JSON object with exactly these keys:
launch_allowed, package_disposition, mechanism_status, add_to_tried_rejected,
fresh_gate_requires.
Use only these enum values where applicable:
package_disposition = GO | NO_GO_LAUNCH_PACKAGE_ONLY | NO_GO_MECHANISM
mechanism_status = UNTESTED | EMPIRICALLY_REJECTED
fresh_gate_requires = NEVER | SUBSTANTIVE_REPAIR_OR_NEW_EVIDENCE.
"""
    cap_output = runs_dir / "cap_disposition.md"
    cap_log = runs_dir / "cap_disposition.log"
    try:
        run_codex(cap_prompt, cap_output, cap_log, repo, args.model, args.effort)
        cap_actual = parse_json_object(cap_output.read_text(encoding="utf-8"))
        cap_error = None
    except Exception as exc:
        cap_actual = None
        cap_error = str(exc)
    cap_passed = cap_actual == CAP_EXPECTED

    report = {
        "model": args.model,
        "effort": args.effort,
        "case_count": len(results),
        "cases": results,
        "cap_expected": CAP_EXPECTED,
        "cap_actual": cap_actual,
        "cap_passed": cap_passed,
        "cap_error": cap_error,
        "passed": all(item["passed"] for item in results) and cap_passed,
    }
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "out": str(output_path)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
