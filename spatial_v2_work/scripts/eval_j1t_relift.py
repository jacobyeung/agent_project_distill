"""Exact DEV-MASK 117 paired distance-MRA evaluator for J1-T (KT-1a).

Imports relift.py unchanged via lever8/j1/kit/j1_common.py and scores all J1-T decoded masks
(k', kB(0.9), kB(0.7), kB(0.7)/s2, kB(0.5), kP-miss, kP-fp) plus k_notower (0 SAM 3)
paired against baseline a, GT ceiling e, and banked J1 k on the 117 eligible items
(46 captures, 35 physical rooms, 10,000-draw room bootstrap, seed 20261120).
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

J1_KIT = Path("/scratch/jjyeung/orch_n30/lever8/j1/kit")
if str(J1_KIT) not in sys.path:
    sys.path.insert(0, str(J1_KIT))

import j1_common as G
import select_j1 as S

J1T_ARMS = (
    "k_prime",
    "kB_0.9",
    "kB_0.7",
    "kB_0.7_s2",
    "kB_0.5",
    "kP_miss",
    "kP_fp",
)
EXTRA_ARMS = ("k_notower",)
ALL_EVAL_ARMS = ("k",) + J1T_ARMS + EXTRA_ARMS
CELLS = ("a", "e") + ALL_EVAL_ARMS


def relift_args(R, out: Path):
    return SimpleNamespace(
        capture=R.BASE / "cap/t1.gz",
        depth=G.DEPTH,
        receipt=G.RECEIPT,
        join=R.BASE / "cap/score_t1/JOIN_T1.jsonl",
        funnel=R.BASE / "cap/score_t1/FUNNEL_T1.json",
        gt_dirs=[R.BASE / "gt/t1_gt/gt", R.BASE / "gt/arkit_gt/gt"] + R.NOGT_DIRS,
        out=Path(out),
        half_only=False,
    )


def fresh_relift(R) -> dict[str, Any]:
    captured: dict[str, Any] = {}
    original = R.dump
    R.dump = lambda path, value: captured.__setitem__("result", value)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            R.run(relift_args(R, G.OUT / "unused_relift_dump.json"))
    finally:
        R.dump = original
    result = captured["result"]
    if result["status"] != "complete":
        raise ValueError("fresh relift did not complete: " + str(result["status"]))
    return result


def box_to_grid_mask(box_cxcywh: list[float], shape: tuple[int, int] = G.GRID) -> np.ndarray:
    """Fill normalized [cx, cy, w, h] box directly onto the (240, 320) relift grid (0 SAM 3)."""
    r0, r1, c0, c1 = S.box_pixels(box_cxcywh, shape=shape)
    H, W = shape
    r0, r1 = max(0, min(H, r0)), max(0, min(H, r1))
    c0, c1 = max(0, min(W, c0)), max(0, min(W, c1))
    m = np.zeros(shape, dtype=bool)
    if r1 > r0 and c1 > c0:
        m[r0:r1, c0:c1] = True
    return m


def j1t_verdict_vs_k(m: dict[str, Any]) -> str:
    """Registered J1-T tolerance rule on D(t) = kB(t) - k (PRICING_C2_C3.md L44-48):
    - holds: D(t) >= -3 and lower bound > -8
    - breaks: upper bound < -3
    - unclear: otherwise
    """
    if m["mean"] is None or m["ci95"] is None:
        return "unclear"
    if m["mean"] >= -3.0 and m["ci95"][0] > -8.0:
        return "holds"
    if m["ci95"][1] < -3.0:
        return "breaks"
    return "unclear"


def share_ratio(boot, rr: list[dict[str, Any]], num_key: str, den_key: str) -> dict[str, Any]:
    """Bootstrap ratio mean(num_key - a) / mean(den_key - a) across 10,000 room draws."""
    d_num = [dict(r, delta=r[num_key] - r["a"]) for r in rr]
    d_den = [dict(r, delta=r[den_key] - r["a"]) for r in rr]
    v_num, _ = boot.samples(d_num, "delta")
    v_den, _ = boot.samples(d_den, "delta")
    ratio = np.divide(v_num, v_den, out=np.full(len(v_num), np.nan), where=np.isfinite(v_den) & (v_den != 0))
    m_num = float(np.mean([r["delta"] for r in d_num])) if rr else None
    m_den = float(np.mean([r["delta"] for r in d_den])) if rr else None
    return boot.summarize((m_num / m_den) if (m_num is not None and m_den) else None, ratio)


def load_j1t_capture_masks(
    cap: str,
    j1t_detect_dir: Path,
    j1_detect_dir: Path,
    prompts_cap: dict[str, Any],
) -> tuple[dict[str, dict[int, np.ndarray]], dict[str, list[float]]]:
    """Load (32, 240, 320) boolean mask arrays per arm and instance_id for one capture,
    and compute per-anchor 480x640 mask IoUs against banked J1 k and J1-T k_prime.
    """
    stub = G.stub(cap)
    j1_data = G.read_json(j1_detect_dir / f"{stub}.json.gz")
    j1t_data = G.read_json(j1t_detect_dir / f"{stub}.json.gz")

    arm_masks: dict[str, dict[int, np.ndarray]] = {arm: {} for arm in ALL_EVAL_ARMS}
    mask_ious_vs_k: dict[str, list[float]] = {arm: [] for arm in J1T_ARMS}

    # Banked J1 k (480x640 unpacked for parity, 240x320 grid for relift)
    j1_k_480: dict[int, dict[int, np.ndarray]] = {}
    for iid_str, rec in j1_data["k"].items():
        iid = int(iid_str)
        m_grid = np.zeros((32,) + G.GRID, dtype=bool)
        j1_k_480[iid] = {}
        for a in rec["anchors"]:
            m480 = G.unpack(a["mask"])
            j1_k_480[iid][int(a["slot"])] = m480
            m_grid[int(a["slot"]) - 1] = S.to_grid(m480)
        arm_masks["k"][iid] = m_grid

    # J1-T decoded arms
    for arm in J1T_ARMS:
        for iid_str, rec in j1t_data["arms"][arm].items():
            iid = int(iid_str)
            m_grid = np.zeros((32,) + G.GRID, dtype=bool)
            by_slot_480: dict[int, np.ndarray] = {}
            for a in rec["anchors"]:
                slot = int(a["slot"])
                m480 = G.unpack(a["mask"])
                by_slot_480[slot] = m480
                m_grid[slot - 1] = S.to_grid(m480)
            arm_masks[arm][iid] = m_grid

            # Compare against banked J1 k on all GT slots
            if iid in j1_k_480:
                for slot, ref480 in j1_k_480[iid].items():
                    cand480 = by_slot_480.get(slot, np.zeros(G.CANVAS, dtype=bool))
                    mask_ious_vs_k[arm].append(float(S.iou(cand480, ref480)))

    # k_notower: raw GT tight box filled on 240x320 grid without SAM 3
    for u in prompts_cap["arms"]["k_prime"]:
        iid = int(u["instance_id"])
        m_grid = np.zeros((32,) + G.GRID, dtype=bool)
        for b in u["boxes"]:
            m_grid[int(b["slot"]) - 1] = box_to_grid_mask(b["box"], G.GRID)
        arm_masks["k_notower"][iid] = m_grid

    return arm_masks, mask_ious_vs_k


def evaluate_j1t(j1t_dir: Path) -> dict[str, Any]:
    R = G.load_relift()
    R.dependencies()
    fresh = fresh_relift(R)

    prompts_j1t = G.read_json(j1t_dir / "PROMPTS_J1T.json")
    prompts_by_cap = {c["capture"]: c for c in prompts_j1t["captures"]}
    j1t_detect_dir = j1t_dir / "detect"

    refs = {r["item_id"]: r for r in json.loads(G.ITEMS.read_text())["items"]}
    items, objects, _ = G.eligible(R, refs)
    rows = R.read_records(R.BASE / "cap/t1.gz", refs)
    depths = G.depth_rows(R)

    by_item: dict[str, list[dict[str, Any]]] = {}
    for o in objects:
        by_item.setdefault(o["item_id"], []).append(o)

    out_rows = []
    pr_records: dict[tuple[str, str], list[dict[str, Any]]] = {
        (cell, ds): [] for cell in CELLS for ds in G.DATASETS3
    }
    grid_ious_vs_gt: dict[str, list[float]] = {cell: [] for cell in CELLS}
    all_480_ious_vs_k: dict[str, list[float]] = {arm: [] for arm in J1T_ARMS}

    cache: dict[str, Any] = {}
    for cap, p_cap in prompts_by_cap.items():
        _, cap_ious_vs_k = load_j1t_capture_masks(cap, j1t_detect_dir, G.DETECT, p_cap)
        for arm in J1T_ARMS:
            all_480_ious_vs_k[arm].extend(cap_ious_vs_k[arm])

    for it in items:
        iid, cap = it["item_id"], it["capture"]
        ref = refs[iid]
        if cap not in cache:
            cache.clear()
            with np.load(it["gt_path"], allow_pickle=False) as z:
                inst_arr = z["inst"].copy()
            g_arr = R.restore(depths[cap])
            arm_masks, _ = load_j1t_capture_masks(cap, j1t_detect_dir, G.DETECT, prompts_by_cap[cap])
            cache[cap] = (inst_arr, g_arr, arm_masks)
        inst, g, arm_masks = cache[cap]
        served = {o["name"].strip().lower(): o for o in rows[iid]["objects"]}

        pair: dict[str, list[Any]] = {cell: [] for cell in CELLS}
        for o in by_item[iid]:
            name = o["name"]
            target = inst == o["instance_id"]
            obj = served.get(name.strip().lower())
            masks: dict[str, np.ndarray] = {
                "a": R.masks_array(obj["selected_masks"]) if obj else np.zeros((32,) + G.GRID, dtype=bool),
                "e": target,
            }
            for arm in ALL_EVAL_ARMS:
                masks[arm] = arm_masks[arm][o["instance_id"]]

            for cell in CELLS:
                m_cell = masks[cell]
                if m_cell.shape != (32,) + G.GRID:
                    raise ValueError(f"Mask shape mismatch for {cell}: {m_cell.shape}")
                value, _ = R.fit_lift(name, m_cell, g)
                pair[cell].append(value)
                fr = G.precision_recall(m_cell, target)
                pr_records[(cell, G.fine(cap))] += fr
                for f in range(32):
                    if target[f].any():
                        grid_ious_vs_gt[cell].append(float(S.iou(m_cell[f], target[f])))

        truth = float(ref["task"]["ground_truth"])
        factor = R.unit_factor(ref["task"]["question"])
        entry: dict[str, Any] = dict(
            item_id=iid,
            capture=cap,
            room=ref["task"]["room"],
            dataset=G.dataset(cap),
            dataset3=G.fine(cap),
            gaps={},
        )
        for cell, values in pair.items():
            lifted = R.gap_value(values)
            gap = R.round_gap(lifted)
            entry["gaps"][cell] = gap
            entry[cell] = 100.0 * R.official_mra(None if gap is None else gap * factor, truth)
        out_rows.append(entry)

    # Verify exact reproduction of a and e against fresh relift.run
    ref_rows = fresh["rows"]
    if [r["item_id"] for r in ref_rows] != [r["item_id"] for r in out_rows]:
        raise AssertionError("Item population or order differs from relift")
    for mine, theirs in zip(out_rows, ref_rows):
        for cell in ("a", "e"):
            if mine[cell] != theirs[cell] or mine["gaps"][cell] != theirs["gaps"][cell]:
                raise AssertionError(f"Cell {cell} differs from relift on {mine['item_id']}")

    boot = R.Bootstrap(refs)
    statistics = []
    for ds in ("all",) + G.DATASETS3:
        rr = [r for r in out_rows if ds == "all" or r["dataset3"] == ds]
        cells_stat = {cell: boot.metric(rr, cell) for cell in CELLS}
        vs_a = {
            f"{arm}-a": boot.metric([dict(r, delta=r[arm] - r["a"]) for r in rr], "delta")
            for arm in ALL_EVAL_ARMS + ("e",)
        }
        vs_k = {
            f"{arm}-k": boot.metric([dict(r, delta=r[arm] - r["k"]) for r in rr], "delta")
            for arm in J1T_ARMS + EXTRA_ARMS + ("a", "e")
        }
        vs_k_prime = {
            f"{arm}-k_prime": boot.metric([dict(r, delta=r[arm] - r["k_prime"]) for r in rr], "delta")
            for arm in J1T_ARMS + EXTRA_ARMS + ("k", "a", "e")
        }
        share_ea = {arm: share_ratio(boot, rr, arm, "e") for arm in ALL_EVAL_ARMS}
        share_ka = {arm: share_ratio(boot, rr, arm, "k") for arm in J1T_ARMS + EXTRA_ARMS}
        refusals = {cell: sum(1 for r in rr if r["gaps"][cell] is None) for cell in CELLS}

        stat_entry: dict[str, Any] = dict(
            dataset=ds,
            n=len(rr),
            rooms=len({r["room"] for r in rr}),
            decides=(ds == "all"),
            cells=cells_stat,
            versus_a=vs_a,
            versus_k=vs_k,
            versus_k_prime=vs_k_prime,
            share_of_e_minus_a=share_ea,
            share_of_k_minus_a=share_ka,
            refusals=refusals,
        )
        if ds == "all":
            stat_entry["verdict_vs_a"] = {arm: S.verdict(vs_a[f"{arm}-a"], oracle=True) for arm in ALL_EVAL_ARMS}
            stat_entry["verdict_vs_k_j1t"] = {arm: j1t_verdict_vs_k(vs_k[f"{arm}-k"]) for arm in J1T_ARMS + EXTRA_ARMS}
        statistics.append(stat_entry)

    # Parity gate check: k' vs J1 k
    k_prime_ious = np.asarray(all_480_ious_vs_k["k_prime"], dtype=np.float64)
    k_prime_pass_n = int(np.sum(k_prime_ious >= 0.95))
    k_prime_total = int(len(k_prime_ious))
    k_prime_rate = float(k_prime_pass_n / k_prime_total) if k_prime_total else 0.0
    all_stat = statistics[0]
    k_prime_minus_k_mean = float(all_stat["versus_k"]["k_prime-k"]["mean"])
    exact_item_score_matches = sum(1 for r in out_rows if r["k_prime"] == r["k"])
    exact_item_gap_matches = sum(1 for r in out_rows if r["gaps"]["k_prime"] == r["gaps"]["k"])
    parity_gate_passed = (k_prime_rate >= 0.95) and (abs(k_prime_minus_k_mean) <= 0.5)

    # Precision / recall & mask IoU summaries
    precision_recall = {
        cell: {ds: G.summarize_pr(pr_records[(cell, ds)]) for ds in G.DATASETS3}
        for cell in CELLS
    }
    for cell in CELLS:
        precision_recall[cell]["all"] = G.summarize_pr(
            [x for ds in G.DATASETS3 for x in pr_records[(cell, ds)]]
        )

    decoded_mask_iou_summary = {}
    for cell in CELLS:
        arr_gt = np.asarray(grid_ious_vs_gt[cell], dtype=np.float64)
        entry_iou: dict[str, Any] = dict(
            gt_anchor_evals=int(len(arr_gt)),
            mean_grid_iou_vs_gt=round(float(arr_gt.mean()), 4) if len(arr_gt) else None,
            median_grid_iou_vs_gt=round(float(np.median(arr_gt)), 4) if len(arr_gt) else None,
        )
        if cell in all_480_ious_vs_k:
            arr_k = np.asarray(all_480_ious_vs_k[cell], dtype=np.float64)
            entry_iou.update(
                k_anchors=int(len(arr_k)),
                mean_480_iou_vs_k=round(float(arr_k.mean()), 4) if len(arr_k) else None,
                median_480_iou_vs_k=round(float(np.median(arr_k)), 4) if len(arr_k) else None,
                iou_ge_095_rate_vs_k=round(float(np.mean(arr_k >= 0.95)), 4) if len(arr_k) else None,
            )
        decoded_mask_iou_summary[cell] = entry_iou

    # Decision table evaluation (PRICING_C2_C3.md L50-56)
    v_07 = all_stat["verdict_vs_k_j1t"]["kB_0.7"]
    v_05 = all_stat["verdict_vs_k_j1t"]["kB_0.5"]
    if v_07 == "holds" and v_05 == "holds":
        c3_action = "GO: candidate 3 pilot at box bar IoU 0.5; full fit may follow"
        c3_box_bar = 0.5
    elif v_07 == "holds":
        c3_action = "GO: candidate 3 pilot at box bar IoU 0.7; full fit may follow"
        c3_box_bar = 0.7
    elif v_07 == "unclear" and v_05 == "holds":
        c3_action = "GO (PILOT): candidate 3 pilot at box bar IoU 0.5; full fit waits for orchestrator with curve"
        c3_box_bar = 0.5
    elif v_07 == "unclear":
        c3_action = "GO (PILOT): candidate 3 pilot at box bar IoU 0.7; full fit waits for orchestrator with curve"
        c3_box_bar = 0.7
    else:
        c3_action = "STOP/RETURN: kB(0.7) breaks; return to orchestrator before pilot training"
        c3_box_bar = None

    return dict(
        schema="j1t-relift-v1",
        status="complete" if parity_gate_passed else "PARITY_FAILED",
        parity_gate=dict(
            passed=parity_gate_passed,
            k_prime_anchors_ge_095=k_prime_pass_n,
            k_prime_anchors_total=k_prime_total,
            k_prime_anchor_rate=round(k_prime_rate, 4),
            k_prime_min_iou=round(float(k_prime_ious.min()), 4) if len(k_prime_ious) else None,
            k_prime_minus_k_mra=round(k_prime_minus_k_mean, 4),
            exact_item_score_matches=f"{exact_item_score_matches}/{len(out_rows)}",
            exact_item_gap_matches=f"{exact_item_gap_matches}/{len(out_rows)}",
        ),
        decision=dict(
            kB_07_verdict=v_07,
            kB_07_s2_verdict=all_stat["verdict_vs_k_j1t"]["kB_0.7_s2"],
            kB_05_verdict=v_05,
            c3_box_bar=c3_box_bar,
            action=c3_action,
        ),
        sampler_summary=prompts_j1t["sampler_summary"],
        decoded_mask_iou_summary=decoded_mask_iou_summary,
        statistics=statistics,
        precision_recall=precision_recall,
        rows=out_rows,
    )


def format_ci(m: dict[str, Any], signed: bool = True) -> str:
    if m["mean"] is None:
        return "n/a"
    fmt = "%+.2f [%+.2f, %+.2f]" if signed else "%.2f [%.2f, %.2f]"
    return fmt % (m["mean"], m["ci95"][0], m["ci95"][1])


def render_markdown(res: dict[str, Any]) -> str:
    pg = res["parity_gate"]
    dec = res["decision"]
    s_all = res["statistics"][0]
    L = [
        "# RELIFT_J1T: Registered SAM 3 Box-Tolerance & Presence Diagnostic on DEV-MASK 117",
        "",
        f"- **Status:** `{res['status']}` | **k' Parity Gate:** `{pg['k_prime_anchors_ge_095']}/{pg['k_prime_anchors_total']}` (`{pg['k_prime_anchor_rate']*100:.2f}% >= 95%`, `min_iou = {pg['k_prime_min_iou']}`), `|(k'-a)-(k-a)| = {abs(pg['k_prime_minus_k_mra']):.3f} <= 0.5`, exact item MRA matches `{pg['exact_item_score_matches']}` (`PASS = {pg['passed']}`).",
        f"- **J1-T Registered Decision (`PRICING_C2_C3.md` L44-57):** `kB(0.7)` = **`{dec['kB_07_verdict']}`** (`kB(0.7)/s2` = **`{dec['kB_07_s2_verdict']}`**), `kB(0.5)` = **`{dec['kB_05_verdict']}`** -> **`{dec['action']}`**.",
        "",
        "## 1. All-117 Paired DEV-MASK Distance-MRA Table (35 Physical Rooms, 10,000-Draw Room Bootstrap)",
        "",
        "| Arm | Prompt Box IoU | Decoded Mask IoU vs GT | MRA (x100) | X - a (vs Served) | D(t) = X - k (vs Box Oracle) | Share of (e - a) | Share of (k - a) | Frame Prec / Rec | Empty-GT Masks | Refusals | Verdict (vs k / vs a) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    arm_labels = [
        ("a", "served", "served"),
        ("e", "1.000 (GT mask)", "e (GT ceiling)"),
        ("k", "1.000 (J1 banked)", "k (J1 box oracle)"),
        ("k_prime", "1.000 (recomputed)", "k' (parity gate)"),
        ("kB_0.9", "0.900", "kB(0.9)"),
        ("kB_0.7", "0.700 (seed 1)", "kB(0.7)"),
        ("kB_0.7_s2", "0.700 (seed 2)", "kB(0.7)/s2"),
        ("kB_0.5", "0.500", "kB(0.5)"),
        ("kP_miss", "1.000 (area>=1%)", "kP-miss (drop <1%)"),
        ("kP_fp", "1.000 + h1 FPs", "kP-fp (+810 h1 FP boxes)"),
        ("k_notower", "1.000 (0 SAM 3)", "k_notower (raw box grid)"),
    ]

    for key, box_desc, label in arm_labels:
        cell_m = format_ci(s_all["cells"][key], signed=False)
        vs_a_m = "0.00 (baseline)" if key == "a" else format_ci(s_all["versus_a"][f"{key}-a"], signed=True)
        if key == "k":
            vs_k_m = "0.00 (oracle)"
        elif f"{key}-k" in s_all["versus_k"]:
            vs_k_m = format_ci(s_all["versus_k"][f"{key}-k"], signed=True)
        else:
            vs_k_m = "n/a"
        sh_e = "n/a" if key in ("a", "e") else f"{s_all['share_of_e_minus_a'][key]['mean']:.2f}"
        sh_k = "n/a" if key in ("a", "e", "k") else f"{s_all['share_of_k_minus_a'][key]['mean']:.2f}"
        pr = res["precision_recall"][key]["all"]
        pr_str = f"{pr['precision']:.3f} / {pr['recall']:.3f}"
        empty_fp = pr["pred_on_empty_gt"]
        ref_n = s_all["refusals"][key]
        miou = res["decoded_mask_iou_summary"][key]["mean_grid_iou_vs_gt"]
        miou_str = f"{miou:.3f}" if miou is not None else "n/a"
        if key in ("a", "e"):
            v_str = "baseline" if key == "a" else "GT ceiling"
        elif key == "k":
            v_str = f"— / {s_all['verdict_vs_a']['k']}"
        else:
            v_str = f"{s_all['verdict_vs_k_j1t'][key]} / {s_all['verdict_vs_a'][key]}"
        L.append(
            f"| **{label}** | `{box_desc}` | `{miou_str}` | `{cell_m}` | `{vs_a_m}` | `{vs_k_m}` | `{sh_e}` | `{sh_k}` | `{pr_str}` | `{empty_fp}` | `{ref_n}` | **{v_str}** |"
        )

    L += [
        "",
        "## 2. Per-Dataset Paired Deltas (`X - a` and `X - k`)",
        "",
        "| Dataset | Items | Rooms | k' - a | kB(0.9) - a | kB(0.7) - a | kB(0.7)/s2 - a | kB(0.5) - a | kP-miss - a | kP-fp - a | k_notower - a | e - a |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for s in res["statistics"]:
        ds_label = f"**{s['dataset']} (decides)**" if s["decides"] else s["dataset"]
        cols = [
            format_ci(s["versus_a"][f"{arm}-a"])
            for arm in ("k_prime", "kB_0.9", "kB_0.7", "kB_0.7_s2", "kB_0.5", "kP_miss", "kP_fp", "k_notower", "e")
        ]
        L.append(f"| {ds_label} | {s['n']} | {s['rooms']} | " + " | ".join(f"`{c}`" for c in cols) + " |")

    L += [
        "",
        "| Dataset | Items | Rooms | k' - k | kB(0.9) - k | kB(0.7) - k | kB(0.7)/s2 - k | kB(0.5) - k | kP-miss - k | kP-fp - k | k_notower - k |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for s in res["statistics"]:
        ds_label = f"**{s['dataset']} (decides)**" if s["decides"] else s["dataset"]
        cols = [
            format_ci(s["versus_k"][f"{arm}-k"])
            for arm in ("k_prime", "kB_0.9", "kB_0.7", "kB_0.7_s2", "kB_0.5", "kP_miss", "kP_fp", "k_notower")
        ]
        L.append(f"| {ds_label} | {s['n']} | {s['rooms']} | " + " | ".join(f"`{c}`" for c in cols) + " |")

    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--j1t-dir", type=Path, default=Path("/scratch/jjyeung/orch_home_distill/work_e03_e04/out_j1t_full"))
    args = ap.parse_args(argv)

    res = evaluate_j1t(args.j1t_dir)
    out_json = args.j1t_dir / "RELIFT_J1T.json"
    out_md = args.j1t_dir / "RELIFT_J1T.md"
    G.write_json(out_json, res)
    md_text = render_markdown(res)
    out_md.write_text(md_text)
    print(md_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
