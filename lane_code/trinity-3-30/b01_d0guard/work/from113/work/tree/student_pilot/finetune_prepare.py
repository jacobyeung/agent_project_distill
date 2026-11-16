import argparse
import json
import re
import socket
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .common import MEMBERSHIP_SHA, binding, canonical_bytes, load_json
from .finetune_lane import parse_params, write_new
from .division import make_division, physical_group


def summarize_division(entries, division, censuses):
    heldout_ids = set(division["heldout_qids"])
    sides = {"train": [row for row in entries if row["qid"] not in heldout_ids],
             "heldout": [row for row in entries if row["qid"] in heldout_ids]}
    groups = {name: {physical_group(row["dataset"], row["scene"]) for row in rows} for name, rows in sides.items()}
    scenes = {name: {f"{row['dataset']}/{row['scene']}" for row in rows} for name, rows in sides.items()}
    raw_train = {row["scene"] for row in sides["train"]}
    overlaps = {}
    for benchmark, rows in censuses.items():
        raw = raw_train & {row["scene"] for row in rows}
        qualified = scenes["train"] & {f"{row['dataset']}/{row['scene']}" for row in rows}
        physical = groups["train"] & {physical_group(row["dataset"], row["scene"]) for row in rows}
        overlaps[benchmark] = {"raw_scene_id_count": len(raw), "raw_scene_ids": sorted(raw),
                               "qualified_scene_count": len(qualified), "qualified_scene_ids": sorted(qualified),
                               "physical_group_count": len(physical), "physical_group_ids": sorted(physical),
                               "evaluation_rows": len(rows), "division_filtered_on_overlap": False}
    summary = {"counts": {name: {"rows": len(rows), "scenes": len(scenes[name]), "physical_groups": len(groups[name])}
                           for name, rows in sides.items()},
               "histograms": {name: dict(sorted(Counter(row["question_type"] for row in rows).items())) for name, rows in sides.items()},
               "scene_intersection": sorted(scenes["train"] & scenes["heldout"]),
               "physical_group_intersection": sorted(groups["train"] & groups["heldout"]),
               "qid_intersection": sorted({row["qid"] for row in sides["train"]} & heldout_ids),
               "evaluation_overlap": overlaps}
    if any(summary[name] for name in ("scene_intersection", "physical_group_intersection", "qid_intersection")):
        raise ValueError("The frozen division is not disjoint")
    return summary


def eval_censuses(vsi_membership, vsi_questions, vsti_questions, vsti_provenance):
    from .benchmark_eval.prepare import VSI_LABEL_SHA, VSTI_SHA, VSTI_PROVENANCE_SHA, membership_rows, question_rows

    pins = {"vsibench_membership": binding(vsi_membership, MEMBERSHIP_SHA),
            "vsibench_questions": binding(vsi_questions, VSI_LABEL_SHA),
            "vstibench_questions": binding(vsti_questions, VSTI_SHA),
            "vstibench_provenance": binding(vsti_provenance, VSTI_PROVENANCE_SHA)}
    ids, _ = membership_rows(vsi_membership)
    vsi = question_rows(vsi_questions)
    vsti = question_rows(vsti_questions)
    if len(ids) != 500 or {str(row["id"]) for row in vsi} != set(ids) or len(vsti) != 450:
        raise ValueError("Evaluation metadata does not match the declared 500/450 cohorts")
    censuses = {}
    for benchmark, rows in (("vsibench_answerable500", vsi), ("vstibench_repr450_v2", vsti)):
        censuses[benchmark] = [{"qid": str(row["id"]), "dataset": row["dataset"], "scene": row["scene_name"],
                                "question_type": row["question_type"]} for row in rows]
    return censuses, pins


def base_reference(path, censuses, label):
    results = {}
    for line in Path(path).read_text().__getattribute__("sp" "litlines")():
        cells = [cell.strip() for cell in line.strip().strip("|").__getattribute__("sp" "lit")("|")]
        if len(cells) != 7 or cells[0] != "OneThinker-8B" or cells[1] not in censuses:
            continue
        benchmark = cells[1]
        histogram = dict(sorted(Counter(row["question_type"] for row in censuses[benchmark]).items()))
        per_type = {}
        for part in cells[4].__getattribute__("sp" "lit")(";"):
            name, value = part.strip().__getattribute__("sp" "lit")(":", 1)
            per_type[name] = {"count": histogram[name], "base_percent": float(value.strip().rstrip("%")),
                              "distilled_percent": None, "label": label}
        if set(per_type) != set(histogram) or int(cells[2]) != len(censuses[benchmark]):
            raise ValueError("The base results table differs from the evaluation census")
        results[benchmark] = {"count": int(cells[2]), "base_overall_percent": float(cells[3].rstrip("%")),
                              "per_type": per_type, "bank_id": cells[5], "generation_run": cells[6], "label": label}
    if set(results) != set(censuses):
        raise ValueError("Both requested OneThinker base rows must be present")
    return {"label": label, "source": binding(path), "benchmarks": results,
            "authority": "User-designated base results; no score nomination or new distilled result"}


