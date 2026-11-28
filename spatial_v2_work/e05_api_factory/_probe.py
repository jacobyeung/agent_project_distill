#!/usr/bin/env python3
"""Diagnostic census of the 233 leak-free K1 train captures on local NVMe."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, "/scratch/jjyeung/orch_n30/sb_ktfix2/code/vendor")
import store_room_audit as sra


def run_census():
    ledger = sra.Inputs()
    base = Path("/scratch/jjyeung/orch_n30/sb_ktfix2/inputs/exclusions")
    rooms_obj, mint, sets, _, aliases, quarantine = sra.prepare(
        base / "tree_r1", base / "lists", ledger
    )
    bench_doc = json.loads((base / "lists/3119aa4a.raw").read_bytes())
    resti_set = {"scannet/" + s.split("_")[0] for s in bench_doc["subsets"]["ReSTI_scannet_scenes"]}

    d = json.load(open("/scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json"))
    labels_by_cap = {
        r["capture"]: r["convention"]
        for r in json.load(open("/scratch/jjyeung/orch_n30/sb_kbox4/train_labels.json"))["rows"]
    }

    clean = []
    for c in d["captures"]:
        ds, sc = c["canonical"].split("/", 1)
        _, _, phys_room, _, err = sra.resolve(
            {"dataset": ds, "scene": sc, "canonical": c["canonical"]},
            rooms_obj, mint, aliases, quarantine,
        )
        assert err is None and phys_room == c["room"]
        if any(phys_room in s for s in sets.values()) or phys_room in resti_set:
            continue
        clean.append(c)

    by_ds = Counter(c["canonical"].split("/")[0] for c in clean)
    print("Clean captures by dataset:", dict(by_ds))

    small_examples = []
    large_count_examples = []
    oof_unseen_examples = []
    multi_inst_examples = []
    skip_labels = {"wall", "floor", "ceiling", "object", "otherfurniture", "otherstructure", "otherprop", " REMOVE"}

    for c in clean:
        ds = c["canonical"].split("/")[0]
        z = np.load(c["gt"]["path"], allow_pickle=False)
        conv = labels_by_cap.get(c["canonical"], "half" if ds == "scannetpp" else "full")
        mult = 2.0 if conv == "half" else 1.0
        lengths = z["obb_lengths"] * mult
        labs = [str(x).strip() for x in z["labels"]]
        inst = z["inst"]
        valid = z["valid"].astype(bool)

        vis_px_by_id = {}
        for f_idx in np.flatnonzero(valid):
            u, cnts = np.unique(inst[f_idx], return_counts=True)
            for iid, px in zip(u.tolist(), cnts.tolist()):
                if iid > 0 and px >= 150:
                    vis_px_by_id.setdefault(iid, []).append((int(f_idx) + 1, int(px)))

        vis_idx = [i for i, iid in enumerate(z["ids"]) if int(iid) in vis_px_by_id]
        cat_to_idxs = {}
        for i in vis_idx:
            if labs[i].lower() not in skip_labels and len(labs[i]) >= 2:
                cat_to_idxs.setdefault(labs[i], []).append(i)

        for cat, idxs in cat_to_idxs.items():
            if len(idxs) == 1:
                i = idxs[0]
                max_ext = float(np.max(lengths[i]))
                best_f, best_px = max(vis_px_by_id[int(z["ids"][i])], key=lambda x: x[1])
                if 0.06 <= max_ext < 0.30 and best_px >= 250 and len(small_examples) < 12:
                    small_examples.append((c["canonical"], cat, round(max_ext, 4), best_f, best_px))
            if len(idxs) >= 5 and len(large_count_examples) < 12:
                large_count_examples.append((c["canonical"], cat, len(idxs)))
            if 2 <= len(idxs) <= 4 and len(multi_inst_examples) < 12:
                multi_inst_examples.append((c["canonical"], cat, len(idxs)))

        # Check real OOF SAM3 candidates.json for UNSEEN on registered operands
        key = hashlib.sha256(json.dumps(c["canonical"]).encode()).hexdigest()[:16]
        cand_path = Path("/scratch/jjyeung/k1/run_convert_2") / key / "candidates.json"
        if cand_path.is_file() and len(oof_unseen_examples) < 12:
            cand = json.load(open(cand_path))
            phrases = list(cand.get("phrases", []))
            for r in c["rows"]:
                for op in r.get("operands", []):
                    iid = (r.get("gt_instances") or {}).get(op)
                    if iid and iid in vis_px_by_id and op in phrases:
                        p_idx = phrases.index(op)
                        max_score = 0.0
                        frames_obj = cand.get("frames", {})
                        fr_iter = frames_obj.values() if isinstance(frames_obj, dict) else frames_obj
                        for fr in fr_iter:
                            props = fr.get("proposals", fr) if isinstance(fr, dict) else fr
                            for prop in (props if isinstance(props, list) else []):
                                if isinstance(prop, dict) and (prop.get("phrase_index") == p_idx or prop.get("phrase") == op):
                                    max_score = max(max_score, float(prop.get("score", 0.0)))
                        if max_score < 0.30:
                            best_f, best_px = max(vis_px_by_id[iid], key=lambda x: x[1])
                            if best_px >= 300:
                                oof_unseen_examples.append((c["canonical"], op, round(max_score, 3), best_f, best_px))

    print("Sample small (<30cm) singletons:", small_examples[:8])
    print("Sample large counts (>=5):", large_count_examples[:8])
    print("Sample multi-instance (2..4):", multi_inst_examples[:8])
    print("Sample real OOF UNSEEN (<0.30 score):", oof_unseen_examples[:8])


if __name__ == "__main__":
    run_census()
