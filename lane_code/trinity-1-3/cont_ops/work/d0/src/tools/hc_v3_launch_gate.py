#!/usr/bin/env python3
"""HC/HX launch rule on PDG v3's final heads (USER 2026-11-01): the held-out head gate of PDG v3's final export passes
at least 7 of its 9 checks, and no gated metric is worse than PDG v2's m400 report.

usage: hc_v3_launch_gate.py FINAL_REPORT M400_REPORT [--out DECISION.json]
Both reports are run_gate_eval_pdg.py outputs ({"checkpoint", "report": {"heads": {"checks", "summary"}}}).
Exit 0 = PASS (launch HC and HX), 3 = FAIL, 2 = unreadable input. Standard library only.
"""
import argparse
import hashlib
import json
import sys

# (check name, summary metric path, direction): lower is better unless "higher".
METRICS = (("call_refusals", ("call_refusals",), "lower"),
           ("rotation_deg_median", ("rotation_deg", "median"), "lower"),
           ("position_m_median", ("position_m", "median"), "lower"),
           ("heading_deg_median", ("heading_deg", "median"), "lower"),
           ("depth_abs_rel", ("depth_abs_rel",), "lower"),
           ("depth_delta125", ("depth_delta125",), "higher"),
           ("depth_abs_err_m_median", ("depth_abs_err_m", "median"), "lower"),
           ("decision_agreement", ("decision_agreement",), "higher"),
           ("row_decision_agreement", ("row_decision_agreement",), "higher"))
MIN_PASSED = 7


def metric(summary, path):
    value = summary
    for key in path:
        value = value[key]
    if not isinstance(value, (int, float)):
        raise ValueError(f"metric {'.'.join(path)} is {value!r}")
    return float(value)


def decide(final, reference):
    heads, ref = final["report"]["heads"], reference["report"]["heads"]
    checks = heads["checks"]
    if set(checks) != {name for name, _, _ in METRICS}:
        raise ValueError(f"unexpected gate checks {sorted(checks)}")
    if heads["summary"].get("rows") != ref["summary"].get("rows") or heads["summary"].get("scenes") != ref["summary"].get("scenes"):
        raise ValueError("the two reports scored different probe sets")
    passed = sorted(name for name, value in checks.items() if value is True)
    comparisons, worse = {}, []
    for name, path, direction in METRICS:
        new, old = metric(heads["summary"], path), metric(ref["summary"], path)
        bad = new > old if direction == "lower" else new < old
        comparisons[name] = {"final": new, "pdg_v2_m400": old, "better_is": direction, "worse": bad}
        if bad:
            worse.append(name)
    verdict = "PASS" if len(passed) >= MIN_PASSED and not worse else "FAIL"
    return {"schema": "hc-v3-launch-gate-v1", "verdict": verdict, "rule": "checks passed >= 7 of 9 and no gated metric "
            "worse than PDG v2 m400 (USER 2026-11-01)", "checks_passed": len(passed), "passed": passed,
            "failed_checks": sorted(set(checks) - set(passed)), "worse_than_m400": worse, "metrics": comparisons,
            "final_checkpoint": final.get("checkpoint"), "rows": heads["summary"].get("rows")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("final")
    parser.add_argument("reference")
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        raw = {name: open(path, "rb").read() for name, path in (("final", args.final), ("reference", args.reference))}
        result = decide(json.loads(raw["final"]), json.loads(raw["reference"]))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"UNREADABLE {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    result["inputs"] = {name: {"path": path, "sha256": hashlib.sha256(raw[name]).hexdigest()}
                        for name, path in (("final", args.final), ("reference", args.reference))}
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if args.out:
        with open(args.out, "x") as handle:
            handle.write(text)
    print(text, end="")
    return 0 if result["verdict"] == "PASS" else 3


if __name__ == "__main__":
    sys.exit(main())