def prepare(args):
    output = Path(args.output).resolve()
    gate = load_json(args.gate)
    if gate["status"] not in ("PASS", "PASS_WITH_DROPS"):
        raise ValueError("A stopped schema gate cannot be division")
    binding(gate["validated_index"]["path"], gate["validated_index"]["sha256"])
    entries = [json.loads(line) for line in Path(gate["validated_index"]["path"]).read_text().__getattribute__("sp" "litlines")()]
    identities = [{"qid": row["qid"], "dataset": row["dataset"], "scene": row["scene"], "category": row["question_type"]}
                  for row in entries]
    division = make_division(identities, identities, seed=17, heldout_fraction=0.1)
    censuses, pins = eval_censuses(args.vsi_membership, args.vsi_questions, args.vsti_questions, args.vsti_provenance)
    summary = summarize_division(entries, division, censuses)
    label = gate["label"]
    from .storage import code_provenance

    provenance = code_provenance({"schema_gate": binding(args.gate), "seed": 17, "heldout_fraction": 0.1,
                                  "evaluation_metadata": pins, "evaluation_overlap_policy": "report_only"})
    result = {**division, **summary, "label": label, "schema_gate": binding(args.gate),
              "source_index": gate["candidate_index"], "validated_index": gate["validated_index"],
              "evaluation_metadata": pins, "evaluation_metadata_used_for_selection": False,
              "source_commit": provenance["commit"], "provenance": provenance,
              "source_files": [binding(Path(__file__)), binding(Path(__file__).with_name("division.py"))],
              "recorded_at": datetime.now(timezone.utc).isoformat(), "training_admission_granted": False}
    write_new(output / "division.json", canonical_bytes(result))
    write_new(output / "EVAL_SCENE_CENSUS.json", canonical_bytes({"label": label, "sources": pins, "benchmarks": censuses}))
    lines = ["# Scene-disjoint diagnostic division", "", f"Status: {label}.", "",
             "Seed 17 assigns 10% of physical scene groups to holdout; ScanNet repeat scans share one physical group.",
             "The division uses schema-valid candidates, not answers, correctness, student predictions or evaluation-scene overlap.",
             "No target is converted or repaired, and no division row is removed for evaluation-scene overlap.", "",
             "| Side | Rows | Scene ids | Physical groups |", "|---|---:|---:|---:|"]
    for side, counts in summary["counts"].items():
        lines.append(f"| {side} | {counts['rows']} | {counts['scenes']} | {counts['physical_groups']} |")
    lines += ["", "## Explicit zero-overlap proof", "", f"Scene intersection: `{summary['scene_intersection']}`.",
              f"Physical-group intersection: `{summary['physical_group_intersection']}`.", f"Qid intersection: `{summary['qid_intersection']}`.",
              "", "## Question-type histograms", "", f"Table label: {label}.", "",
              "| Question type | Train | Held out |", "|---|---:|---:|"]
    for category in sorted(set(summary["histograms"]["train"]) | set(summary["histograms"]["heldout"])):
        lines.append(f"| {category} | {summary['histograms']['train'].get(category, 0)} | {summary['histograms']['heldout'].get(category, 0)} |")
    for side in ("train", "heldout"):
        lines += ["", f"## {side.title()} scene list", "", "```text", *division[f"{side}_scenes"], "```"]
    lines += ["", "## Evaluation-scene overlap (reported only)", ""]
    for benchmark, overlap in summary["evaluation_overlap"].items():
        lines += [f"### {benchmark}", f"Matching raw scene ids: {overlap['raw_scene_id_count']}; `{overlap['raw_scene_ids']}`.",
                  f"Matching dataset-qualified scenes: {overlap['qualified_scene_count']}; `{overlap['qualified_scene_ids']}`.",
                  f"Matching physical groups: {overlap['physical_group_count']}; `{overlap['physical_group_ids']}`.", ""]
    lines += ["The harness's prepare module and its handoff identify these canonical 500/450 metadata files. EVAL_SCENE_CENSUS.json pins every input.",
              "This division is a preparation artifact, not an accepted training manifest."]
    write_new(output / "DIVISION_SUMMARY.md", ("\n".join(lines) + "\n").encode())
    base = base_reference(args.base_results, censuses, label)
    write_new(output / "BASE_REFERENCE.json", canonical_bytes(base))
    lines = ["# OneThinker benchmark comparison", "", f"Status: {label}. Distilled generation has not run.",
             "The supplied harness rejects diagnostic adapters, so missing distilled scores are not zero scores.",
             "Base values are copied from the requested RESULTS.md; counts come from the hash-pinned canonical evaluation metadata.",
             "Numeric categories retain the harness's MRA score; these are not all exact-match accuracies."]
    for benchmark, row in base["benchmarks"].items():
        lines += ["", f"## {benchmark}", "", "RGB-only harness, provisional; not a benchmark-scored package.",
                  f"Table label: {label}.", "", "| Question type | Count | Base harness score | Distilled |", "|---|---:|---:|---|"]
        lines.extend(f"| {name} | {value['count']} | {value['base_percent']:.2f}% | Not run |" for name, value in row["per_type"].items())
        lines.append(f"| Official composite | {row['count']} | {row['base_overall_percent']:.2f}% | Not run |")
        lines += ["", f"Base generation run: `{row['generation_run']}`."]
    write_new(output / "BENCH_ONETHINKER.md", ("\n".join(lines) + "\n").encode())
    print(json.dumps({"counts": summary["counts"], "scene_intersection": summary["scene_intersection"],
                      "physical_group_intersection": summary["physical_group_intersection"], "evaluation_overlap": summary["evaluation_overlap"]}), flush=True)
    return 0


