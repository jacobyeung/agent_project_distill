"""Write offline, additive tolerance diagnostics without changing census decisions."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

# Imports must never create bytecode in the sealed collector.
sys.dont_write_bytecode = True
TIERS = (10, 15, 25)
OUTPUT_NAMES = ("TOLERANCE_TIERS.json", "TOLERANCE_SUMMARY.md")
DEFAULT_REPO = Path("/home/jjyeung/agent_project_distill")
CENSUS_ROOT = Path("/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/census_r1313")
CENSUS_LOADER_SHA256 = "2527836cbfe9e9615e5ba97fdc44f47bc25f7a50ed12fad5f1d2e12b0af43af4"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def import_census(repo):
    collector = repo.resolve() / "collector"
    sys.path.insert(0, str(collector))
    spec = importlib.util.spec_from_file_location("tolerance_census", collector / "census.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_census_inputs(census, census_dir):
    """Stop the sanctioned census immediately after its inline label loader.

    census.py:280-283 loads answer-free membership, verifies the label digest,
    and loads labels. There is no standalone loader. Trace only this frame and
    stop before baseline processing, attempt traversal, or any output writes.
    No label-reading implementation or label file is copied into this tool.
    """
    if digest(Path(census.__file__).read_bytes()) != CENSUS_LOADER_SHA256:
        raise ValueError("census loader source changed; review its read-only stopping point")
    captured = {}

    class InputsLoaded(Exception):
        pass

    def capture(frame, event, arg):
        if frame.f_code is census.census.__code__:
            if event == "line" and "gold" in frame.f_locals:
                captured.update(rows=frame.f_locals["rows"], gold=frame.f_locals["gold"])
                raise InputsLoaded
            return capture
        return None

    previous = sys.gettrace()
    try:
        sys.settrace(capture)
        census.census(census_dir, census_dir)
    except InputsLoaded:
        return captured["rows"], captured["gold"]
    finally:
        sys.settrace(previous)
    raise ValueError("census inline loader could not be intercepted")


def relative_error(census, row, gold, answer):
    """Use grade() itself to parse numbers and validate units (lines 45-61)."""
    parsed = {}

    def capture(frame, event, arg):
        if event == "return" and frame.f_code is census.grade.__code__:
            parsed.update(frame.f_locals)

    previous = sys.getprofile()
    try:
        sys.setprofile(capture)
        _, reason = census.grade(row, gold, answer)
    finally:
        sys.setprofile(previous)
    if reason not in ("numeric_mra_1.0", "exact_integer"):
        return None
    pred, target = parsed["pred"], parsed["target"]
    if reason == "exact_integer":
        # Census requires integral operands and no suffix even in relaxed tiers.
        if not census.grade(row, pred, answer)[0] or not target.is_integer():
            return None
    if target == 0:
        # Relative error is undefined at zero; strict acceptance is still retained.
        return None
    error = abs(pred - target) / target
    return error if math.isfinite(error) else None


def validate_destination(census_dir, output_dir):
    census_dir, output_dir = census_dir.resolve(), output_dir.resolve()
    # The explicitly authorized census archive sits under a training-named root.
    # Exempt only its direct numeric snapshot directories, never descendants.
    authorized = output_dir.parent == CENSUS_ROOT.resolve() and output_dir.name.isdigit()
    if not authorized:
        for part in output_dir.parts:
            if any(word in part.lower() for word in ("train", "convers", "convert", "target")):
                raise ValueError("output path is inside a training, conversion, or target directory")
    if output_dir != census_dir:
        raise ValueError("outputs must be beside the census files")
    for name in OUTPUT_NAMES:
        path = output_dir / name
        if path.exists() or path.is_symlink():
            raise FileExistsError("a tolerance output already exists")
    return output_dir


def provenance(repo):
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    source = Path(__file__).read_bytes()
    tracked = subprocess.run(
        ["git", "-C", str(repo), "show", f"{head}:tools/numeric_tolerance_tiers.py"],
        capture_output=True, check=False)
    committed = tracked.returncode == 0 and tracked.stdout == source
    return {"tool_git_commit": head if committed else None,
            "tool_base_git_commit": head, "tool_sha256": digest(source)}


def make_table(aggregates):
    lines = ["| Question type | Finalized | Strict accepted | Additional ≤10% | Additional ≤15% | Additional ≤25% |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for kind, counts in sorted(aggregates.items()):
        cells = [kind, counts["finalized"], counts["strict_accepted"]]
        cells.extend(counts[f"additional_{tier}pct"] for tier in TIERS)
        lines.append("| " + " | ".join(map(str, cells)) + " |")
    return lines


def run(census_dir, census, tool_provenance, *, output_dir=None, label_loader=load_census_inputs):
    census_dir = Path(census_dir)
    destination = validate_destination(census_dir, Path(output_dir or census_dir))
    decision_bytes = (census_dir / "DECISIONS.json").read_bytes()
    decisions = json.loads(decision_bytes)
    summary = json.loads((census_dir / "SUMMARY.json").read_bytes())
    if len(decisions) != summary["distinct_finalized"]:
        raise ValueError("finalized count disagrees with census decisions")
    if sum(d["accepted"] for d in decisions) != summary["distinct_accepted"]:
        raise ValueError("strict accepted count disagrees with census decisions")
    if len({d["id"] for d in decisions}) != len(decisions):
        raise ValueError("duplicate census decision")
    rows, gold = label_loader(census, census_dir)
    by_id = {row["id"]: row for row in rows}
    numeric_types = sorted({row["question_type"] for row in rows if not row.get("options")})
    records, aggregates = [], {}
    for decision in decisions:
        row = by_id[decision["id"]]
        kind = row["question_type"]
        counts = aggregates.setdefault(kind, {"finalized": 0, "strict_accepted": 0,
            **{f"additional_{tier}pct": 0 for tier in TIERS}})
        counts["finalized"] += 1
        counts["strict_accepted"] += decision["accepted"]
        if row.get("options"):
            continue
        error = None
        complete = decision.get("mechanically_complete", False)
        evidence = decision.get("has_perceptual_evidence", False)
        if decision.get("trace_path"):
            trace_bytes = Path(decision["trace_path"]).read_bytes()
            if decision.get("trace_sha256") and digest(trace_bytes) != decision["trace_sha256"]:
                raise ValueError("trace digest disagrees with census decision")
            trace = json.loads(trace_bytes)
            if trace["question_id"] != decision["id"] or trace["question_type"] != kind:
                raise ValueError("trace identity disagrees with census membership")
            answer = census.final_answer(trace)
            # Census grades the final provider answer, not an unchecked pred field.
            # Refuse disagreement rather than assigning tiers to a different answer.
            if answer is not None and trace.get("pred") != answer:
                raise ValueError("trace pred disagrees with the census final answer")
            error = relative_error(census, row, gold[decision["id"]], answer)
        elif decision["accepted"]:
            raise ValueError("accepted census decision lacks its trace")
        record = {"id": decision["id"], "question_type": kind,
                  "strict_accepted": decision["accepted"], "relative_error": error,
                  "mechanically_complete": bool(complete), "has_perceptual_evidence": bool(evidence)}
        for tier in TIERS:
            within = error is not None and error <= tier / 100 + 1e-12
            record[f"within_{tier}pct"] = within
            counts[f"additional_{tier}pct"] += bool(
                within and complete and evidence and not decision["accepted"])
        records.append(record)
    total = len(decisions)
    strict = summary["distinct_accepted"]
    blended = {}
    for tier in TIERS:
        accepted = strict + sum(c[f"additional_{tier}pct"] for c in aggregates.values())
        blended[f"{tier}pct"] = {"accepted": accepted, "finalized": total,
                                 "acceptance_rate": accepted / total if total else None}
    metadata = {"census_stamp": census_dir.name, "decisions_sha256": digest(decision_bytes),
                **tool_provenance}
    result = {**metadata, "numeric_question_types": numeric_types, "records": records,
              "by_question_type": aggregates, "blended": blended}
    lines = ["# Additive numeric tolerance tiers", "",
             f"Census stamp: `{metadata['census_stamp']}`.",
             f"Tool git commit: `{metadata['tool_git_commit'] or 'uncommitted; patch required'}`; base: `{metadata['tool_base_git_commit']}`.",
             f"Tool SHA256: `{metadata['tool_sha256']}`.",
             f"DECISIONS.json SHA256: `{metadata['decisions_sha256']}`.", "",
             "Thresholds are cumulative. Additional traces must satisfy the recorded census completion and perception conditions; strict accepted decisions remain unchanged.",
             "The census grades all rows without options numerically (collector/census.py:47-61), including exact integer counts (55-56). Observed membership types: " + ", ".join(numeric_types) + ".",
             "Census line 47: `if row.get('options'):`; line 56: `return not suffix and pred.is_integer() and target.is_integer() and pred==target,'exact_integer'`; line 60: `correct=target>0 and abs(pred-target)/target <= .05+1e-12`.",
             "The tool uses census.grade() parsing and unit checks. Missing, invalid, unit-incompatible, and zero-denominator answers have null relative error and false tier flags. Counting retains integer and suffix constraints.", "",
             *make_table(aggregates), "",
             f"Strict blended acceptance: {strict}/{total} ({strict / total:.2%})." if total else "Strict blended acceptance: undefined (no finalized traces)."]
    for tier in TIERS:
        value = blended[f"{tier}pct"]
        rate = f"{value['acceptance_rate']:.2%}" if total else "undefined"
        lines.append(f"Blended acceptance at ≤{tier}%: {value['accepted']}/{total} ({rate}).")
    # Validate both destinations before either exclusive write; never overwrite.
    validate_destination(census_dir, destination)
    with (destination / OUTPUT_NAMES[0]).open("x") as handle:
        handle.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    with (destination / OUTPUT_NAMES[1]).open("x") as handle:
        handle.write("\n".join(lines) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("census_dir", type=Path)
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    try:
        run(args.census_dir, import_census(args.repo), provenance(args.repo), output_dir=args.output_dir)
    except Exception as error:
        # Third-party exception text can contain a label or prediction.
        print(f"Tolerance analysis refused ({type(error).__name__}); no answer values logged.", file=sys.stderr)
        return 1
    print("Wrote TOLERANCE_TIERS.json and TOLERANCE_SUMMARY.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
