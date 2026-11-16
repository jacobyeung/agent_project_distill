import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from .arms import MODELS
from .io import ROOT, dump_json, json_hash, sha256, utc
from .metrics import paired_bootstrap
from .protocol import PRIMARY, PRIMARY_TYPES
from .provenance import verify_pricing_cell, verify_arm_epoch


def holm(pvalues):
    values = np.asarray(pvalues, dtype=float)
    if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
        raise ValueError("Invalid family p-value")
    adjusted, previous = np.empty_like(values), 0.
    for rank, index in enumerate(np.argsort(values, kind="stable")):
        previous = max(previous, min(1., (len(values)-rank)*values[index]))
        adjusted[index] = previous
    return adjusted.tolist()


def paired_inference(rows, baseline, draws=20000, permutations=100000, seed=20261111):
    result = paired_bootstrap(rows, baseline, draws=draws, seed=seed)
    reference = {(r["set"], str(r["id"])): r for r in baseline}
    grouped = defaultdict(float)
    for row in rows:
        grouped[row["scene"]] += row["score"] - reference[(row["set"], str(row["id"]))]["score"]
    differences = np.array([grouped[scene] for scene in sorted(grouped)])
    observed = differences.sum()
    exact = len(differences) <= 16
    count = 2**len(differences) if exact else permutations
    rng, exceed = np.random.default_rng(seed), 0
    for start in range(0, count, 2048):
        size = min(2048, count-start)
        if exact:
            bits = ((np.arange(start, start+size)[:, None] >> np.arange(len(differences))) & 1)
        else:
            bits = rng.integers(0, 2, (size, len(differences)))
        statistics = ((2*bits-1)*differences).sum(axis=1)
        exceed += int(np.count_nonzero(statistics >= observed-1e-12))
    result.update(p_one_sided=exceed/count if exact else (exceed+1)/(count+1),
                  permutation_draws=count, permutation_exact=exact,
                  test="paired scene sign-flip; whole-scene model/reference exchange",
                  interval="unadjusted paired scene-cluster percentile interval")
    return result


def selected(rows, typ):
    return [{**r, "score": r["fb"]} for r in rows
            if r["set"] == "vsi" and r["mask"] == "selector" and r["type"] == typ]


def membership(rows):
    return {(r["set"], str(r["id"]), r["scene"], r["type"], r["mask"]) for r in rows}


def verify_family_request(request, seal_sha256, run_id):
    if request["kit_seal_sha256"] != seal_sha256 or request.get("run_id") != run_id:
        raise ValueError("The comparison belongs to another sealed run")


def primary_family(candidates, baseline, draws=20000, permutations=100000):
    results = []
    for model in MODELS:
        for typ in PRIMARY_TYPES:
            reference = selected(baseline, typ)
            rows = selected(candidates.get(model, []), typ)
            row = {"model": model, "arm": f"{model}_depth", "type": typ, "p_one_sided": 1.,
                   "required_items": len(reference), "available_items": len(rows)}
            if not reference:
                raise ValueError("A primary type is absent from the fixed reference")
            if membership(rows) != membership(reference):
                row["status"] = "not_run" if not rows else "incomplete_cohort"
            else:
                row.update(paired_inference(rows, reference, draws, permutations))
                row["status"] = "complete"
            results.append(row)
    for row, adjusted in zip(results, holm([r["p_one_sided"] for r in results])):
        row["holm_p"] = adjusted
        row["primary_win"] = row["status"] == "complete" and adjusted <= PRIMARY["alpha"] and row["ci95"][0] > 0
    decisions = {}
    for model in MODELS:
        rows = [r for r in results if r["model"] == model]
        complete = all(r["status"] == "complete" for r in rows)
        protected = complete and all(r["ci95"][0] >= -2. for r in rows)
        decisions[model] = {"full_cohort": complete, "protected_types_pass": protected,
                            "depth_swap_supported": protected and any(r["primary_win"] for r in rows)}
    return {"protocol": PRIMARY, "hypotheses": results, "decisions": decisions}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--native-g3t-cell")
    args = parser.parse_args()
    baseline_path = ROOT / "out/baselines/g3t_policy_selector/rows.jsonl"
    seal = json.loads((ROOT / "KIT_SEAL.json").read_text())
    seal_digest = sha256(ROOT / "KIT_SEAL.json")
    run_id = json_hash({"output": str(Path(args.runs).resolve()), "kit": seal_digest})[:16]
    if sha256(baseline_path) != seal["files"][str(baseline_path.relative_to(ROOT))]:
        raise ValueError("The fixed primary reference differs from its seal")
    baseline = [json.loads(line) for line in baseline_path.read_text().splitlines()]
    candidates, evidence, secondary = {}, {}, {}
    native_reference = None
    if args.native_g3t_cell:
        native_reference, config = verify_pricing_cell(args.native_g3t_cell)
        if config["fusion"] != "policy" or config["mode"] != "selector" or config["representation"] != "native":
            raise ValueError("Native G3T reference does not match the frozen pricing cell")
        export_config = json.loads((Path(config["exports"]) / "config.json").read_text())
        if export_config.get("model") != "g3t":
            raise ValueError("The native reference is not G3T")
        request = verify_arm_epoch(config["exports"], seal_digest)
        verify_family_request(request, seal_digest, run_id)
    for model in MODELS:
        arm = Path(args.runs) / f"{model}_depth"
        cell = arm / "policy_selector_grid51"
        if not (cell / "COMPLETE.json").exists():
            continue
        rows, config = verify_pricing_cell(cell)
        request = json.loads((arm / "request.json").read_text())
        verify_family_request(request, seal_digest, run_id)
        export_config = json.loads((Path(config["exports"]) / "config.json").read_text())
        if (config["calibration"] != "frozen_g3t" or config["primary_protocol_sha256"] != json_hash(PRIMARY)
                or (config["fusion"], config["mode"], config["representation"]) != ("policy", "selector", "grid51")
                or export_config.get("kind") != "depth" or export_config.get("candidate_model") != model):
            raise ValueError("A primary arm changed the frozen protocol")
        candidates[model] = rows
        evidence[model] = {"cell_receipt_sha256": sha256(cell / "COMPLETE.json"),
                           "request_sha256": sha256(arm / "request.json")}
        native = arm / "policy_selector_native"
        secondary[model] = {"native_reference_status": "authenticated" if native_reference is not None else "deferred",
                            "candidate_native_status": "not_run"}
        if (native / "COMPLETE.json").exists():
            native_rows, _ = verify_pricing_cell(native)
            secondary[model]["candidate_native_status"] = "complete"
            for label, reference in (("g3t_grid51", baseline), ("g3t_native", native_reference)):
                if reference is None:
                    continue
                comparisons = {}
                for typ in PRIMARY_TYPES:
                    aa, bb = selected(native_rows, typ), selected(reference, typ)
                    comparisons[typ] = (paired_bootstrap(aa, bb) if membership(aa) == membership(bb) and aa
                                        else {"status": "incomplete_cohort"})
                secondary[model][label] = comparisons
    result = primary_family(candidates, baseline)
    result.update(checked_at=utc(), evidence=evidence, secondary_native=secondary,
                  native_reference_status="authenticated" if native_reference is not None else "deferred",
                  baseline_sha256=sha256(baseline_path), kit_sha256=sha256(ROOT / "KIT_SEAL.json"))
    dump_json(args.out, result)


if __name__ == "__main__":
    main()