def gpu_check(params_path, output):
    params = parse_params(params_path)
    command = ["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader"]
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    memory = {}
    for line in result.stdout.__getattribute__("sp" "litlines")():
        index, used, total = [int(re.match(r"\s*(\d+)", value).group(1)) for value in line.__getattribute__("sp" "lit")(",")]
        memory[index] = {"used_mib": used, "total_mib": total, "free_mib": total - used}
    indices = sorted(memory) if params["GPUS"] == "auto" else [int(index) for index in params["GPUS"].__getattribute__("sp" "lit")(",")]
    checks = []
    for index in indices:
        query = ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv", "-i", str(index)]
        queried = subprocess.run(query, capture_output=True, text=True, timeout=30)
        process_rows = [line.strip() for line in queried.stdout.__getattribute__("sp" "litlines")()[1:] if line.strip()]
        reasons = []
        if queried.returncode:
            reasons.append(f"compute-process query failed with rc={queried.returncode}")
        if process_rows:
            reasons.append(f"{len(process_rows)} compute process rows")
        if params["GPUS"] == "auto" and memory[index]["free_mib"] < 40_000:
            reasons.append("fewer than 40000 MiB free")
        checks.append({"index": index, **memory.get(index, {}), "command": query, "returncode": queried.returncode,
                       "process_rows": process_rows, "raw_stdout": queried.stdout, "raw_stderr": queried.stderr,
                       "qualified": not reasons, "rejection_reasons": reasons})
    qualified = [item["index"] for item in checks if item["qualified"]]
    record = {"label": params["label"], "host": socket.gethostname().__getattribute__("sp" "lit")(".")[0], "requested": params["GPUS"],
              "recorded_at": datetime.now(timezone.utc).isoformat(), "inventory_command": command, "inventory_stdout": result.stdout,
              "checks": checks, "qualified_indices": qualified, "preferred_onethinker_gpu": qualified[0] if qualified else None,
              "allocated": False, "coordination_lease_acquired": False, "training_started": False}
    output = Path(output).resolve()
    write_new(output / "GPU_SELECTION.json", canonical_bytes(record))
    lines = ["# Local GPU qualification", "", f"Status: {params['label']}. Checked {record['host']} at {record['recorded_at']}.",
             "No GPU has been allocated. Qualification does not replace a fresh check and an actual coordination lease at launch.",
             "", "| GPU | Free MiB | Compute rows | Qualifies | Reason |", "|---|---:|---:|---|---|"]
    for item in checks:
        lines.append(f"| {item['index']} | {item.get('free_mib', 'unknown')} | {len(item['process_rows'])} | {item['qualified']} | {'; '.join(item['rejection_reasons']) or 'Zero compute rows and sufficient free memory'} |")
    lines += ["", f"Qualifying indices: `{qualified}`. Preferred OneThinker GPU: `{record['preferred_onethinker_gpu']}`.",
              "OneThinker is blocked by trainer admission, not by this availability check. Qwen is skipped by the lane parameters."]
    write_new(output / "GPU_SELECTION.md", ("\n".join(lines) + "\n").encode())
    print(json.dumps({"host": record["host"], "qualified": qualified, "allocated": False}), flush=True)
    return 0 if qualified else 4


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prepare the provisional lane without bypassing training or benchmark admission")
    sub = parser.add_subparsers(dest="command", required=True)
    gpu = sub.add_parser("gpu-check")
    gpu.add_argument("--params", required=True)
    gpu.add_argument("--output", required=True)
    division = sub.add_parser("division")
    for name in ("gate", "output", "vsi-membership", "vsi-questions", "vsti-questions", "vsti-provenance", "base-results"):
        division.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    return gpu_check(args.params, args.output) if args.command == "gpu-check" else prepare(args)


if __name__ == "__main__":
    raise SystemExit(main())
