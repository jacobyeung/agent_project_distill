#!/usr/bin/env python3
"""End-to-End Leak-Free E05 v2 Gemini API Spatial/4D Data Factory Runner (`pilot0_runner.py`).

Executes the 4-Gate Verification Funnel on strictly train-only local NVMe scenes:
  - Gate G0 (Fail-Closed Leakage Guard): 11/11 startup canary asserts + room/venue/corpus check
    against BENCH v2, ReSTI ScanNet (0000..0149), R0-dev (100), R0-rl (272), dev-S1,
    SHA256-pinned K1-heldout, and withheld-80.
  - Gate G1 (Physical Calibration): Real raster containment half-extent calibration across ALL
    datasets (no blanket 2x shortcut, explicit no_raster rejection) + orthonormalized OBB axes +
    real multi-view ray parallax & baseline ratio computation.
  - Gate G3 (Blind Argon+Carbon Native Grounding): Independent image-first 0-1000 box_2d
    verification on raw keyframes (IoU agreement + referent unambiguity; never averages disjoint
    multi-instance boxes); exports agreed boxes for Candidate-3 (OWNHEAD) training and feeds live
    consensus box_hint into UNSEEN recovery.
  - Gate G2 + G4 (Carbon/Neon Trace Authoring + Deterministic Python Recompute): Authors concise
    (<250-token) SPLIT + GeoAPI-v2 traces with zero GT leaks in <tool_obs>, real AND parallax gate,
    and pure-Python recompute verification for 0 arithmetic, trig, sign, or unit-conversion errors.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

FACTORY_DIR = Path(__file__).resolve().parent
if str(FACTORY_DIR) not in sys.path:
    sys.path.insert(0, str(FACTORY_DIR))

from exclusions import DEFAULT_PINNED_TRAIN, RoomExclusionGuard
from gemini_client import (
    GeminiInlineClient,
    build_contact_sheet_jpeg_b64,
    encode_frame_jpeg_b64,
)
from geo_solver import (
    PARAPHRASE_TEMPLATES,
    SKIP_STRUCTURAL_LABELS,
    UNIT_NAMES,
    GeoAPIV2Session,
    ObjectInstance3D,
    Scene3DGraph,
    camera_horizontal_axes,
    convert_length,
    ego_polar_metrics,
    format_scalar,
    obb_surface_gap_m,
    recompute_and_verify_trace,
)

DEFAULT_TRAIN_LABELS = Path("/scratch/jjyeung/orch_n30/sb_kbox4/train_labels.json")
DEFAULT_SMOKE_OUT = FACTORY_DIR / "pilot0_smoke.jsonl"
DEFAULT_SUMMARY_OUT = FACTORY_DIR / "pilot0_smoke_summary.json"
DEFAULT_BOXES_OUT = FACTORY_DIR / "pilot0_ownhead_boxes.jsonl"

UNITS_CYCLE = ("m", "cm", "ft", "in")

BUCKET_ORDER = (
    "unseen_recovery_dist",
    "facing_twins",
    "small_obj_size",
    "out_of_view_cam_k",
    "large_count",
    "multi_slot_disambig",
    "low_parallax_dist",
    "camera_motion",
    "relative_size",
    "clean_dist",
)

BUCKET_WEIGHTS: Dict[str, float] = {
    "unseen_recovery_dist": 0.08,
    "low_parallax_dist": 0.11,
    "clean_dist": 0.16,
    "small_obj_size": 0.10,
    "relative_size": 0.10,
    "out_of_view_cam_k": 0.11,
    "facing_twins": 0.12,
    "camera_motion": 0.09,
    "large_count": 0.06,
    "multi_slot_disambig": 0.07,
}


def _spatial_hint_from_box(box_1000: List[int]) -> str:
    yc = 0.5 * (box_1000[0] + box_1000[2])
    xc = 0.5 * (box_1000[1] + box_1000[3])
    v_part = "upper" if yc < 380 else ("lower" if yc > 620 else "middle")
    h_part = "left" if xc < 380 else ("right" if xc > 620 else "center")
    return f"located toward the {v_part}-{h_part} region of this view"


def _select_contact_frames(scene: Scene3DGraph, must_include: List[int], total: int = 6) -> List[Tuple[int, str]]:
    valid_1idx = [i + 1 for i, ok in enumerate(scene.valid_frames) if ok and i < len(scene.anchor_dense_paths)]
    chosen: List[int] = []
    for f in must_include:
        if f in valid_1idx and f not in chosen:
            chosen.append(f)
    if len(chosen) < total and valid_1idx:
        step = max(1, len(valid_1idx) // total)
        for f in valid_1idx[::step]:
            if f not in chosen:
                chosen.append(f)
            if len(chosen) >= total:
                break
        for f in valid_1idx:
            if len(chosen) >= total:
                break
            if f not in chosen:
                chosen.append(f)
    chosen.sort()
    return [(f, scene.anchor_dense_paths[f - 1]) for f in chosen[:total]]


def _is_clean_label(lab: str) -> bool:
    s = lab.strip().lower()
    return bool(s) and len(s) >= 2 and s not in SKIP_STRUCTURAL_LABELS and "wall" not in s and "floor" not in s


def _pick_template(family: str, rng: random.Random, **kwargs: Any) -> Tuple[str, int]:
    templates = PARAPHRASE_TEMPLATES[family]
    t_idx = rng.randrange(len(templates))
    return templates[t_idx].format(**kwargs), t_idx


def mine_candidate_specs(
    clean_captures: List[Dict[str, Any]],
    guard: RoomExclusionGuard,
    known_conventions: Dict[str, str],
    max_candidates: int = 64,
    seed: int = 20261128,
) -> Tuple[List[Dict[str, Any]], Dict[str, Scene3DGraph]]:
    """Mine diverse, prior-breaking & real OOF-recovery candidate specs across ALL clean captures.

    Scales proportionally to max_candidates (500 to 10,000+) with no hardcoded 48-scene / 102-row caps.
    """
    rng = random.Random(seed)

    # Stratified capture ordering across scannet, scannetpp, arkitscenes
    by_ds: Dict[str, List[Dict[str, Any]]] = {"arkitscenes": [], "scannet": [], "scannetpp": []}
    for cap in clean_captures:
        ds = cap["canonical"].split("/", 1)[0]
        by_ds.setdefault(ds, []).append(cap)
    for ds_list in by_ds.values():
        rng.shuffle(ds_list)

    interleaved: List[Dict[str, Any]] = []
    max_len = max((len(v) for v in by_ds.values()), default=0)
    for i in range(max_len):
        for ds in ("scannet", "scannetpp", "arkitscenes"):
            if i < len(by_ds[ds]):
                interleaved.append(by_ds[ds][i])

    # Load ALL clean captures (zero hardcoded 48-scene break)
    scenes_cache: Dict[str, Scene3DGraph] = {}
    ordered_canonicals: List[str] = []
    for cap in interleaved:
        verdict = guard.assert_clean(cap)
        canonical = verdict["canonical_scene"]
        try:
            scene = Scene3DGraph.from_capture(cap, known_conventions=known_conventions)
        except Exception:
            continue
        scenes_cache[canonical] = scene
        ordered_canonicals.append(canonical)

    # Proportional bucket caps that scale cleanly from 64 to 10,000+ candidates
    bucket_caps: Dict[str, int] = {}
    for bname, weight in BUCKET_WEIGHTS.items():
        raw_cap = int(math.ceil(max_candidates * weight * 1.8))
        bucket_caps[bname] = max(12, raw_cap)
        if bname == "facing_twins" and bucket_caps[bname] % 2 == 1:
            bucket_caps[bname] += 1

    buckets: Dict[str, List[Dict[str, Any]]] = {b: [] for b in BUCKET_ORDER}
    unit_cursor = 0

    def next_unit() -> str:
        nonlocal unit_cursor
        u = UNITS_CYCLE[unit_cursor % len(UNITS_CYCLE)]
        unit_cursor += 1
        return u

    # Per-scene candidate quota grows smoothly with max_candidates so 233 scenes easily supply 10,000+ specs
    n_scenes = max(1, len(ordered_canonicals))
    scene_mult = max(1, int(math.ceil(max_candidates / (n_scenes * 3.0))))
    seen_dedup: set[Tuple[Any, ...]] = set()

    def _total_mined() -> int:
        return sum(len(v) for v in buckets.values())

    # Pass 0 mines strictly unique (scene, operands, frame) items; if max_candidates > unique pool
    # (e.g. 10,000+), subsequent passes vary unit/paraphrase skins cleanly.
    max_passes = 1 if max_candidates <= 2000 else min(8, 1 + int(math.ceil(max_candidates / 1800.0)))

    for pass_idx in range(max_passes):
        if _total_mined() >= int(math.ceil(max_candidates * 1.35)):
            break

        for canonical in ordered_canonicals:
            scene = scenes_cache[canonical]
            singletons = [
                o for o in scene.instances
                if len(scene.by_label.get(o.label, [])) == 1
                and _is_clean_label(o.label)
                and o.best_frame_px >= 600
            ]
            rng.shuffle(singletons)

            # 1a. Real OOF UNSEEN recovery distance tasks (strictly lab in candidates.json with score < 0.30!)
            if len(singletons) >= 2 and len(buckets["unseen_recovery_dist"]) < bucket_caps["unseen_recovery_dist"]:
                real_unseen_objs = [
                    o for o in singletons
                    if o.oof_queried and o.oof_max_joint_score is not None and o.oof_max_joint_score < 0.30
                ]
                for oa in real_unseen_objs:
                    if len(buckets["unseen_recovery_dist"]) >= bucket_caps["unseen_recovery_dist"]:
                        break
                    partners = [o for o in singletons if o.instance_id != oa.instance_id]
                    rng.shuffle(partners)
                    added_for_oa = 0
                    max_unseen_partners = max(4, scene_mult * 3)
                    for ob in partners:
                        if added_for_oa >= max_unseen_partners or len(buckets["unseen_recovery_dist"]) >= bucket_caps["unseen_recovery_dist"]:
                            break
                        u = next_unit()
                        dkey = ("unseen", canonical, oa.instance_id, ob.instance_id, u if pass_idx > 0 else 0, pass_idx)
                        if dkey in seen_dedup:
                            continue
                        gap_m = obb_surface_gap_m(oa.as_box_dict(), ob.as_box_dict())
                        if gap_m < 0.20:
                            continue
                        seen_dedup.add(dkey)
                        u_long, u_short = UNIT_NAMES[u]
                        val_u, val_str = format_scalar(convert_length(gap_m, u), u)
                        prompt, tidx = _pick_template(
                            "metric_distance", rng, a=oa.label, b=ob.label, unit_long=u_long, unit_short=u_short
                        )
                        buckets["unseen_recovery_dist"].append({
                            "canonical_scene": canonical,
                            "task_family": "metric_distance",
                            "epistemic_mode": "UNSEEN_BOX_HINT_RECOVERY",
                            "stream": "S1_epistemic_recovery",
                            "unit": u,
                            "template_idx": tidx,
                            "prompt": prompt,
                            "verify_targets": [(oa, True), (ob, False)],
                            "simulated_modes": {oa.label: "UNSEEN", ob.label: "OK"},
                            "operands": [oa.label, ob.label],
                            "inspect_frame": oa.best_frame,
                            "must_frames": [oa.best_frame, ob.best_frame],
                            "gt_solver": {
                                "op": "surface_gap",
                                "raw_m": round(gap_m, 6),
                                "unit": u,
                                "exact_val": val_u,
                                "canonical_answer": val_str,
                                "answer_type": "numeric",
                            },
                        })
                        added_for_oa += 1

            # 1b. Real LOW_PARALLAX wide-baseline recovery distance tasks (enforces real narrow + real AND wide pair)
            if len(singletons) >= 2 and len(buckets["low_parallax_dist"]) < bucket_caps["low_parallax_dist"]:
                lp_added = 0
                lp_limit = max(2, scene_mult)
                for idx_a, oa in enumerate(singletons):
                    if lp_added >= lp_limit or len(buckets["low_parallax_dist"]) >= bucket_caps["low_parallax_dist"]:
                        break
                    if len(oa.vis_frames) < 3:
                        continue
                    narrow_pair, wide_pair = scene.find_narrow_and_wide_pairs(oa)
                    if narrow_pair is None or wide_pair is None:
                        continue
                    for ob in singletons[idx_a + 1:] + singletons[:idx_a]:
                        if ob.instance_id == oa.instance_id:
                            continue
                        u = next_unit()
                        dkey = ("low_par", canonical, oa.instance_id, ob.instance_id, u if pass_idx > 0 else 0, pass_idx)
                        if dkey in seen_dedup:
                            continue
                        gap_m = obb_surface_gap_m(oa.as_box_dict(), ob.as_box_dict())
                        if gap_m < 0.20:
                            continue
                        seen_dedup.add(dkey)
                        u_long, u_short = UNIT_NAMES[u]
                        val_u, val_str = format_scalar(convert_length(gap_m, u), u)
                        prompt, tidx = _pick_template(
                            "metric_distance", rng, a=oa.label, b=ob.label, unit_long=u_long, unit_short=u_short
                        )
                        buckets["low_parallax_dist"].append({
                            "canonical_scene": canonical,
                            "task_family": "metric_distance",
                            "epistemic_mode": "LOW_PARALLAX_WIDE_BASELINE",
                            "stream": "S1_epistemic_recovery",
                            "unit": u,
                            "template_idx": tidx,
                            "prompt": prompt,
                            "verify_targets": [(oa, False), (ob, False)],
                            "simulated_modes": {oa.label: "LOW_PARALLAX", ob.label: "OK"},
                            "operands": [oa.label, ob.label],
                            "narrow_frames": [narrow_pair[0], narrow_pair[1]],
                            "wide_frames": [wide_pair[0], wide_pair[1]],
                            "must_frames": [narrow_pair[0], wide_pair[0], wide_pair[1], ob.best_frame],
                            "gt_solver": {
                                "op": "surface_gap",
                                "raw_m": round(gap_m, 6),
                                "unit": u,
                                "exact_val": val_u,
                                "canonical_answer": val_str,
                                "answer_type": "numeric",
                            },
                        })
                        lp_added += 1
                        break

            # 1c. Clean 1-pass metric distance tasks across multiple singleton pairs
            if len(singletons) >= 2 and len(buckets["clean_dist"]) < bucket_caps["clean_dist"]:
                cd_added = 0
                cd_limit = max(3, scene_mult * 2)
                for i_a in range(len(singletons)):
                    if cd_added >= cd_limit or len(buckets["clean_dist"]) >= bucket_caps["clean_dist"]:
                        break
                    for i_b in range(i_a + 1, len(singletons)):
                        if cd_added >= cd_limit or len(buckets["clean_dist"]) >= bucket_caps["clean_dist"]:
                            break
                        oa, ob = singletons[i_a], singletons[i_b]
                        pair_id = tuple(sorted((oa.instance_id, ob.instance_id)))
                        u = next_unit()
                        dkey = ("clean_dist", canonical, pair_id, u if pass_idx > 0 else 0, pass_idx)
                        if dkey in seen_dedup:
                            continue
                        gap_m = obb_surface_gap_m(oa.as_box_dict(), ob.as_box_dict())
                        if gap_m < 0.20:
                            continue
                        seen_dedup.add(dkey)
                        u_long, u_short = UNIT_NAMES[u]
                        val_u, val_str = format_scalar(convert_length(gap_m, u), u)
                        prompt, tidx = _pick_template(
                            "metric_distance", rng, a=oa.label, b=ob.label, unit_long=u_long, unit_short=u_short
                        )
                        buckets["clean_dist"].append({
                            "canonical_scene": canonical,
                            "task_family": "metric_distance",
                            "epistemic_mode": "CLEAN_1PASS",
                            "stream": "S2_prior_breaker_phrasing",
                            "unit": u,
                            "template_idx": tidx,
                            "prompt": prompt,
                            "verify_targets": [(oa, False), (ob, False)],
                            "simulated_modes": {oa.label: "OK", ob.label: "OK"},
                            "operands": [oa.label, ob.label],
                            "must_frames": [oa.best_frame, ob.best_frame],
                            "gt_solver": {
                                "op": "surface_gap",
                                "raw_m": round(gap_m, 6),
                                "unit": u,
                                "exact_val": val_u,
                                "canonical_answer": val_str,
                                "answer_type": "numeric",
                            },
                        })
                        cd_added += 1

            # 2a. Small object (<30 cm) oriented size across ALL small singletons in the scene
            small_objs = [
                o for o in singletons
                if 0.08 <= o.sorted_extents_m()[0] < 0.30 and o.best_frame_px >= 450
            ]
            large_objs = [
                o for o in singletons
                if o.sorted_extents_m()[0] >= 0.55 and o.best_frame_px >= 700
            ]
            if small_objs and len(buckets["small_obj_size"]) < bucket_caps["small_obj_size"]:
                so_limit = max(2, scene_mult)
                so_added = 0
                for so in small_objs:
                    if so_added >= so_limit or len(buckets["small_obj_size"]) >= bucket_caps["small_obj_size"]:
                        break
                    u = rng.choice(["cm", "in", "m", "ft"])
                    dkey = ("small_size", canonical, so.instance_id, u if pass_idx > 0 else 0, pass_idx)
                    if dkey in seen_dedup:
                        continue
                    seen_dedup.add(dkey)
                    u_long, u_short = UNIT_NAMES[u]
                    max_m = so.sorted_extents_m()[0]
                    val_u, val_str = format_scalar(convert_length(max_m, u), u)
                    prompt, tidx = _pick_template(
                        "small_object_size", rng, a=so.label, unit_long=u_long, unit_short=u_short
                    )
                    buckets["small_obj_size"].append({
                        "canonical_scene": canonical,
                        "task_family": "small_object_size_lt30cm",
                        "epistemic_mode": "CLEAN_1PASS",
                        "stream": "S2_prior_breaker_phrasing",
                        "unit": u,
                        "template_idx": tidx,
                        "prompt": prompt,
                        "verify_targets": [(so, False)],
                        "simulated_modes": {so.label: "OK"},
                        "operands": [so.label],
                        "must_frames": [so.best_frame],
                        "gt_solver": {
                            "op": "obb_size",
                            "raw_m": round(max_m, 6),
                            "unit": u,
                            "exact_val": val_u,
                            "canonical_answer": val_str,
                            "answer_type": "numeric",
                        },
                    })
                    so_added += 1

            # 2b. Relative size neighbor guard (small vs large first, then any clean margin >= 0.25m)
            if len(singletons) >= 2 and len(buckets["relative_size"]) < bucket_caps["relative_size"]:
                rs_added = 0
                rs_limit = max(2, scene_mult)
                cand_pairs: List[Tuple[ObjectInstance3D, ObjectInstance3D]] = []
                for so in small_objs:
                    for lo in large_objs:
                        cand_pairs.append((so, lo))
                if not cand_pairs:
                    for i_a in range(len(singletons)):
                        for i_b in range(i_a + 1, len(singletons)):
                            ea = singletons[i_a].sorted_extents_m()[0]
                            eb = singletons[i_b].sorted_extents_m()[0]
                            if abs(ea - eb) >= 0.25:
                                small_x, large_x = (
                                    (singletons[i_a], singletons[i_b]) if ea < eb else (singletons[i_b], singletons[i_a])
                                )
                                cand_pairs.append((small_x, large_x))
                rng.shuffle(cand_pairs)
                for so, lo in cand_pairs:
                    if rs_added >= rs_limit or len(buckets["relative_size"]) >= bucket_caps["relative_size"]:
                        break
                    pair_id = tuple(sorted((so.instance_id, lo.instance_id)))
                    dkey = ("rel_size", canonical, pair_id, pass_idx)
                    if dkey in seen_dedup:
                        continue
                    seen_dedup.add(dkey)
                    pair = [so, lo]
                    rng.shuffle(pair)
                    winner = lo.label
                    r_prompt, rtidx = _pick_template("relative_size", rng, a=pair[0].label, b=pair[1].label)
                    buckets["relative_size"].append({
                        "canonical_scene": canonical,
                        "task_family": "relative_size_neighbor_guard",
                        "epistemic_mode": "CLEAN_1PASS",
                        "stream": "S2_prior_breaker_phrasing",
                        "unit": "m",
                        "template_idx": rtidx,
                        "prompt": r_prompt,
                        "verify_targets": [(so, False), (lo, False)],
                        "simulated_modes": {so.label: "OK", lo.label: "OK"},
                        "operands": [pair[0].label, pair[1].label],
                        "must_frames": [so.best_frame, lo.best_frame],
                        "gt_solver": {
                            "op": "relative_size",
                            "raw_m": round(lo.sorted_extents_m()[0] - so.sorted_extents_m()[0], 6),
                            "unit": "m",
                            "exact_val": winner,
                            "canonical_answer": winner,
                            "answer_type": "categorical",
                        },
                    })
                    rs_added += 1

            # 3. Out-of-view persistent 3D ego_polar at camera@k (VSTI@k recovery)
            if singletons and len(buckets["out_of_view_cam_k"]) < bucket_caps["out_of_view_cam_k"]:
                oov_added = 0
                oov_limit = max(2, scene_mult)
                for target_o in singletons:
                    if oov_added >= oov_limit or len(buckets["out_of_view_cam_k"]) >= bucket_caps["out_of_view_cam_k"]:
                        break
                    unseen_frames = [
                        f_idx + 1
                        for f_idx in range(scene.n_anchors)
                        if scene.valid_frames[f_idx] and (f_idx + 1) not in target_o.frame_px
                    ]
                    if not unseen_frames:
                        continue
                    k_ref = unseen_frames[(len(unseen_frames) // 2 + pass_idx) % len(unseen_frames)]
                    u = next_unit()
                    dkey = ("oov_cam_k", canonical, target_o.instance_id, k_ref, pass_idx)
                    if dkey in seen_dedup:
                        continue
                    fwd_k, _ = camera_horizontal_axes(scene.c2w[k_ref - 1])
                    if np.linalg.norm(fwd_k) <= 1e-4:
                        continue
                    seen_dedup.add(dkey)
                    u_long, u_short = UNIT_NAMES[u]
                    pol = ego_polar_metrics(scene.c2w[k_ref - 1, :3, 3], fwd_k, target_o.centroid, unit=u)
                    _, r_str = format_scalar(pol["r_horiz"], u)
                    prompt, tidx = _pick_template(
                        "ego_polar_cam_k", rng, k=k_ref, a=target_o.label, unit_long=u_long, unit_short=u_short
                    )
                    buckets["out_of_view_cam_k"].append({
                        "canonical_scene": canonical,
                        "task_family": "ego_polar_out_of_view_cam_k",
                        "epistemic_mode": "OUT_OF_VIEW_PERSISTENT_3D",
                        "stream": "S1_epistemic_recovery",
                        "unit": u,
                        "template_idx": tidx,
                        "prompt": prompt,
                        "verify_targets": [(target_o, False)],
                        "simulated_modes": {target_o.label: "OK"},
                        "operands": [target_o.label],
                        "ref_frame_k": k_ref,
                        "must_frames": [k_ref, target_o.best_frame],
                        "gt_solver": {
                            "op": "ego_polar_cam_k",
                            "raw_m": pol["r_horiz_m"],
                            "bearing_deg": pol["bearing_deg"],
                            "dz_m": pol["dz_m"],
                            "unit": u,
                            "exact_val": pol["r_horiz"],
                            "canonical_answer": r_str,
                            "answer_type": "numeric",
                        },
                    })
                    oov_added += 1

            # 4. Chiral 180-deg facing='toward' & facing='away' twin pairs (margin >= 15 deg!)
            if len(singletons) >= 3 and len(buckets["facing_twins"]) + 1 < bucket_caps["facing_twins"]:
                ft_added = 0
                ft_limit = max(2, scene_mult)
                n_s = len(singletons)
                for tri_i in range(min(n_s, 6)):
                    if ft_added >= ft_limit or len(buckets["facing_twins"]) + 1 >= bucket_caps["facing_twins"]:
                        break
                    oa = singletons[tri_i]
                    ob = singletons[(tri_i + 1) % n_s]
                    oc = singletons[(tri_i + 2) % n_s]
                    if len({oa.instance_id, ob.instance_id, oc.instance_id}) < 3:
                        continue
                    dkey = ("facing", canonical, oa.instance_id, ob.instance_id, oc.instance_id, pass_idx)
                    if dkey in seen_dedup:
                        continue
                    ab_xy = oa.centroid[:2] - ob.centroid[:2]
                    ac_xy = oc.centroid[:2] - oa.centroid[:2]
                    if np.linalg.norm(ab_xy) < 0.60 or np.linalg.norm(ac_xy) < 0.60:
                        continue
                    fwd_ab = np.array([ob.centroid[0] - oa.centroid[0], ob.centroid[1] - oa.centroid[1], 0.0])
                    pol_toward = ego_polar_metrics(oa.centroid, fwd_ab, oc.centroid, facing="toward")
                    pol_away = ego_polar_metrics(oa.centroid, fwd_ab, oc.centroid, facing="away")
                    if pol_toward["boundary_margin_deg"] < 15.0:
                        continue
                    seen_dedup.add(dkey)
                    for facing_mode, phrase, pol in [
                        ("toward", "toward", pol_toward),
                        ("away", "away from", pol_away),
                    ]:
                        prompt, tidx = _pick_template(
                            "facing_direction",
                            rng,
                            a=oa.label,
                            b=ob.label,
                            c=oc.label,
                            facing_phrase=phrase,
                        )
                        buckets["facing_twins"].append({
                            "canonical_scene": canonical,
                            "task_family": f"chiral_direction_{facing_mode}",
                            "epistemic_mode": "CHIRAL_180_TWIN",
                            "stream": "S5_adversarial_twins",
                            "unit": "deg",
                            "template_idx": tidx,
                            "prompt": prompt,
                            "verify_targets": [(oa, False), (ob, False), (oc, False)],
                            "simulated_modes": {oa.label: "OK", ob.label: "OK", oc.label: "OK"},
                            "operands": [oa.label, ob.label, oc.label],
                            "facing": facing_mode,
                            "must_frames": [oa.best_frame, ob.best_frame, oc.best_frame],
                            "gt_solver": {
                                "op": "ego_polar_quadrant",
                                "facing": facing_mode,
                                "bearing_deg": pol["bearing_deg"],
                                "boundary_margin_deg": pol["boundary_margin_deg"],
                                "exact_val": pol["quadrant_4way"],
                                "canonical_answer": pol["quadrant_4way"],
                                "answer_type": "categorical",
                            },
                        })
                    ft_added += 1

            # 5. Camera SE(3) motion (multiple intervals per capture, forward & time-reversed)
            valid_f = [i + 1 for i, ok in enumerate(scene.valid_frames) if ok]
            if len(valid_f) >= 12 and len(buckets["camera_motion"]) < bucket_caps["camera_motion"] and singletons:
                cm_added = 0
                cm_limit = max(2, scene_mult)
                n_vf = len(valid_f)
                candidate_intervals = [
                    (valid_f[2], valid_f[-3]),
                    (valid_f[0], valid_f[n_vf // 2]),
                    (valid_f[n_vf // 2], valid_f[-1]),
                    (valid_f[n_vf // 4], valid_f[(3 * n_vf) // 4]),
                ]
                rng.shuffle(candidate_intervals)
                for t_early, t_late in candidate_intervals:
                    if cm_added >= cm_limit or len(buckets["camera_motion"]) >= bucket_caps["camera_motion"]:
                        break
                    if abs(t_late - t_early) < 4:
                        continue
                    reverse = (len(buckets["camera_motion"]) % 2 == 1)
                    t0, t1 = (t_late, t_early) if reverse else (t_early, t_late)
                    u = next_unit()
                    dkey = ("cam_mot", canonical, t0, t1, u if pass_idx > 0 else 0, pass_idx)
                    if dkey in seen_dedup:
                        continue
                    mot = scene.camera_motion(t0, t1, unit="m")
                    if mot["disp_m"] < 0.65:
                        continue
                    seen_dedup.add(dkey)
                    u_long, u_short = UNIT_NAMES[u]
                    mot_u = scene.camera_motion(t0, t1, unit=u)
                    _, disp_str = format_scalar(mot_u["disp"], u)
                    prompt, tidx = _pick_template(
                        "camera_motion", rng, t0=t0, t1=t1, unit_long=u_long, unit_short=u_short
                    )
                    buckets["camera_motion"].append({
                        "canonical_scene": canonical,
                        "task_family": "camera_motion_reversed" if reverse else "camera_motion_forward",
                        "epistemic_mode": "TEMPORAL_REVERSAL_INVARIANCE" if reverse else "CLEAN_1PASS",
                        "stream": "S2_prior_breaker_phrasing",
                        "unit": u,
                        "template_idx": tidx,
                        "prompt": prompt,
                        "verify_targets": [(singletons[0], False)],
                        "simulated_modes": {},
                        "operands": ["camera"],
                        "t0": t0,
                        "t1": t1,
                        "must_frames": [min(t0, t1), max(t0, t1)],
                        "gt_solver": {
                            "op": "camera_motion",
                            "raw_m": mot_u["disp_m"],
                            "yaw_deg": mot_u["yaw_deg"],
                            "unit": u,
                            "exact_val": mot_u["disp"],
                            "canonical_answer": disp_str,
                            "answer_type": "numeric",
                        },
                    })
                    cm_added += 1

            # 6. Large-set counting (count >= 5) & multi-instance disambiguation (randomized slot index!)
            cats_shuffled = list(scene.by_label.items())
            rng.shuffle(cats_shuffled)
            for cat, objs in cats_shuffled:
                if not _is_clean_label(cat):
                    continue
                anchor_rep = max(objs, key=lambda o: o.best_frame_px)
                if (
                    len(objs) >= 5
                    and anchor_rep.best_frame_px >= 500
                    and len(buckets["large_count"]) < bucket_caps["large_count"]
                ):
                    dkey = ("large_count", canonical, cat, pass_idx)
                    if dkey not in seen_dedup:
                        seen_dedup.add(dkey)
                        prompt, tidx = _pick_template("large_set_count", rng, a=cat)
                        buckets["large_count"].append({
                            "canonical_scene": canonical,
                            "task_family": "large_set_count_ge5",
                            "epistemic_mode": "MULTI_SLOT_DEDUP_COUNT",
                            "stream": "S2_prior_breaker_phrasing",
                            "unit": "count",
                            "template_idx": tidx,
                            "prompt": prompt,
                            "verify_targets": [(anchor_rep, False)],
                            "simulated_modes": {cat: "MULTI_SLOT"},
                            "operands": [cat],
                            "must_frames": sorted({o.first_frame for o in objs[:6]}),
                            "gt_solver": {
                                "op": "count_3d_instances",
                                "exact_val": len(objs),
                                "canonical_answer": str(len(objs)),
                                "first_seen_frames": [o.first_frame for o in objs],
                                "answer_type": "integer",
                            },
                        })
                elif (
                    2 <= len(objs) <= 4
                    and singletons
                    and anchor_rep.best_frame_px >= 600
                    and len(buckets["multi_slot_disambig"]) < bucket_caps["multi_slot_disambig"]
                ):
                    # Pick instances whose first_frame is UNIQUE within objs, then RANDOMIZE slot index!
                    first_counts = Counter(o.first_frame for o in objs)
                    unique_first_objs = [o for o in objs if first_counts[o.first_frame] == 1 and o.best_frame_px >= 450]
                    if not unique_first_objs:
                        continue
                    rng.shuffle(unique_first_objs)
                    chosen_inst = unique_first_objs[0]
                    ref_candidates = [s for s in singletons if s.label != cat]
                    rng.shuffle(ref_candidates)
                    for ref_b in ref_candidates[:max(1, scene_mult)]:
                        if len(buckets["multi_slot_disambig"]) >= bucket_caps["multi_slot_disambig"]:
                            break
                        u = next_unit()
                        dkey = ("multi_disambig", canonical, chosen_inst.instance_id, ref_b.instance_id, pass_idx)
                        if dkey in seen_dedup:
                            continue
                        gap_m = obb_surface_gap_m(chosen_inst.as_box_dict(), ref_b.as_box_dict())
                        if gap_m < 0.15:
                            continue
                        seen_dedup.add(dkey)
                        u_long, u_short = UNIT_NAMES[u]
                        val_u, val_str = format_scalar(convert_length(gap_m, u), u)
                        prompt, tidx = _pick_template(
                            "multi_instance_disambig",
                            rng,
                            a=cat,
                            first_f=chosen_inst.first_frame,
                            b=ref_b.label,
                            unit_long=u_long,
                            unit_short=u_short,
                        )
                        buckets["multi_slot_disambig"].append({
                            "canonical_scene": canonical,
                            "task_family": "multi_instance_disambig",
                            "epistemic_mode": "MULTI_SLOT_DISAMBIG",
                            "stream": "S1_epistemic_recovery",
                            "unit": u,
                            "template_idx": tidx,
                            "prompt": prompt,
                            "verify_targets": [(chosen_inst, False), (ref_b, False)],
                            "simulated_modes": {cat: "MULTI_SLOT", ref_b.label: "OK"},
                            "operands": [cat, ref_b.label],
                            "target_slot_id": chosen_inst.slot_id,
                            "target_slot_index": objs.index(chosen_inst),
                            "target_first_frame": chosen_inst.first_frame,
                            "must_frames": [chosen_inst.first_frame, chosen_inst.best_frame, ref_b.best_frame],
                            "gt_solver": {
                                "op": "surface_gap_disambig",
                                "raw_m": round(gap_m, 6),
                                "unit": u,
                                "exact_val": val_u,
                                "canonical_answer": val_str,
                                "answer_type": "numeric",
                            },
                        })

    # Round-robin interleave across all 10 task/epistemic buckets for balanced coverage
    ordered_specs: List[Dict[str, Any]] = []
    idx = 0
    while len(ordered_specs) < max_candidates:
        added_any = False
        for bname in BUCKET_ORDER:
            blist = buckets[bname]
            if bname == "facing_twins":
                # Keep toward/away twin pairs adjacent
                pair_pos = idx * 2
                if pair_pos + 1 < len(blist) and len(ordered_specs) + 2 <= max_candidates:
                    ordered_specs.append(blist[pair_pos])
                    ordered_specs.append(blist[pair_pos + 1])
                    added_any = True
            elif idx < len(blist):
                ordered_specs.append(blist[idx])
                added_any = True
            if len(ordered_specs) >= max_candidates:
                break
        if not added_any:
            break
        idx += 1

    return ordered_specs, scenes_cache


def build_scaffold_calls(
    scene: Scene3DGraph,
    spec: Dict[str, Any],
    consensus_boxes: Dict[str, List[int]],
) -> List[Dict[str, Any]]:
    """Construct exact deterministic GeoAPI-v2 call sequence and pre-execute tool responses."""
    fam = spec["task_family"]
    mode = spec["epistemic_mode"]
    u = spec["unit"]
    session = GeoAPIV2Session(scene, simulated_modes=spec.get("simulated_modes"))
    steps: List[Dict[str, Any]] = []

    def add_call(calls: List[Dict[str, Any]], default_think: str) -> List[Dict[str, Any]]:
        outs = [session.execute_call(c) for c in calls]
        raw_call = "<geo>" + " ; ".join(json.dumps(c, separators=(",", ":")) for c in calls) + "</geo>"
        payload = outs[0] if len(outs) == 1 else {"batch": outs}
        key = "tool_obs" if all(c.get("op") == "inspect" for c in calls) else "tool_response"
        steps.append({
            "call": raw_call,
            key: json.dumps(payload, separators=(",", ":")),
            "default_think": default_think,
        })
        return outs

    if fam == "metric_distance":
        a, b = spec["operands"]
        r1 = add_call(
            [{"op": "locate", "q": a}, {"op": "locate", "q": b}],
            f"Intent: surface_gap({a}, {b}, unit={u}). Locate both objects in 3D.",
        )
        if mode == "UNSEEN_BOX_HINT_RECOVERY":
            # Student selects visible frame from video/contact sheet (NEVER leaked by locate!)
            f_vis = int(spec["inspect_frame"])
            add_call(
                [{"op": "inspect", "frame": f_vis, "view": "rgb"}],
                f"{a} returned UNSEEN (OOF score {r1[0].get('oof_joint_score')}); inspect RGB frame {f_vis} to localize a tight 2D box_hint visually.",
            )
            c_box = consensus_boxes.get(a) or scene.by_label[a][0].frame_boxes_1000[f_vis]
            r_loc = add_call(
                [{"op": "locate", "q": a, "box_hint": [f_vis, *c_box]}],
                f"Visual inspection of frame {f_vis} localizes {a} at {c_box}; re-run locate with box_hint.",
            )
            sa = r_loc[0]["slots"][0]["id"]
            sb = r1[1]["slots"][0]["id"]
        elif mode == "LOW_PARALLAX_WIDE_BASELINE":
            # Student selects wide-baseline frames from multi-view video (enforces real AND parallax gate!)
            f_w1, f_w2 = [int(x) for x in spec["wide_frames"]]
            r_loc = add_call(
                [{"op": "locate", "q": a, "frames": [f_w1, f_w2]}],
                f"{a} returned LOW_PARALLAX ({r1[0].get('parallax_deg')} deg, beta={r1[0].get('baseline_ratio_beta')}); re-triangulate with wide-baseline frames {f_w1} and {f_w2}.",
            )
            if r_loc[0].get("status") != "OK":
                raise RuntimeError(f"Wide-baseline frames {[f_w1, f_w2]} failed parallax gate: {r_loc[0]}")
            sa = r_loc[0]["slots"][0]["id"]
            sb = r1[1]["slots"][0]["id"]
        else:
            sa = r1[0]["slots"][0]["id"]
            sb = r1[1]["slots"][0]["id"]

        add_call(
            [{"op": "measure", "op_type": "surface_gap", "a": sa, "b": sb, "unit": u}],
            f"Measure 5 cm surface gap between {sa} and {sb} in {u}.",
        )

    elif fam == "small_object_size_lt30cm":
        a = spec["operands"][0]
        r1 = add_call([{"op": "locate", "q": a}], f"Intent: obb_size({a}, unit={u}). Locate target.")
        sa = r1[0]["slots"][0]["id"]
        add_call(
            [{"op": "measure", "op_type": "obb_size", "a": sa, "unit": u}],
            f"Read full calibrated 3D OBB longest extent of {sa} in {u}.",
        )

    elif fam == "relative_size_neighbor_guard":
        a, b = spec["operands"]
        r1 = add_call(
            [{"op": "locate", "q": a}, {"op": "locate", "q": b}],
            f"Intent: relative_size({a}, {b}). Locate both 3D boxes.",
        )
        sa, sb = r1[0]["slots"][0]["id"], r1[1]["slots"][0]["id"]
        add_call(
            [
                {"op": "measure", "op_type": "obb_size", "a": sa, "unit": "m"},
                {"op": "measure", "op_type": "obb_size", "a": sb, "unit": "m"},
            ],
            f"Compare longest 3D extents of {sa} and {sb}.",
        )

    elif fam == "ego_polar_out_of_view_cam_k":
        a = spec["operands"][0]
        k = spec["ref_frame_k"]
        r1 = add_call(
            [{"op": "locate", "q": a}],
            f"Intent: ego_polar(cam@{k}, {a}, unit={u}). Ground {a} across visible frames first.",
        )
        sa = r1[0]["slots"][0]["id"]
        add_call(
            [{"op": "ego_polar", "ref": f"cam@{k}", "targets": [sa], "unit": u}],
            f"Project persistent 3D slot {sa} into gravity-leveled camera@{k} frame.",
        )

    elif fam.startswith("chiral_direction_"):
        a, b, c = spec["operands"]
        facing_mode = spec["facing"]
        r1 = add_call(
            [{"op": "locate", "q": a}, {"op": "locate", "q": b}, {"op": "locate", "q": c}],
            f"Intent: ego_polar(ref={a}, look_at={b}, target={c}, facing={facing_mode}).",
        )
        sa, sb, sc = r1[0]["slots"][0]["id"], r1[1]["slots"][0]["id"], r1[2]["slots"][0]["id"]
        add_call(
            [{"op": "ego_polar", "ref": sa, "look_at": sb, "targets": [sc], "facing": facing_mode}],
            f"Compute gravity-leveled bearing of {sc} from {sa} facing {facing_mode} {sb}.",
        )

    elif fam.startswith("camera_motion_"):
        t0, t1 = spec["t0"], spec["t1"]
        add_call(
            [{"op": "motion", "target": "camera", "t0": t0, "t1": t1, "unit": u}],
            f"Intent: camera_motion(t0={t0}, t1={t1}, unit={u}). Query SE(3) translation.",
        )

    elif fam == "large_set_count_ge5":
        a = spec["operands"][0]
        needed_k = max(32, len(scene.by_label.get(a, [])))
        add_call(
            [{"op": "locate", "q": a, "max_k": needed_k}],
            f"Intent: count_3d({a}). Enumerate all deduplicated 3D instance slots across the scan.",
        )

    elif fam == "multi_instance_disambig":
        a, b = spec["operands"]
        r1 = add_call(
            [{"op": "locate", "q": a, "max_k": 8}, {"op": "locate", "q": b}],
            f"Intent: disambiguate '{a}' by first-seen frame {spec.get('target_first_frame')} and measure gap to {b} ({u}).",
        )
        # Bind target slot directly from locate's returned first_t table (no redundant BEV echo!)
        sa = spec["target_slot_id"]
        sb = r1[1]["slots"][0]["id"]
        add_call(
            [{"op": "measure", "op_type": "surface_gap", "a": sa, "b": sb, "unit": u}],
            f"MULTI_SLOT returned for '{a}'; slot {sa} matches first_t={spec.get('target_first_frame')}. Measure 5 cm surface gap to {sb} in {u}.",
        )
    else:
        raise ValueError(f"Unhandled task_family: {fam}")

    steps.append({
        "answer": str(spec["gt_solver"]["canonical_answer"]),
        "default_think": f"Tool returned exact value {spec['gt_solver']['canonical_answer']} ({u}); emit final answer.",
    })
    return steps


async def run_pilot0(
    target_rows: int = 36,
    workers: int = 16,
    pinned_path: Path = DEFAULT_PINNED_TRAIN,
    labels_path: Path = DEFAULT_TRAIN_LABELS,
    out_path: Path = DEFAULT_SMOKE_OUT,
    summary_path: Path = DEFAULT_SUMMARY_OUT,
    boxes_path: Path = DEFAULT_BOXES_OUT,
    author_models: Tuple[str, ...] = ("gemini-4-neon", "gemini-4-carbon"),
    argon_level: str = "MEDIUM",
    request_timeout_s: float = 120.0,
    seed: int = 20261128,
) -> Dict[str, Any]:
    t_start = time.monotonic()

    # 1. Fail-closed room exclusion pre-flight + 11/11 canary check
    guard = RoomExclusionGuard()
    canary_report = guard.assert_canaries()

    pinned_doc = json.loads(pinned_path.read_bytes())
    known_convs: Dict[str, str] = {}
    if labels_path.is_file():
        for r in json.loads(labels_path.read_bytes()).get("rows", []):
            known_convs[r["capture"]] = r["convention"]

    clean_captures, blocked_captures = guard.filter_captures(pinned_doc["captures"])

    # Mine ~2.5x candidate pool to absorb strictly blind Argon+Carbon filter rejections cleanly
    pool_size = max(int(math.ceil(target_rows * 2.5)) + 32, 96)
    candidate_specs, scenes_cache = mine_candidate_specs(
        clean_captures, guard, known_convs, max_candidates=pool_size, seed=seed
    )

    # Cache blind Argon+Carbon object verifications per (canonical_scene, instance_id, best_frame)
    vis_cache: Dict[Tuple[str, int, int], asyncio.Future] = {}
    sheet_cache: Dict[Tuple[str, Tuple[int, ...]], Tuple[str, int]] = {}
    frame_b64_cache: Dict[str, Tuple[str, int, Tuple[int, int]]] = {}

    verified_rows: List[Dict[str, Any]] = []
    exported_boxes: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
    reject_reasons: Counter = Counter()
    vis_checks_total = 0
    vis_checks_agreed = 0

    row_lock = asyncio.Lock()
    box_lock = asyncio.Lock()
    target_reached = asyncio.Event()

    # Open streaming JSONL files upfront so every verified row & box flushes incrementally to local /scratch
    out_path.parent.mkdir(parents=True, exist_ok=True)
    boxes_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    trace_fh = out_path.open("w", encoding="utf-8")
    box_fh = boxes_path.open("w", encoding="utf-8")

    def _build_summary(api_stats: Dict[str, Any], wall_s: float) -> Dict[str, Any]:
        rows_per_min = len(verified_rows) / (wall_s / 60.0) if wall_s > 0 else 0.0
        scale_factor_32 = 32.0 / max(1, workers)
        projected_24h_cur = int(round(rows_per_min * 60.0 * 24.0))
        projected_24h_w32 = int(round(rows_per_min * scale_factor_32 * 60.0 * 24.0))
        min_pass_rows = target_rows if target_rows <= 20 else math.ceil(0.95 * target_rows)
        shortfall = max(0, target_rows - len(verified_rows))
        status = "PASS" if len(verified_rows) >= min_pass_rows else "INCOMPLETE"
        return {
            "status": status,
            "verified_rows": len(verified_rows),
            "target_rows": target_rows,
            "min_pass_rows": min_pass_rows,
            "shortfall": shortfall,
            "candidates_mined": len(candidate_specs),
            "unique_clean_scenes_used": len({r["canonical_scene"] for r in verified_rows}),
            "unique_clean_rooms_used": len({r["canonical_room"] for r in verified_rows}),
            "exported_ownhead_boxes": len(exported_boxes),
            "exclusion_proof": {
                "manifest_sha256": guard.manifest_sha256,
                "canaries_passed": f"{canary_report['passed']}/{canary_report['total']}",
                "pinned_input_captures": len(pinned_doc["captures"]),
                "clean_train_captures": len(clean_captures),
                "blocked_withheld_captures": len(blocked_captures),
                "emitted_rows_hitting_any_exclusion": 0,
            },
            "quality_gates": {
                "math_recompute_pass_rate_emitted": 1.0,
                "visual_checks_total": vis_checks_total,
                "visual_checks_agreed": vis_checks_agreed,
                "argon_carbon_agreement_rate": round(vis_checks_agreed / max(1, vis_checks_total), 4),
                "emitted_argon_carbon_mean_iou": round(
                    float(np.mean([r["audit"]["argon_carbon_mean_iou"] for r in verified_rows])), 4
                ) if verified_rows else 0.0,
                "reject_breakdown": dict(reject_reasons),
            },
            "distribution": {
                "by_dataset": dict(Counter(r["dataset"] for r in verified_rows)),
                "by_task_family": dict(Counter(r["task_family"] for r in verified_rows)),
                "by_epistemic_mode": dict(Counter(r["epistemic_mode"] for r in verified_rows)),
                "by_unit": dict(Counter(r["unit"] for r in verified_rows)),
                "by_author_model": dict(Counter(r["audit"]["author_model"] for r in verified_rows)),
            },
            "throughput_and_api": {
                **api_stats,
                "workers": workers,
                "request_timeout_s": request_timeout_s,
                "rows_per_min": round(rows_per_min, 2),
                "projected_rows_24h_at_current_workers": projected_24h_cur,
                "projected_rows_24h_at_32_workers": projected_24h_w32,
            },
            "artifacts": {
                "traces_jsonl": str(out_path),
                "ownhead_boxes_jsonl": str(boxes_path),
                "summary_json": str(summary_path),
            },
        }

    api_stats: Dict[str, Any] = {}
    wall_s = 0.0
    try:
        async with GeminiInlineClient(
            concurrency=workers,
            request_timeout_s=request_timeout_s,
        ) as client:

            async def get_verified_target(scene: Scene3DGraph, obj: ObjectInstance3D) -> Dict[str, Any]:
                nonlocal vis_checks_total, vis_checks_agreed
                cache_key = (scene.canonical_scene, obj.instance_id, obj.best_frame)
                if cache_key in vis_cache:
                    return await vis_cache[cache_key]
                loop = asyncio.get_running_loop()
                fut = loop.create_future()
                vis_cache[cache_key] = fut
                try:
                    png_path = scene.anchor_dense_paths[obj.best_frame - 1]
                    if png_path not in frame_b64_cache:
                        frame_b64_cache[png_path] = encode_frame_jpeg_b64(png_path)
                    f_b64, _, _ = frame_b64_cache[png_path]
                    gt_b1000 = obj.frame_boxes_1000[obj.best_frame]
                    # Strictly blind for singletons; coarse region hint ONLY for multi-instance categories
                    is_multi_cat = len(scene.by_label.get(obj.label, [])) > 1
                    hint = _spatial_hint_from_box(gt_b1000) if is_multi_cat else ""
                    res = await client.verify_referent_argon_carbon(
                        frame_jpeg_b64=f_b64,
                        object_label=obj.label,
                        spatial_hint=hint,
                        gt_box_1000=gt_b1000,
                        argon_level=argon_level,
                    )
                    vis_checks_total += 1
                    if res["agreed"]:
                        vis_checks_agreed += 1
                        b_rec = {
                            "canonical_scene": scene.canonical_scene,
                            "canonical_room": scene.canonical_room.replace("/", "::"),
                            "exclusion_sha256": guard.manifest_sha256,
                            "frame_1idx": obj.best_frame,
                            "label": obj.label,
                            "instance_id": obj.instance_id,
                            "consensus_source": res.get("consensus_source", "argon_carbon_avg"),
                            "consensus_box_1000": res["consensus_box_1000"],
                            "argon_box_1000": res["argon_box_1000"],
                            "carbon_box_1000": res["carbon_box_1000"],
                            "argon_carbon_iou": res["argon_carbon_iou"],
                            "gt_iou": res["gt_iou"],
                        }
                        async with box_lock:
                            if cache_key not in exported_boxes:
                                exported_boxes[cache_key] = b_rec
                                box_fh.write(json.dumps(b_rec, ensure_ascii=False) + "\n")
                                box_fh.flush()
                    if not fut.done():
                        fut.set_result(res)
                    return res
                except Exception as exc:
                    # Never cache failed futures — pop so transient timeouts/errors can retry cleanly!
                    vis_cache.pop(cache_key, None)
                    if not fut.done():
                        fut.set_exception(exc)
                        # Mark exception retrieved so Python never warns if no second waiter exists
                        fut.exception()
                    raise

            async def process_one_candidate(idx: int, spec: Dict[str, Any]) -> None:
                if len(verified_rows) >= target_rows:
                    return
                scene = scenes_cache[spec["canonical_scene"]]
                # Re-verify room cleanliness before any API spend
                guard.assert_clean(scene.canonical_scene)

                # Gate G3: Independent blind Argon + Carbon visual & referent check
                consensus_boxes: Dict[str, List[int]] = {}
                audit_ious: List[float] = []
                consensus_sources: List[str] = []
                try:
                    vis_results = await asyncio.gather(
                        *(get_verified_target(scene, obj) for obj, _ in spec["verify_targets"])
                    )
                except Exception as exc:
                    reject_reasons[f"vis_api_err:{type(exc).__name__}"] += 1
                    return

                for (obj, need_hint), vres in zip(spec["verify_targets"], vis_results):
                    if not vres["agreed"]:
                        reject_reasons["argon_carbon_disagreed_or_occluded"] += 1
                        return
                    audit_ious.append(float(vres["argon_carbon_iou"]))
                    consensus_sources.append(str(vres.get("consensus_source", "argon_carbon_avg")))
                    if need_hint:
                        # Verify consensus box hits target GT mask so UNSEEN recovery lifts true object
                        if (vres.get("gt_iou") or 0.0) >= 0.30:
                            consensus_boxes[obj.label] = vres["consensus_box_1000"]
                        else:
                            reject_reasons["box_hint_gt_iou_below_0.30"] += 1
                            return

                if len(verified_rows) >= target_rows:
                    return

                # Build contact sheet & deterministic GeoAPI-v2 scaffold
                c_frames = _select_contact_frames(scene, spec["must_frames"], total=6)
                s_key = (scene.canonical_scene, tuple(f for f, _ in c_frames))
                if s_key not in sheet_cache:
                    sheet_cache[s_key] = build_contact_sheet_jpeg_b64(c_frames)
                sheet_b64, _ = sheet_cache[s_key]

                try:
                    scaffold = build_scaffold_calls(scene, spec, consensus_boxes)
                except Exception as exc:
                    reject_reasons[f"scaffold_err:{exc}"] += 1
                    return

                preferred = (
                    author_models[idx % len(author_models)]
                    if len(author_models) > 1
                    else author_models[0]
                )
                try:
                    authored_turns, author_meta = await client.author_grounded_trace(
                        contact_sheet_b64=sheet_b64,
                        task_spec=spec,
                        scaffold_steps=scaffold,
                        preferred_model=preferred,
                    )
                except Exception as exc:
                    reject_reasons[f"author_api_err:{type(exc).__name__}"] += 1
                    return

                if not author_meta.get("visual_sanity_ok", True):
                    reject_reasons["author_visual_sanity_veto"] += 1
                    return

                # Gate G2 + G4: Deterministic Python 3D Recompute & Hygiene Gate
                recomp = recompute_and_verify_trace(scene, spec, authored_turns)
                if not recomp["valid"]:
                    reject_reasons[f"recompute_gate:{recomp['reason']}"] += 1
                    return

                # Final fail-closed room assertion right before row emission
                final_guard = guard.assert_clean({
                    "canonical": scene.canonical_scene,
                    "room": scene.canonical_room,
                })

                async with row_lock:
                    if len(verified_rows) >= target_rows:
                        return
                    row_num = len(verified_rows) + 1
                    slug = scene.canonical_scene.replace("/", "_")
                    row_record = {
                        "row_id": f"e05_v2_{row_num:05d}_{slug}",
                        "stream": spec["stream"],
                        "task_family": spec["task_family"],
                        "epistemic_mode": spec["epistemic_mode"],
                        "dataset": final_guard["dataset"],
                        "canonical_scene": final_guard["canonical_scene"],
                        "canonical_room": final_guard["format_room"],
                        "exclusion_sha256": final_guard["exclusion_sha256"],
                        "extent_calibration": scene.extent_convention,
                        "metric_scale_locked": 1,
                        "unit": spec["unit"],
                        "template_idx": spec["template_idx"],
                        "contact_frames_1idx": [f for f, _ in c_frames],
                        "prompt": spec["prompt"],
                        "trace_turns": recomp["trace_turns"],
                        "wire_xml": recomp["wire_xml"],
                        "gt_solver": spec["gt_solver"],
                        "audit": {
                            "author_model": author_meta["model_used"],
                            "argon_carbon_mean_iou": round(float(np.mean(audit_ious)), 4),
                            "consensus_sources": consensus_sources,
                            "referent_unique": spec["task_family"] != "large_set_count_ge5",
                            "all_slots_returned": True,
                            "recompute_math_exact": True,
                            "think_words": recomp["think_words"],
                            "geo_calls": recomp["geo_calls"],
                        },
                    }
                    verified_rows.append(row_record)
                    trace_fh.write(json.dumps(row_record, ensure_ascii=False) + "\n")
                    trace_fh.flush()

                    print(
                        f"[VERIFIED {row_num:04d}/{target_rows}] {row_record['canonical_room']} | "
                        f"{row_record['task_family']} ({row_record['epistemic_mode']}) | "
                        f"ans={row_record['gt_solver']['canonical_answer']} ({row_record['unit']}) | "
                        f"AC_IoU={row_record['audit']['argon_carbon_mean_iou']:.3f} | "
                        f"author={author_meta['model_used']}",
                        flush=True,
                    )
                    if row_num % 25 == 0:
                        interim = _build_summary(
                            client.telemetry.summary(time.monotonic() - t_start),
                            time.monotonic() - t_start,
                        )
                        summary_path.write_text(json.dumps(interim, indent=2) + "\n", encoding="utf-8")
                    if len(verified_rows) >= target_rows:
                        target_reached.set()

            # Continuous non-blocking worker pool with immediate cancellation on target_reached
            cand_queue: asyncio.Queue[Tuple[int, Dict[str, Any]]] = asyncio.Queue()
            for idx, sp in enumerate(candidate_specs):
                cand_queue.put_nowait((idx, sp))

            async def _worker_loop() -> None:
                while not target_reached.is_set():
                    try:
                        idx, sp = cand_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return
                    try:
                        await process_one_candidate(idx, sp)
                    finally:
                        cand_queue.task_done()

            num_pool_workers = min(len(candidate_specs), max(workers, 20))
            worker_tasks = [asyncio.create_task(_worker_loop()) for _ in range(num_pool_workers)]
            done_waiter = asyncio.create_task(target_reached.wait())
            all_workers_fut = asyncio.gather(*worker_tasks, return_exceptions=True)

            await asyncio.wait(
                [done_waiter, asyncio.ensure_future(all_workers_fut)],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for wt in worker_tasks:
                if not wt.done():
                    wt.cancel()
            if not done_waiter.done():
                done_waiter.cancel()
            await asyncio.gather(*worker_tasks, return_exceptions=True)

            wall_s = time.monotonic() - t_start
            api_stats = client.telemetry.summary(wall_s)
    finally:
        trace_fh.flush()
        trace_fh.close()
        box_fh.flush()
        box_fh.close()

    summary = _build_summary(api_stats, wall_s)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-rows", type=int, default=36)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--pinned", type=Path, default=DEFAULT_PINNED_TRAIN)
    parser.add_argument("--labels", type=Path, default=DEFAULT_TRAIN_LABELS)
    parser.add_argument("--out", type=Path, default=DEFAULT_SMOKE_OUT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_OUT)
    parser.add_argument("--boxes-out", type=Path, default=DEFAULT_BOXES_OUT)
    parser.add_argument("--author-models", type=str, default="gemini-4-neon,gemini-4-carbon")
    parser.add_argument("--argon-level", type=str, default="MEDIUM", choices=("LOW", "MEDIUM", "HIGH"))
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--seed", type=int, default=20261128)
    args = parser.parse_args(argv)

    models = tuple(m.strip() for m in args.author_models.split(",") if m.strip())
    summary = asyncio.run(
        run_pilot0(
            target_rows=args.target_rows,
            workers=args.workers,
            pinned_path=args.pinned,
            labels_path=args.labels,
            out_path=args.out,
            summary_path=args.summary_out,
            boxes_path=args.boxes_out,
            author_models=models,
            argon_level=args.argon_level,
            request_timeout_s=args.timeout,
            seed=args.seed,
        )
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
