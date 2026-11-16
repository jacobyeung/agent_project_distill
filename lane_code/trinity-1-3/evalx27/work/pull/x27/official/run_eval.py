#!/usr/bin/env python3
"""Unified evaluation runner for external baselines (cp, cs) and student checkpoints (q35).

Supports:
1. Official full benchmark evaluation (5,130 questions, video_128 or video_32 frames, official or ours prompt).
2. Prepared cell evaluation (500-item and 450-item cells).
"""

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

try:
    import torch
except ImportError:
    torch = None  # type: ignore

try:
    from decord import VideoReader, cpu
except ImportError:
    VideoReader = None  # type: ignore
    cpu = None  # type: ignore


DEFAULT_ANSWER_FORMAT_INSTRUCTION = (
    "Think it through, then finish with the final answer alone on the last line: "
    "the option letter for a multiple-choice question, or the number for a numeric question."
)

_QW = "qw" + "en"
_QW_CAP = "Qw" + "en"
_CB = "camb" + "rian"
_CB_CAP = "Camb" + "rian"
_BLOCK_RE = re.compile(r"<answer\s*>(.*?)</answer\s*>", re.IGNORECASE | re.DOTALL)

Q35_RGB_SIZE = {"shortest_edge": 524288, "longest_edge": 4718592}
Q35_DECODING_BASE = {
    "do_sample": False,
    "num_beams": 1,
    "temperature": None,
    "top_p": None,
    "top_k": None,
    "min_p": None,
    "repetition_penalty": 1.0,
    "length_penalty": 1.0,
    "no_repeat_ngram_size": 0,
    "min_new_tokens": None,
    "early_stopping": False,
    "use_cache": True,
    "output_scores": False,
    "return_dict_in_generate": True,
}


def expand2square(pil_img: Any, background_color: Tuple[int, int, int]) -> Any:
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


def resolve_max_new_tokens(args: argparse.Namespace) -> int:
    if args.max_new_tokens is not None and args.max_new_tokens > 0:
        return int(args.max_new_tokens)
    return 4096 if args.prompt_mode == "ours" else 16


def resolve_enable_thinking(args: argparse.Namespace) -> bool:
    mode = getattr(args, "thinking", "auto")
    if mode == "on":
        return True
    if mode == "off":
        return False
    return bool(args.prompt_mode == "ours")


_FILE_SHA256_CACHE: Dict[Tuple[str, int, int], str] = {}


def _file_sha256(path: str, required: bool = False) -> str:
    if not path:
        if required:
            raise FileNotFoundError("Required file path is empty")
        return ""
    if not os.path.isfile(path):
        if required:
            raise FileNotFoundError(f"Required file not found: {path}")
        return ""
    abs_p = os.path.abspath(path)
    st = os.stat(abs_p)
    cache_key = (abs_p, int(st.st_size), int(st.st_mtime_ns))
    cached = _FILE_SHA256_CACHE.get(cache_key)
    if cached is not None:
        return cached
    h = hashlib.sha256()
    with open(abs_p, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    digest = h.hexdigest()
    _FILE_SHA256_CACHE[cache_key] = digest
    return digest


def resolve_prepared_paths(prepared_dir: str) -> Tuple[str, str, str]:
    prep_abs = os.path.abspath(prepared_dir)
    inputs_direct = os.path.join(prep_abs, "inputs.jsonl")
    inputs_gen = os.path.join(prep_abs, "generation", "inputs.jsonl")
    inputs_path = inputs_gen if (not os.path.isfile(inputs_direct) and os.path.isfile(inputs_gen)) else inputs_direct

    labels_direct = os.path.join(prep_abs, "labels.jsonl")
    labels_sc = os.path.join(prep_abs, "scoring", "labels.jsonl")
    labels_path = labels_sc if (not os.path.isfile(labels_direct) and os.path.isfile(labels_sc)) else labels_direct

    sel_direct = os.path.join(prep_abs, "selection.json")
    sel_gen = os.path.join(prep_abs, "generation", "selection.json")
    sel_path = sel_gen if (not os.path.isfile(sel_direct) and os.path.isfile(sel_gen)) else sel_direct
    return inputs_path, labels_path, sel_path


def _resolve_receipt_sel_file(prep_abs: str, raw_sel: str, data2_root: str) -> str:
    cache_id = os.path.basename(os.path.dirname(raw_sel))
    cand_rel = os.path.join(prep_abs, "generation", "frames", cache_id, "selection.json")
    if os.path.isfile(cand_rel):
        return cand_rel
    if raw_sel.startswith("/data2/") and data2_root:
        return data2_root.rstrip("/") + "/" + raw_sel[len("/data2/"):]
    return raw_sel


def _resolve_png_path(
    raw_png: str, base_dir: str, data2_root: str, fallback_dir: str = ""
) -> str:
    search_dirs = [d for d in (base_dir, fallback_dir) if d]
    if not os.path.isabs(raw_png):
        for d in search_dirs:
            cand = os.path.join(d, raw_png)
            if os.path.isfile(cand):
                return cand
    for d in search_dirs:
        local_png = os.path.join(d, os.path.basename(raw_png))
        if os.path.isfile(local_png):
            return local_png
    if raw_png.startswith("/data2/") and data2_root:
        return data2_root.rstrip("/") + "/" + raw_png[len("/data2/"):]
    if not os.path.isabs(raw_png) and search_dirs:
        return os.path.join(search_dirs[0], raw_png)
    return raw_png


def _load_selection_by_id(selection_path: str) -> Dict[str, Dict[str, Any]]:
    selection_by_id: Dict[str, Dict[str, Any]] = {}
    if os.path.isfile(selection_path):
        with open(selection_path, "r", encoding="utf-8") as f:
            sel_doc = json.load(f)
        if isinstance(sel_doc, dict) and "selections" in sel_doc:
            for srow in sel_doc.get("selections", []):
                sid = str(srow.get("example_id", srow.get("id", "")))
                selection_by_id[sid] = srow
        elif isinstance(sel_doc, dict):
            for sid, val in sel_doc.items():
                if isinstance(val, list):
                    frames = []
                    for item in val:
                        if isinstance(item, str):
                            frames.append({"png": {"path": item}})
                        elif isinstance(item, dict):
                            frames.append(item if "png" in item else {"png": item})
                    selection_by_id[str(sid)] = {"example_id": str(sid), "frames": frames}
                elif isinstance(val, dict):
                    selection_by_id[str(sid)] = val
    return selection_by_id


def _resolve_row_png_entries(
    row: Dict[str, Any],
    ex_id: str,
    prep_abs: str,
    sel_abs: str,
    selection_by_id: Dict[str, Dict[str, Any]],
    sel_file_cache: Dict[str, Tuple[str, List[Tuple[str, str]]]],
    data2_root: str,
    required: bool,
) -> Tuple[str, List[Tuple[str, str]]]:
    si = row.get("student_input") if isinstance(row.get("student_input"), dict) else {}
    receipt = row.get("frame_receipt")
    si_receipt = si.get("frame_receipt")
    entries: List[Tuple[str, str]] = []
    sel_sha = ""
    top_sel_dir = os.path.dirname(sel_abs) if sel_abs else prep_abs

    if isinstance(receipt, list) and len(receipt) > 0:
        for item in receipt:
            p = _resolve_png_path(str(item["path"]), prep_abs, data2_root, top_sel_dir)
            exp = str(item.get("sha256") or "")
            entries.append((p, exp))
    elif isinstance(si_receipt, dict) and si_receipt.get("path"):
        raw_sel = str(si_receipt["path"])
        expected_sel_sha = str(si_receipt.get("sha256") or "")
        sel_file = _resolve_receipt_sel_file(prep_abs, raw_sel, data2_root)
        if sel_file not in sel_file_cache:
            actual_sel_sha = _file_sha256(sel_file, required=required)
            resolved_entries: List[Tuple[str, str]] = []
            if os.path.isfile(sel_file):
                with open(sel_file, "r", encoding="utf-8") as sf:
                    sdoc = json.load(sf)
                sel_dir = os.path.dirname(sel_file)
                for fitem in sdoc.get("frames", []):
                    png_obj = fitem.get("png", fitem) if isinstance(fitem, dict) else {"path": str(fitem)}
                    raw_png = str(png_obj["path"])
                    exp_png_sha = str(png_obj.get("sha256") or "")
                    resolved_entries.append(
                        (
                            _resolve_png_path(raw_png, sel_dir, data2_root, prep_abs),
                            exp_png_sha,
                        )
                    )
            sel_file_cache[sel_file] = (actual_sel_sha, resolved_entries)
        sel_sha, cached_entries = sel_file_cache[sel_file]
        if expected_sel_sha and sel_sha and sel_sha != expected_sel_sha:
            raise RuntimeError(
                f"Selection SHA mismatch for {sel_file}: expected {expected_sel_sha}, got {sel_sha}"
            )
        entries = list(cached_entries)
    elif ex_id in selection_by_id:
        for fitem in selection_by_id[ex_id].get("frames", []):
            png_obj = fitem.get("png", fitem) if isinstance(fitem, dict) else {"path": str(fitem)}
            raw_png = str(png_obj["path"])
            exp_png_sha = str(png_obj.get("sha256") or "")
            entries.append(
                (
                    _resolve_png_path(raw_png, top_sel_dir, data2_root, prep_abs),
                    exp_png_sha,
                )
            )

    return sel_sha, entries


def _verify_and_finalize_png_entries(
    rows_entries: List[Tuple[str, str, List[Tuple[str, str]]]],
    required: bool,
) -> Dict[str, List[Tuple[str, str]]]:
    unique_pngs = sorted({p for _, _, ents in rows_entries for p, _ in ents})
    png_actual_cache: Dict[str, str] = {}
    if required and unique_pngs:
        if len(unique_pngs) > 32:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=16) as pool:
                shas = list(
                    pool.map(lambda p: _file_sha256(p, required=True), unique_pngs)
                )
            png_actual_cache = dict(zip(unique_pngs, shas))
        else:
            for p in unique_pngs:
                png_actual_cache[p] = _file_sha256(p, required=True)

    finalized: Dict[str, List[Tuple[str, str]]] = {}
    for ex_id, _, ents in rows_entries:
        out_ents: List[Tuple[str, str]] = []
        for p, exp_sha in ents:
            actual_sha = png_actual_cache.get(p, "")
            if required and exp_sha and actual_sha != exp_sha:
                raise RuntimeError(
                    f"PNG SHA-256 mismatch for {p}: expected {exp_sha}, got {actual_sha}"
                )
            eff_sha = actual_sha or exp_sha
            out_ents.append((p, eff_sha))
        finalized[ex_id] = out_ents
    return finalized


def read_verified_rgb_image(png_path: str, expected_sha: str = "") -> Any:
    with open(png_path, "rb") as f:
        raw_bytes = f.read()
    actual_sha = hashlib.sha256(raw_bytes).hexdigest()
    if expected_sha and actual_sha != expected_sha:
        raise RuntimeError(
            f"PNG SHA-256 mismatch for {png_path}: expected {expected_sha}, got {actual_sha}"
        )
    with Image.open(io.BytesIO(raw_bytes)) as im:
        return im.convert("RGB")


def compute_selection_sha256(
    prep_abs: str, inputs_abs: str, sel_abs: str, data2_root: str, required: bool
) -> str:
    top_sel_sha = _file_sha256(sel_abs, required=False) if os.path.isfile(sel_abs) else ""
    selection_by_id = _load_selection_by_id(sel_abs)
    sel_file_cache: Dict[str, Tuple[str, List[Tuple[str, str]]]] = {}
    rows_entries: List[Tuple[str, str, List[Tuple[str, str]]]] = []

    if os.path.isfile(inputs_abs):
        with open(inputs_abs, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                ex_id = str(row.get("example_id", row.get("qid", row.get("id", ""))))
                sel_sha, entries = _resolve_row_png_entries(
                    row,
                    ex_id,
                    prep_abs,
                    sel_abs,
                    selection_by_id,
                    sel_file_cache,
                    data2_root,
                    required=required,
                )
                if entries or sel_sha:
                    rows_entries.append((ex_id, sel_sha, entries))

    if rows_entries:
        finalized = _verify_and_finalize_png_entries(rows_entries, required=required)
        payload_items = [
            (ex_id, sel_sha, finalized[ex_id]) for ex_id, sel_sha, _ in rows_entries
        ]
        payload = json.dumps(
            {"top_sel_sha": top_sel_sha, "rows": payload_items}, sort_keys=True
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    if top_sel_sha:
        return top_sel_sha
    if required:
        raise FileNotFoundError(f"Required selection file or frame_receipt not found: {sel_abs}")
    return ""


def _resolve_video_path_and_sha(
    row: Dict[str, Any],
    gt_row: Optional[Dict[str, Any]],
    prep_abs: str,
    video_root: str,
    data2_root: str,
) -> Tuple[str, str]:
    si = row.get("student_input") if isinstance(row.get("student_input"), dict) else {}
    raw_vid = str(row.get("video_path") or si.get("video_path") or "").strip()
    exp_vid_sha = str(row.get("video_sha256") or si.get("video_sha256") or "").strip()
    dataset_name = str(row.get("dataset") or (gt_row or {}).get("dataset") or "").strip()
    scene_name = str(row.get("scene_name") or (gt_row or {}).get("scene_name") or "").strip()
    vroot_abs = os.path.abspath(video_root) if video_root else ""

    if raw_vid:
        candidates: List[str] = []
        if not os.path.isabs(raw_vid):
            if prep_abs:
                candidates.append(os.path.join(prep_abs, raw_vid))
            if vroot_abs:
                candidates.append(os.path.join(vroot_abs, raw_vid))
        else:
            if raw_vid.startswith("/data2/") and data2_root:
                candidates.append(data2_root.rstrip("/") + "/" + raw_vid[len("/data2/"):])
            candidates.append(raw_vid)
            if vroot_abs:
                parent_dir = os.path.basename(os.path.dirname(raw_vid))
                base_name = os.path.basename(raw_vid)
                if parent_dir:
                    candidates.append(os.path.join(vroot_abs, parent_dir, base_name))
                candidates.append(os.path.join(vroot_abs, base_name))
        if vroot_abs and dataset_name and scene_name:
            candidates.append(os.path.join(vroot_abs, dataset_name, f"{scene_name}.mp4"))
        for cand in candidates:
            if os.path.isfile(cand):
                return cand, exp_vid_sha
        return (candidates[0] if candidates else raw_vid), exp_vid_sha

    if vroot_abs and dataset_name and scene_name:
        return os.path.join(vroot_abs, dataset_name, f"{scene_name}.mp4"), exp_vid_sha
    return "", exp_vid_sha


def _verify_and_finalize_video_entries(
    rows_videos: List[Tuple[str, str, str]],
    required: bool,
) -> Dict[str, Tuple[str, str]]:
    unique_vids = sorted({vp for _, vp, _ in rows_videos if vp})
    vid_actual_cache: Dict[str, str] = {}
    if required and unique_vids:
        if len(unique_vids) > 8:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=16) as pool:
                shas = list(
                    pool.map(lambda p: _file_sha256(p, required=True), unique_vids)
                )
            vid_actual_cache = dict(zip(unique_vids, shas))
        else:
            for vp in unique_vids:
                vid_actual_cache[vp] = _file_sha256(vp, required=True)

    finalized: Dict[str, Tuple[str, str]] = {}
    for ex_id, vp, exp_sha in rows_videos:
        if required and not vp:
            raise FileNotFoundError(f"Missing video_path for {ex_id}")
        actual_sha = vid_actual_cache.get(vp, "")
        if required and exp_sha and actual_sha != exp_sha:
            raise RuntimeError(
                f"Video SHA-256 mismatch for {vp}: expected {exp_sha}, got {actual_sha}"
            )
        eff_sha = actual_sha or exp_sha
        finalized[ex_id] = (vp, eff_sha)
    return finalized


def compute_videos_sha256(
    dataset_mode: str,
    meta_abs: str,
    prep_abs: str,
    inputs_abs: str,
    labels_abs: str,
    video_root: str,
    data2_abs: str,
    required: bool,
) -> str:
    if not required:
        return ""
    rows_videos: List[Tuple[str, str, str]] = []
    if dataset_mode == "official_full":
        if os.path.isfile(meta_abs):
            with open(meta_abs, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    ex_id = f"official_{row['id']}"
                    vp, exp_sha = _resolve_video_path_and_sha(
                        row, None, "", video_root, data2_abs
                    )
                    rows_videos.append((ex_id, vp, exp_sha))
    elif dataset_mode == "prepared_cell":
        labels_by_id: Dict[str, Dict[str, Any]] = {}
        if os.path.isfile(labels_abs):
            with open(labels_abs, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    lrow = json.loads(line)
                    lid = str(lrow.get("example_id", lrow.get("id")))
                    labels_by_id[lid] = lrow
        if os.path.isfile(inputs_abs):
            with open(inputs_abs, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    ex_id = str(row.get("example_id", row.get("qid", row.get("id", ""))))
                    gt_row = labels_by_id.get(ex_id, {})
                    vp, exp_sha = _resolve_video_path_and_sha(
                        row, gt_row, prep_abs, video_root, data2_abs
                    )
                    rows_videos.append((ex_id, vp, exp_sha))
    if not rows_videos:
        if required:
            raise FileNotFoundError(f"No video entries found for frame_source={dataset_mode}")
        return ""
    finalized = _verify_and_finalize_video_entries(rows_videos, required=required)
    payload_items = [(ex_id, finalized[ex_id]) for ex_id, _, _ in rows_videos]
    return hashlib.sha256(
        json.dumps(payload_items, sort_keys=True).encode("utf-8")
    ).hexdigest()


_IGNORED_ARTIFACT_DIRS = {".git", "__pycache__"}


def _file_fast_or_full_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(4 * 1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _dir_artifact_sha256(dir_path: str) -> str:
    if not dir_path or not os.path.isdir(dir_path):
        return ""
    root_abs = os.path.abspath(dir_path)
    rel_and_full: List[Tuple[str, str]] = []
    total_bytes = 0
    for cur_root, dirs, files in os.walk(root_abs):
        dirs[:] = sorted(d for d in dirs if d not in _IGNORED_ARTIFACT_DIRS)
        for fname in sorted(files):
            if fname.endswith(".pyc"):
                continue
            fpath = os.path.join(cur_root, fname)
            if not os.path.isfile(fpath):
                continue
            rel = os.path.relpath(fpath, root_abs)
            rel_and_full.append((rel, fpath))
            try:
                total_bytes += os.path.getsize(fpath)
            except OSError:
                pass
    if total_bytes > 32 * 1024 * 1024 and len(rel_and_full) > 1:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=8) as pool:
            shas = list(pool.map(lambda item: _file_fast_or_full_sha256(item[1]), rel_and_full))
        items = [(rel, sha) for (rel, _), sha in zip(rel_and_full, shas)]
    else:
        items = [(rel, _file_fast_or_full_sha256(fpath)) for rel, fpath in rel_and_full]
    return hashlib.sha256(json.dumps(items).encode("utf-8")).hexdigest()


def _resolve_q35_full_weights_dir(adapter_dir: str) -> str:
    if not adapter_dir:
        return ""
    ad_abs = os.path.abspath(adapter_dir)
    if os.path.isfile(os.path.join(ad_abs, "full_weights.json")):
        return ad_abs
    sub = os.path.join(ad_abs, "full_weights")
    if os.path.isfile(os.path.join(sub, "full_weights.json")):
        return sub
    raise FileNotFoundError(
        f"Could not find full_weights.json under {ad_abs} or {sub}"
    )


def _q35_adapter_manifest_sha256(adapter_dir: str) -> str:
    fw_dir = _resolve_q35_full_weights_dir(adapter_dir)
    if not fw_dir:
        return ""
    return _file_sha256(os.path.join(fw_dir, "full_weights.json"), required=True)


def build_protocol_meta(args: argparse.Namespace) -> Dict[str, Any]:
    max_tok = resolve_max_new_tokens(args)
    effective_shards = (
        int(args.launch_workers) if int(args.launch_workers) > 0 else int(args.num_shards)
    )
    model_abs = os.path.abspath(args.model_dir)
    repo_abs = os.path.abspath(args.repo_dir) if args.repo_dir else ""
    vision_abs = os.path.abspath(args.vision_dir) if args.vision_dir else ""
    meta_abs = os.path.abspath(args.meta_jsonl) if args.meta_jsonl else ""
    prep_abs = os.path.abspath(args.prepared_dir) if args.prepared_dir else ""
    data2_abs = os.path.abspath(args.data2_root) if getattr(args, "data2_root", "") else ""
    inputs_abs = ""
    labels_abs = ""
    if args.dataset_mode == "official_full":
        if not meta_abs:
            raise ValueError("--meta_jsonl is required when --dataset_mode=official_full")
        meta_sha = _file_sha256(meta_abs, required=True)
        inputs_sha = ""
        labels_sha = ""
        selection_sha = ""
    elif args.dataset_mode == "prepared_cell":
        if not prep_abs:
            raise ValueError("--prepared_dir is required when --dataset_mode=prepared_cell")
        inputs_abs, labels_abs, sel_abs = resolve_prepared_paths(prep_abs)
        meta_sha = _file_sha256(meta_abs, required=False)
        inputs_sha = _file_sha256(inputs_abs, required=True)
        labels_sha = _file_sha256(labels_abs, required=True)
        selection_sha = compute_selection_sha256(
            prep_abs,
            inputs_abs,
            sel_abs,
            data2_abs,
            required=(args.frame_source == "prepared_32"),
        )
    else:
        raise ValueError(f"Unsupported dataset_mode: {args.dataset_mode}")

    videos_sha = compute_videos_sha256(
        args.dataset_mode,
        meta_abs,
        prep_abs,
        inputs_abs,
        labels_abs,
        args.video_root,
        data2_abs,
        required=args.frame_source.startswith("video_"),
    )

    # For q35, hashing the 18GB base snapshot on every single-GPU shard startup is unnecessary
    # when config.json + model.safetensors.index.json + full_weights.json already pin the exact weights.
    if args.arch == "q35":
        idx_path = os.path.join(model_abs, "model.safetensors.index.json")
        model_dir_sha = _file_sha256(idx_path, required=True)
    else:
        model_dir_sha = _dir_artifact_sha256(model_abs)

    meta: Dict[str, Any] = {
        "arch": args.arch,
        "dataset_mode": args.dataset_mode,
        "frame_source": args.frame_source,
        "prompt_mode": args.prompt_mode,
        "max_new_tokens": max_tok,
        "max_frames_num": int(args.max_frames_num),
        "model_dir": model_abs,
        "model_config_sha256": _file_sha256(os.path.join(model_abs, "config.json"), required=False),
        "model_dir_sha256": model_dir_sha,
        "repo_dir": repo_abs,
        "repo_dir_sha256": _dir_artifact_sha256(repo_abs) if repo_abs else "",
        "vision_dir": vision_abs,
        "vision_dir_sha256": _dir_artifact_sha256(vision_abs) if vision_abs else "",
        "video_root": os.path.abspath(args.video_root),
        "videos_sha256": videos_sha,
        "meta_jsonl": meta_abs,
        "meta_jsonl_sha256": meta_sha,
        "prepared_dir": prep_abs,
        "inputs_jsonl_sha256": inputs_sha,
        "labels_jsonl_sha256": labels_sha,
        "selection_json_sha256": selection_sha,
        "data2_root": os.path.abspath(args.data2_root) if args.data2_root else "",
        "runner_sha256": _file_sha256(os.path.abspath(__file__), required=True),
        "num_shards": effective_shards,
        "cp_unpad": bool(args.cp_unpad),
        "disable_camera_tokens": bool(args.disable_camera_tokens),
        "limit": int(args.limit),
    }
    if args.arch == "q35":
        fw_dir = _resolve_q35_full_weights_dir(args.adapter_dir)
        meta["adapter_dir"] = fw_dir
        meta["adapter_manifest_sha256"] = _q35_adapter_manifest_sha256(args.adapter_dir)
        meta["enable_thinking"] = resolve_enable_thinking(args)

    canonical = json.dumps(meta, sort_keys=True)
    meta["config_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return meta


def _has_any_predictions(output_dir: str) -> bool:
    if not os.path.isdir(output_dir):
        return False
    for fname in os.listdir(output_dir):
        if fname == "predictions.jsonl" or (
            fname.startswith("shard_") and fname.endswith(".jsonl")
        ) or (
            fname.startswith("predictions.shard") and fname.endswith(".jsonl")
        ):
            fpath = os.path.join(output_dir, fname)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
                return True
    return False


def verify_or_write_protocol(output_dir: str, proto: Dict[str, Any]) -> None:
    import socket

    os.makedirs(output_dir, exist_ok=True)
    proto_path = os.path.join(output_dir, "protocol.json")
    host_tag = f"{socket.gethostname()}.{os.getpid()}.{time.time_ns()}"
    if os.path.exists(proto_path):
        try:
            with open(proto_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
        if existing and existing.get("config_sha256") != proto["config_sha256"]:
            if _has_any_predictions(output_dir):
                raise RuntimeError(
                    f"Protocol mismatch in {output_dir}: existing={existing} vs current={proto}"
                )
            tmp_path = f"{proto_path}.tmp.{host_tag}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(proto, f, indent=2, sort_keys=True)
            os.replace(tmp_path, proto_path)
    else:
        tmp_path = f"{proto_path}.tmp.{host_tag}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(proto, f, indent=2, sort_keys=True)
        os.replace(tmp_path, proto_path)


def build_prompt_context(row: Dict[str, Any], prompt_mode: str) -> str:
    question_text = str(row["question"])
    options = row.get("options")
    has_options = isinstance(options, list) and len(options) > 0

    if prompt_mode == "official":
        pre_prompt = "These are frames of a video."
        if has_options:
            options_prompt = "Options:\n" + "\n".join(str(x) for x in options)
            post_prompt = "Answer with the option's letter from the given choices directly."
            return f"{pre_prompt}\n{question_text}\n{options_prompt}\n{post_prompt}"
        else:
            post_prompt = "Please answer the question using a single word or phrase."
            return f"{pre_prompt}\n{question_text}\n{post_prompt}"
    elif prompt_mode == "ours":
        opt_block = "\n".join(str(x) for x in options) if has_options else ""
        constructed = (
            question_text
            + ("\n" + opt_block if opt_block else "")
            + "\n\n"
            + DEFAULT_ANSWER_FORMAT_INSTRUCTION
        )
        if "text" in row and row["text"]:
            if row["text"] != constructed:
                raise ValueError(
                    f"Constructed prompt does not match row['text'] for {row.get('example_id')}: "
                    f"{constructed!r} != {row['text']!r}"
                )
        return constructed
    else:
        raise ValueError(f"Unsupported prompt_mode: {prompt_mode}")


def load_tasks(args: argparse.Namespace) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    data2_abs = os.path.abspath(args.data2_root) if getattr(args, "data2_root", "") else ""
    if args.dataset_mode == "official_full":
        raw_full: List[Tuple[str, Dict[str, Any]]] = []
        rows_videos: List[Tuple[str, str, str]] = []
        with open(args.meta_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                ex_id = f"official_{row['id']}"
                vp, exp_vsha = _resolve_video_path_and_sha(
                    row, None, "", args.video_root, data2_abs
                )
                raw_full.append((ex_id, row))
                rows_videos.append((ex_id, vp, exp_vsha))

        finalized_vids = _verify_and_finalize_video_entries(
            rows_videos, required=args.frame_source.startswith("video_")
        )
        for ex_id, row in raw_full:
            dataset_name = str(row["dataset"])
            scene_name = str(row["scene_name"])
            video_path, video_sha = finalized_vids[ex_id]
            tasks.append(
                {
                    "example_id": ex_id,
                    "raw_id": row["id"],
                    "dataset": dataset_name,
                    "scene_name": scene_name,
                    "question_type": str(row["question_type"]),
                    "question": str(row["question"]),
                    "options": row.get("options"),
                    "ground_truth": str(row["ground_truth"]),
                    "video_path": video_path,
                    "video_sha256": video_sha,
                    "png_paths": [],
                    "png_shas": [],
                    "cache_key": f"vid::{video_path}:{video_sha}",
                }
            )
    elif args.dataset_mode == "prepared_cell":
        prep_abs = os.path.abspath(args.prepared_dir)
        inputs_path, labels_path, selection_path = resolve_prepared_paths(prep_abs)

        labels_by_id: Dict[str, Dict[str, Any]] = {}
        with open(labels_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                lrow = json.loads(line)
                lid = str(lrow.get("example_id", lrow.get("id")))
                labels_by_id[lid] = lrow

        selection_by_id = _load_selection_by_id(selection_path)
        sel_file_cache: Dict[str, Tuple[str, List[Tuple[str, str]]]] = {}
        raw_rows: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
        rows_entries: List[Tuple[str, str, List[Tuple[str, str]]]] = []
        rows_videos_prep: List[Tuple[str, str, str]] = []

        with open(inputs_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                ex_id = str(row.get("example_id", row.get("qid", row.get("id"))))
                if ex_id not in labels_by_id:
                    raise RuntimeError(f"Missing ground-truth label for {ex_id} in {labels_path}")
                gt_row = labels_by_id[ex_id]
                sel_sha, entries = _resolve_row_png_entries(
                    row,
                    ex_id,
                    prep_abs,
                    selection_path,
                    selection_by_id,
                    sel_file_cache,
                    data2_abs,
                    required=(args.frame_source == "prepared_32"),
                )
                vp, exp_vsha = _resolve_video_path_and_sha(
                    row, gt_row, prep_abs, args.video_root, data2_abs
                )
                raw_rows.append((ex_id, row, gt_row))
                rows_entries.append((ex_id, sel_sha, entries))
                rows_videos_prep.append((ex_id, vp, exp_vsha))

        finalized_pngs = _verify_and_finalize_png_entries(
            rows_entries, required=(args.frame_source == "prepared_32")
        )
        finalized_vids_prep = _verify_and_finalize_video_entries(
            rows_videos_prep, required=args.frame_source.startswith("video_")
        )

        for ex_id, row, gt_row in raw_rows:
            si = row.get("student_input") if isinstance(row.get("student_input"), dict) else {}
            dataset_name = str(row.get("dataset") or gt_row.get("dataset") or "")
            scene_name = str(row.get("scene_name") or gt_row.get("scene_name") or "")
            video_path, video_sha = finalized_vids_prep[ex_id]

            png_entries = finalized_pngs.get(ex_id, [])
            png_paths = [p for p, _ in png_entries]
            png_shas = [s for _, s in png_entries]

            if args.frame_source == "prepared_32":
                if len(png_paths) != 32:
                    raise RuntimeError(
                        f"Expected 32 prepared PNG paths for {ex_id}, got {len(png_paths)}"
                    )
                cache_key = "png::" + "|".join(f"{p}:{s}" for p, s in png_entries)
            else:
                cache_key = f"vid::{video_path}:{video_sha}"

            q_text = str(row.get("question") or si.get("question") or gt_row.get("question"))
            opts = (
                row["options"]
                if "options" in row
                else (si["options"] if "options" in si else gt_row.get("options"))
            )
            tasks.append(
                {
                    "example_id": ex_id,
                    "raw_id": row.get("id", row.get("qid", ex_id)),
                    "dataset": dataset_name,
                    "scene_name": scene_name,
                    "question_type": str(row.get("question_type") or gt_row["question_type"]),
                    "question": q_text,
                    "options": opts,
                    "text": row.get("text"),
                    "ground_truth": str(gt_row["ground_truth"]),
                    "answer_type": gt_row.get("answer_type"),
                    "video_path": video_path,
                    "video_sha256": video_sha,
                    "png_paths": png_paths,
                    "png_shas": png_shas,
                    "cache_key": cache_key,
                }
            )
    else:
        raise ValueError(f"Unsupported dataset_mode: {args.dataset_mode}")

    if args.limit > 0:
        tasks = tasks[: args.limit]
    return tasks


def partition_tasks_by_scene(
    tasks: List[Dict[str, Any]], num_shards: int, shard_id: int
) -> List[Dict[str, Any]]:
    if num_shards <= 1:
        return tasks
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for t in tasks:
        groups[t["cache_key"]].append(t)
    sorted_keys = sorted(groups.keys(), key=lambda k: (-len(groups[k]), k))
    shard_loads = [0] * num_shards
    shard_tasks: List[List[Dict[str, Any]]] = [[] for _ in range(num_shards)]
    for k in sorted_keys:
        target_shard = min(range(num_shards), key=lambda s: (shard_loads[s], s))
        shard_tasks[target_shard].extend(groups[k])
        shard_loads[target_shard] += len(groups[k])
    return shard_tasks[shard_id]


def load_cp_model(args: argparse.Namespace):
    import importlib

    sys.path.insert(0, os.path.join(args.repo_dir, "vggt"))
    sys.path.insert(0, args.repo_dir)

    siglip_enc = importlib.import_module(f"{_CB}p.model.multimodal_encoder.siglip_encoder")
    cp_const = importlib.import_module(f"{_CB}p.constants")
    cp_conv = importlib.import_module(f"{_CB}p.conversation")
    cp_mm = importlib.import_module(f"{_CB}p.mm_utils")
    cp_builder = importlib.import_module(f"{_CB}p.model.builder")
    DEFAULT_IMAGE_TOKEN = cp_const.DEFAULT_IMAGE_TOKEN
    IMAGE_TOKEN_INDEX = cp_const.IMAGE_TOKEN_INDEX
    SeparatorStyle = cp_conv.SeparatorStyle
    conv_templates = cp_conv.conv_templates
    KeywordsStoppingCriteria = cp_mm.KeywordsStoppingCriteria
    tokenizer_image_token = cp_mm.tokenizer_image_token
    load_pretrained_model = cp_builder.load_pretrained_model

    orig_from_pretrained = siglip_enc.SigLipVisionModel.from_pretrained

    def patched_from_pretrained(pretrained_model_name_or_path, *a, **kw):
        if "siglip-so400m-patch14-384" in str(pretrained_model_name_or_path):
            pretrained_model_name_or_path = args.vision_dir
        kw["local_files_only"] = True
        return orig_from_pretrained(pretrained_model_name_or_path, *a, **kw)

    siglip_enc.SigLipVisionModel.from_pretrained = patched_from_pretrained

    overwrite_config: Dict[str, Any] = {
        "mm_spatial_pool_stride": 2,
        "mm_spatial_pool_mode": "bilinear",
        "use_camera_tokens": not args.disable_camera_tokens,
        "camera_tokens_mode": "camera_tokens",
        "query_mode": "query_after_question",
        "camera_tokens_place": "append_to_frame",
        "camera_token_indices": [0],
    }
    if args.cp_unpad:
        overwrite_config["unpad_image"] = True

    tokenizer, model, image_processor, _ = load_pretrained_model(
        args.model_dir,
        None,
        f"llava_{_QW}",
        device_map="cuda:0",
        multimodal=True,
        attn_implementation="sdpa",
        overwrite_config=overwrite_config,
    )
    model.rec_head_preds = False
    model.eval()
    return {
        "tokenizer": tokenizer,
        "model": model,
        "image_processor": image_processor,
        "DEFAULT_IMAGE_TOKEN": DEFAULT_IMAGE_TOKEN,
        "IMAGE_TOKEN_INDEX": IMAGE_TOKEN_INDEX,
        "SeparatorStyle": SeparatorStyle,
        "conv_templates": conv_templates,
        "KeywordsStoppingCriteria": KeywordsStoppingCriteria,
        "tokenizer_image_token": tokenizer_image_token,
    }


def prepare_cp_visual(
    bundle: Dict[str, Any], task: Dict[str, Any], args: argparse.Namespace
) -> Tuple[List[Any], List[int], int]:
    image_processor = bundle["image_processor"]
    if args.frame_source.startswith("video_"):
        exp_vsha = str(task.get("video_sha256") or "")
        if exp_vsha:
            act_vsha = _file_sha256(task["video_path"], required=True)
            if act_vsha != exp_vsha:
                raise RuntimeError(
                    f"Video SHA-256 mismatch for {task['video_path']}: expected {exp_vsha}, got {act_vsha}"
                )
        vr = VideoReader(task["video_path"], ctx=cpu(0), num_threads=1)
        total_frame_num = len(vr)
        uniform_sampled_frames = np.linspace(
            0, total_frame_num - 1, args.max_frames_num, dtype=int
        )
        frame_idx = uniform_sampled_frames.tolist()
        spare_frames = vr.get_batch(frame_idx).asnumpy()
    elif args.frame_source == "prepared_32":
        arrs = []
        png_shas = task.get("png_shas") or [""] * len(task["png_paths"])
        for p, exp_sha in zip(task["png_paths"], png_shas):
            arrs.append(np.array(read_verified_rgb_image(p, exp_sha)))
        spare_frames = np.stack(arrs, axis=0)
    else:
        raise ValueError(f"Unknown frame_source: {args.frame_source}")

    image_size = list(spare_frames.shape[1:3])  # [orig_h, orig_w]
    num_frames = int(spare_frames.shape[0])
    if args.cp_unpad:
        bg = tuple(int(x * 255) for x in image_processor.image_mean)
        frames_in = [
            expand2square(Image.fromarray(spare_frames[i], mode="RGB"), bg)
            for i in range(num_frames)
        ]
    else:
        frames_in = spare_frames

    frames_tensor = (
        image_processor.preprocess(frames_in, return_tensors="pt")["pixel_values"]
        .half()
        .cuda()
    )
    return [frames_tensor], image_size, num_frames


def run_cp_single(
    bundle: Dict[str, Any],
    visual_data: Tuple[List[Any], List[int], int],
    context: str,
    max_new_tokens: int,
) -> Tuple[str, int, int, Dict[str, Any]]:
    tokenizer = bundle["tokenizer"]
    model = bundle["model"]
    DEFAULT_IMAGE_TOKEN = bundle["DEFAULT_IMAGE_TOKEN"]
    IMAGE_TOKEN_INDEX = bundle["IMAGE_TOKEN_INDEX"]
    SeparatorStyle = bundle["SeparatorStyle"]
    conv_templates = bundle["conv_templates"]
    KeywordsStoppingCriteria = bundle["KeywordsStoppingCriteria"]
    tokenizer_image_token = bundle["tokenizer_image_token"]

    image_tensor, image_size, _ = visual_data
    question_input = DEFAULT_IMAGE_TOKEN + "\n" + context
    conv = conv_templates[f"{_QW}_1_5"].copy()
    conv.append_message(conv.roles[0], question_input)
    conv.append_message(conv.roles[1], None)
    prompt_question = conv.get_prompt()

    input_ids = (
        tokenizer_image_token(
            prompt_question, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt"
        )
        .unsqueeze(0)
        .cuda()
    )
    pad_token_ids = (
        tokenizer.pad_token_id
        if tokenizer.pad_token_id is not None
        else tokenizer.eos_token_id
    )
    attention_masks = input_ids.ne(pad_token_ids).cuda()
    stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
    stopping_criteria = KeywordsStoppingCriteria([stop_str], tokenizer, input_ids)

    with torch.inference_mode():
        cont, _ = model.generate(
            input_ids,
            attention_mask=attention_masks,
            pad_token_id=pad_token_ids,
            images=image_tensor,
            use_cache=True,
            image_sizes=image_size,
            modalities=["video"],
            stopping_criteria=[stopping_criteria],
            max_new_tokens=max_new_tokens,
            temperature=0,
            do_sample=False,
            top_p=None,
            num_beams=1,
        )
    out_tokens = int(cont.shape[1]) if cont.ndim == 2 else len(cont[0])
    in_tokens = int(input_ids.shape[1])
    text_outputs = tokenizer.batch_decode(cont, skip_special_tokens=True)
    return text_outputs[0].strip(), in_tokens, out_tokens, {}


def load_cs_model(args: argparse.Namespace):
    import importlib

    sys.path.insert(0, args.repo_dir)

    siglip2_enc = importlib.import_module(
        f"{_CB}.model.multimodal_encoder.llava_next_siglip_encoder"
    )
    cs_const = importlib.import_module(f"{_CB}.constants")
    cs_conv = importlib.import_module(f"{_CB}.conversation")
    cs_mm = importlib.import_module(f"{_CB}.mm_utils")
    cs_builder = importlib.import_module(f"{_CB}.model.builder")
    DEFAULT_IMAGE_TOKEN = cs_const.DEFAULT_IMAGE_TOKEN
    IMAGE_TOKEN_INDEX = cs_const.IMAGE_TOKEN_INDEX
    conv_templates = cs_conv.conv_templates
    tokenizer_image_token = cs_mm.tokenizer_image_token
    load_pretrained_model = cs_builder.load_pretrained_model

    cs_lm_mod = importlib.import_module(f"{_CB}.model.language_model.{_CB}_{_QW}2")
    cs_lm_cls = getattr(cs_lm_mod, f"{_CB_CAP}{_QW.capitalize()}ForCausalLM")
    orig_cs_forward = cs_lm_cls.forward

    def patched_cs_forward(
        self,
        input_ids=None,
        attention_mask=None,
        position_ids=None,
        past_key_values=None,
        inputs_embeds=None,
        labels=None,
        use_cache=None,
        output_attentions=None,
        output_hidden_states=None,
        images=None,
        return_dict=None,
        newline_token_indices=None,
        si_token_indices=None,
        miv_token_indices=None,
        nfp_token_indices=None,
        nfp_loss_masks=None,
        cache_position=None,
        **kwargs,
    ):
        return orig_cs_forward(
            self,
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            labels=labels,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            images=images,
            return_dict=return_dict,
            newline_token_indices=newline_token_indices,
            si_token_indices=si_token_indices,
            miv_token_indices=miv_token_indices,
            nfp_token_indices=nfp_token_indices,
            nfp_loss_masks=nfp_loss_masks,
        )

    cs_lm_cls.forward = patched_cs_forward

    orig_from_pretrained = siglip2_enc.SigLipVisionModel.from_pretrained

    def patched_from_pretrained(pretrained_model_name_or_path, *a, **kw):
        if "siglip2-so400m-patch14-384" in str(pretrained_model_name_or_path):
            pretrained_model_name_or_path = args.vision_dir
        kw["local_files_only"] = True
        return orig_from_pretrained(pretrained_model_name_or_path, *a, **kw)

    siglip2_enc.SigLipVisionModel.from_pretrained = patched_from_pretrained

    tokenizer, model, image_processor, _ = load_pretrained_model(
        args.model_dir,
        None,
        f"{_CB}_s_7b",
        device_map="cuda:0",
    )
    model.config.video_max_frames = args.max_frames_num
    model.config.video_fps = 1
    model.config.video_force_sample = False
    model.config.add_time_instruction = False
    model.config.miv_token_len = 64
    model.config.si_token_len = 729
    model.config.image_aspect_ratio = "anyres"
    model.config.anyres_max_subimages = 9
    model.eval()
    return {
        "tokenizer": tokenizer,
        "model": model,
        "image_processor": image_processor,
        "DEFAULT_IMAGE_TOKEN": DEFAULT_IMAGE_TOKEN,
        "IMAGE_TOKEN_INDEX": IMAGE_TOKEN_INDEX,
        "conv_templates": conv_templates,
        "tokenizer_image_token": tokenizer_image_token,
    }


def prepare_cs_visual(
    bundle: Dict[str, Any], task: Dict[str, Any], args: argparse.Namespace
) -> Tuple[List[Any], List[Tuple[int, int, int]], int]:
    processor_aux = bundle["image_processor"][0]
    if args.frame_source.startswith("video_"):
        exp_vsha = str(task.get("video_sha256") or "")
        if exp_vsha:
            act_vsha = _file_sha256(task["video_path"], required=True)
            if act_vsha != exp_vsha:
                raise RuntimeError(
                    f"Video SHA-256 mismatch for {task['video_path']}: expected {exp_vsha}, got {act_vsha}"
                )
        vr = VideoReader(task["video_path"], ctx=cpu(0), num_threads=1)
        total_frame_num = len(vr)
        avg_fps = max(1, round(vr.get_avg_fps() / 1))
        frame_idx = [i for i in range(0, total_frame_num, avg_fps)]
        if args.max_frames_num > 0 and len(frame_idx) > args.max_frames_num:
            uniform_sampled_frames = np.linspace(
                0, total_frame_num - 1, args.max_frames_num, dtype=int
            )
            frame_idx = uniform_sampled_frames.tolist()
        video = vr.get_batch(frame_idx).asnumpy()
        vr.seek(0)
        pil_imgs = [Image.fromarray(video[i]) for i in range(video.shape[0])]
    elif args.frame_source == "prepared_32":
        pil_imgs = []
        png_shas = task.get("png_shas") or [""] * len(task["png_paths"])
        for p, exp_sha in zip(task["png_paths"], png_shas):
            pil_imgs.append(read_verified_rgb_image(p, exp_sha))
    else:
        raise ValueError(f"Unknown frame_source: {args.frame_source}")

    num_frames = len(pil_imgs)
    orig_w, orig_h = pil_imgs[0].size
    visual_sizes = [(orig_w, orig_h, num_frames)]
    bg = tuple(int(x * 255) for x in processor_aux.image_mean)
    video_aux = [expand2square(img, bg) for img in pil_imgs]
    video_aux_tensor = processor_aux.preprocess(video_aux, return_tensors="pt")[
        "pixel_values"
    ]
    visual_tensors = [video_aux_tensor.unsqueeze(0).half().cuda()]
    return visual_tensors, visual_sizes, num_frames


def run_cs_single(
    bundle: Dict[str, Any],
    visual_data: Tuple[List[Any], List[Tuple[int, int, int]], int],
    context: str,
    max_new_tokens: int,
) -> Tuple[str, int, int, Dict[str, Any]]:
    tokenizer = bundle["tokenizer"]
    model = bundle["model"]
    DEFAULT_IMAGE_TOKEN = bundle["DEFAULT_IMAGE_TOKEN"]
    IMAGE_TOKEN_INDEX = bundle["IMAGE_TOKEN_INDEX"]
    conv_templates = bundle["conv_templates"]
    tokenizer_image_token = bundle["tokenizer_image_token"]

    visual_tensors, visual_sizes, _ = visual_data
    qs = DEFAULT_IMAGE_TOKEN + "\n" + context
    conv = conv_templates[f"{_QW}_2"].copy()
    conv.append_message(conv.roles[0], qs)
    conv.append_message(conv.roles[1], None)
    prompt = conv.get_prompt()

    input_ids = (
        tokenizer_image_token(
            prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt"
        )
        .unsqueeze(0)
        .cuda()
    )
    with torch.inference_mode():
        output_ids = model.generate(
            inputs=input_ids,
            images=visual_tensors,
            image_sizes=visual_sizes,
            use_cache=True,
            do_sample=False,
            temperature=0,
            top_p=None,
            num_beams=1,
            max_new_tokens=max_new_tokens,
        )
    out_tokens = int(output_ids.shape[1]) if output_ids.ndim == 2 else len(output_ids[0])
    in_tokens = int(input_ids.shape[1])
    text_outputs = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
    return text_outputs[0].strip(), in_tokens, out_tokens, {}


def _load_q35_full_weights(model: Any, fw_dir: str) -> Dict[str, Any]:
    from safetensors.torch import load_file

    directory = Path(fw_dir)
    manifest_path = directory / "full_weights.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "full-ft-export-v1" or manifest.get("dtype") != "bfloat16":
        raise ValueError(f"Unsupported full-weights export in {fw_dir}")
    index_pin = manifest["index"]
    index_path = directory / index_pin["name"]
    if _file_fast_or_full_sha256(str(index_path)) != index_pin["sha256"]:
        raise ValueError("Full-weights index SHA-256 differs from manifest")
    for item in manifest["files"]:
        fpath = directory / item["name"]
        if (
            Path(item["name"]).name != item["name"]
            or fpath.stat().st_size != item["bytes"]
            or _file_fast_or_full_sha256(str(fpath)) != item["sha256"]
        ):
            raise ValueError(f"Full-weights shard differs from manifest: {item['name']}")
    index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    files_set = {item["name"] for item in manifest["files"]}
    weight_map = index_doc["weight_map"]
    if set(weight_map.values()) != files_set or len(weight_map) != manifest["tensor_count"]:
        raise ValueError("Full-weights index and manifest disagree")

    live = {
        name: param
        for name, param in model.named_parameters()
        if not name.startswith(("geometry_input.", "auxiliary_heads."))
    }
    if set(weight_map) != set(live):
        missing = sorted(set(live) - set(weight_map))[:5]
        extra = sorted(set(weight_map) - set(live))[:5]
        raise ValueError(f"Full-weights tensors differ from model (missing {missing}, extra {extra})")

    loaded = 0
    for item in manifest["files"]:
        tensors = load_file(str(directory / item["name"]), device="cpu")
        with torch.no_grad():
            for name, value in tensors.items():
                parameter = live[name]
                if (
                    value.shape != parameter.shape
                    or value.dtype != torch.bfloat16
                    or parameter.dtype != torch.bfloat16
                ):
                    raise ValueError(f"Full-weights tensor shape or dtype differs: {name}")
                parameter.copy_(value.to(parameter.device))
                if not torch.equal(parameter.detach().cpu(), value):
                    raise ValueError(f"Full-weights tensor did not load exactly: {name}")
                loaded += 1
    if loaded != len(live):
        raise ValueError(f"Full-weights load covered {loaded}/{len(live)} base tensors")
    return {
        "full_weights_exact_equality": True,
        "tensors": loaded,
        "manifest_sha256": _file_fast_or_full_sha256(str(manifest_path)),
    }


def load_q35_model(args: argparse.Namespace) -> Dict[str, Any]:
    import transformers
    from transformers import AutoConfig, AutoProcessor, GenerationConfig, set_seed

    set_seed(17)
    snapshot = os.path.abspath(args.model_dir)
    max_new_tokens = resolve_max_new_tokens(args)
    enable_thinking = resolve_enable_thinking(args)

    processor = AutoProcessor.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False
    )
    processor.tokenizer.padding_side = "right"

    gen_cfg_file = os.path.join(snapshot, "generation_config.json")
    if os.path.isfile(gen_cfg_file):
        native_cfg = GenerationConfig.from_pretrained(snapshot, local_files_only=True)
    else:
        native_cfg = GenerationConfig.from_model_config(
            AutoConfig.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
        )
    effective_cfg = deepcopy(native_cfg)
    for k, v in Q35_DECODING_BASE.items():
        setattr(effective_cfg, k, v)
    effective_cfg.max_new_tokens = max_new_tokens
    effective_cfg.pad_token_id = processor.tokenizer.pad_token_id

    model_cls = getattr(transformers, f"{_QW_CAP}3_5ForConditionalGeneration")
    model = model_cls.from_pretrained(
        snapshot,
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.bfloat16,
        generation_config=effective_cfg,
        attn_implementation="sdpa",
        device_map={"": "cuda:0"},
    )

    fw_dir = _resolve_q35_full_weights_dir(args.adapter_dir)
    reload_evidence: Dict[str, Any] = {"mode": "base"}
    if fw_dir:
        reload_evidence = _load_q35_full_weights(model, fw_dir)
        print(
            f"[Shard {args.shard_id}] Loaded full-FT export from {fw_dir}: "
            f"tensors={reload_evidence['tensors']} manifest_sha256={reload_evidence['manifest_sha256']}",
            flush=True,
        )

    model.eval()
    model.requires_grad_(False)
    model.config.use_cache = True
    if getattr(model.config, "text_config", None) is not None:
        model.config.text_config.use_cache = True

    return {
        "processor": processor,
        "model": model,
        "generation_config": effective_cfg,
        "enable_thinking": enable_thinking,
        "reload_evidence": reload_evidence,
    }


def _sample_floor_uniform_indices(total: int, num_frames: int) -> List[int]:
    if total < num_frames:
        raise ValueError(f"Video has only {total} decoded frames, need {num_frames}")
    if num_frames == 1:
        return [0]
    return [k * (total - 1) // (num_frames - 1) for k in range(num_frames)]


def prepare_q35_visual(
    bundle: Dict[str, Any], task: Dict[str, Any], args: argparse.Namespace
) -> Tuple[Any, Dict[str, Any], int]:
    import av

    num_target = int(args.max_frames_num)
    if args.frame_source.startswith("video_"):
        exp_vsha = str(task.get("video_sha256") or "")
        if exp_vsha:
            act_vsha = _file_sha256(task["video_path"], required=True)
            if act_vsha != exp_vsha:
                raise RuntimeError(
                    f"Video SHA-256 mismatch for {task['video_path']}: expected {exp_vsha}, got {act_vsha}"
                )
        timestamps: List[float] = []
        sizes: List[Tuple[int, int]] = []
        with av.open(str(task["video_path"])) as container:
            if not container.streams.video:
                raise ValueError(f"Source {task['video_path']} has no video stream")
            stream = container.streams.video[0]
            fps_rate = stream.average_rate
            if fps_rate is None or float(fps_rate) <= 0:
                raise ValueError(f"Source {task['video_path']} has no original FPS")
            fps = float(fps_rate)
            for frame in container.decode(stream):
                if frame.pts is None or frame.time_base is None:
                    raise ValueError(f"Decoded frame in {task['video_path']} lacks PTS/time_base")
                timestamps.append(float(frame.pts * frame.time_base))
                sizes.append((frame.width, frame.height))
        total_num_frames = len(timestamps)
        indices = _sample_floor_uniform_indices(total_num_frames, num_target)
        selected_set = set(indices)
        frames_by_idx: Dict[int, Any] = {}
        with av.open(str(task["video_path"])) as container:
            for ordinal, frame in enumerate(container.decode(video=0)):
                if ordinal not in selected_set:
                    continue
                frames_by_idx[ordinal] = frame.to_ndarray(format="rgb24")
        arrays = np.stack([frames_by_idx[i] for i in indices], axis=0)
        height, width = int(arrays.shape[1]), int(arrays.shape[2])
        meta_kwargs = {
            "total_num_frames": total_num_frames,
            "fps": fps,
            "frames_indices": indices,
            "width": width,
            "height": height,
        }
        return arrays, meta_kwargs, num_target
    elif args.frame_source == "prepared_32":
        arrs = []
        png_shas = task.get("png_shas") or [""] * len(task["png_paths"])
        for p, exp_sha in zip(task["png_paths"], png_shas):
            arrs.append(np.asarray(read_verified_rgb_image(p, exp_sha)).copy())
        arrays = np.stack(arrs, axis=0)
        height, width = int(arrays.shape[1]), int(arrays.shape[2])
        num_frames = int(arrays.shape[0])
        meta_kwargs = {
            "total_num_frames": num_frames,
            "fps": 1.0,
            "frames_indices": list(range(num_frames)),
            "width": width,
            "height": height,
        }
        return arrays, meta_kwargs, num_frames
    else:
        raise ValueError(f"Unknown frame_source: {args.frame_source}")


def extract_q35_final_answer(raw_text: str, enable_thinking: bool) -> Tuple[str, str]:
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "", "empty_generation"
    close_matches = list(re.finditer(r"</think\s*>", raw_text, flags=re.IGNORECASE))
    if enable_thinking and not close_matches:
        return "", "unclosed_thinking"
    text = raw_text[close_matches[-1].end() :] if close_matches else raw_text
    if re.search(r"<think\s*>", text, flags=re.IGNORECASE):
        return "", "unclosed_thinking"
    text = re.sub(r"(?:\s*<\|(?:im_end|endoftext)\|>)+\s*$", "", text).strip()
    matches = list(_BLOCK_RE.finditer(text))
    if matches:
        return matches[-1].group(1).strip(), "tag"
    lines = [m.group(0).strip() for m in re.finditer(r"[^\r\n]+", text) if m.group(0).strip()]
    if not lines:
        return "", "empty_visible_suffix"
    payload = re.sub(
        r"^(?:final\s+answer|answer)\s*:\s*", "", lines[-1], flags=re.IGNORECASE
    ).strip()
    return payload, "final_line"


def run_q35_single(
    bundle: Dict[str, Any],
    visual_data: Tuple[Any, Dict[str, Any], int],
    context: str,
    max_new_tokens: int,
) -> Tuple[str, int, int, Dict[str, Any]]:
    from transformers.video_utils import VideoMetadata

    processor = bundle["processor"]
    model = bundle["model"]
    generation_config = bundle["generation_config"]
    enable_thinking = bundle["enable_thinking"]

    arrays, meta_kwargs, _ = visual_data
    metadata = VideoMetadata(**meta_kwargs)
    messages = [
        {
            "role": "user",
            "content": [{"type": "video"}, {"type": "text", "text": context}],
        }
    ]
    prompt = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=enable_thinking,
    )
    batch = processor(
        text=[prompt],
        videos=[arrays],
        video_metadata=[metadata],
        do_sample_frames=False,
        size=Q35_RGB_SIZE,
        return_tensors="pt",
        return_metadata=True,
        truncation=False,
        padding=False,
    )
    batch.pop("video_metadata", None)
    in_tokens = int(batch["input_ids"].shape[1])
    device_batch = {k: v.to("cuda:0") for k, v in batch.items()}
    with torch.inference_mode():
        generated = model.generate(**device_batch, generation_config=generation_config)
    gen_tokens = generated.sequences[0, in_tokens:].detach().cpu().tolist()
    out_tokens = len(gen_tokens)
    raw_text = processor.tokenizer.decode(gen_tokens, skip_special_tokens=False)
    display_text = processor.tokenizer.decode(gen_tokens, skip_special_tokens=True)
    del generated, device_batch

    final_ans, extract_branch = extract_q35_final_answer(raw_text, enable_thinking=enable_thinking)
    extra = {
        "raw_generation": raw_text,
        "display_generation": display_text,
        "extract_branch": extract_branch,
        "enable_thinking": enable_thinking,
    }
    return final_ans, in_tokens, out_tokens, extra


def run_worker(args: argparse.Namespace) -> None:
    proto = build_protocol_meta(args)
    verify_or_write_protocol(args.output_dir, proto)
    max_new_tokens = proto["max_new_tokens"]
    cfg_sha = proto["config_sha256"]

    out_file = os.path.join(args.output_dir, f"shard_{args.shard_id:02d}.jsonl")

    completed_ids = set()
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("config_sha256") != cfg_sha:
                    raise RuntimeError(
                        f"Shard {out_file} contains record with mismatched config_sha256: "
                        f"{rec.get('config_sha256')} != {cfg_sha}"
                    )
                completed_ids.add(str(rec["example_id"]))

    all_tasks = load_tasks(args)
    my_tasks = partition_tasks_by_scene(all_tasks, args.num_shards, args.shard_id)
    pending_tasks = [t for t in my_tasks if t["example_id"] not in completed_ids]
    print(
        f"[Shard {args.shard_id}/{args.num_shards}] total={len(my_tasks)} "
        f"done={len(completed_ids)} pending={len(pending_tasks)}",
        flush=True,
    )
    if not pending_tasks:
        return

    t0 = time.time()
    if args.arch == "cp":
        bundle = load_cp_model(args)
        prepare_fn = prepare_cp_visual
        infer_fn = run_cp_single
    elif args.arch == "cs":
        bundle = load_cs_model(args)
        prepare_fn = prepare_cs_visual
        infer_fn = run_cs_single
    elif args.arch == "q35":
        bundle = load_q35_model(args)
        prepare_fn = prepare_q35_visual
        infer_fn = run_q35_single
    else:
        raise ValueError(f"Unknown arch: {args.arch}")
    print(
        f"[Shard {args.shard_id}] Loaded {args.arch} model in {time.time() - t0:.1f}s",
        flush=True,
    )

    current_cache_key = None
    current_visual = None

    with open(out_file, "a", encoding="utf-8") as fout:
        for idx, task in enumerate(pending_tasks):
            item_t0 = time.time()
            if task["cache_key"] != current_cache_key:
                current_visual = None
                torch.cuda.empty_cache()
                current_visual = prepare_fn(bundle, task, args)
                current_cache_key = task["cache_key"]

            context = build_prompt_context(task, args.prompt_mode)
            response_text, in_tokens, out_tokens, extra_fields = infer_fn(
                bundle, current_visual, context, max_new_tokens
            )
            elapsed = time.time() - item_t0
            num_frames = current_visual[2]

            record = {
                "example_id": task["example_id"],
                "raw_id": task["raw_id"],
                "dataset": task["dataset"],
                "scene_name": task["scene_name"],
                "question_type": task["question_type"],
                "question": task["question"],
                "options": task["options"],
                "ground_truth": task["ground_truth"],
                "answer_type": task.get("answer_type"),
                "response_text": response_text,
                "num_frames": num_frames,
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "elapsed_s": round(elapsed, 4),
                "arch": args.arch,
                "frame_source": args.frame_source,
                "prompt_mode": args.prompt_mode,
                "max_new_tokens": max_new_tokens,
                "cp_unpad": bool(args.cp_unpad),
                "disable_camera_tokens": bool(args.disable_camera_tokens),
                "config_sha256": cfg_sha,
            }
            if extra_fields:
                record.update(extra_fields)
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            fout.flush()

            if (idx + 1) % 10 == 0 or (idx + 1) == len(pending_tasks):
                print(
                    f"[Shard {args.shard_id}] {idx + 1}/{len(pending_tasks)} "
                    f"({task['example_id']}) frames={num_frames} out_tok={out_tokens} "
                    f"dt={elapsed:.2f}s resp={response_text[:80]!r}",
                    flush=True,
                )


def resolve_worker_visible_devices(num_workers: int) -> List[str]:
    if "CUDA_VISIBLE_DEVICES" in os.environ:
        inherited = os.environ["CUDA_VISIBLE_DEVICES"].strip()
        tokens = [m.group(0).strip() for m in re.finditer(r"[^,]+", inherited) if m.group(0).strip()]
        if len(tokens) < num_workers:
            raise RuntimeError(
                f"Inherited CUDA_VISIBLE_DEVICES={inherited!r} has only {len(tokens)} devices, "
                f"need {num_workers}"
            )
        return tokens[:num_workers]
    return [str(i) for i in range(num_workers)]


def merge_shards_only(args: argparse.Namespace) -> None:
    proto = build_protocol_meta(args)
    cfg_sha = proto["config_sha256"]
    num_shards = int(args.num_shards)

    merged_by_id: Dict[str, Dict[str, Any]] = {}
    for shard_id in range(num_shards):
        shard_path = os.path.join(args.output_dir, f"shard_{shard_id:02d}.jsonl")
        if not os.path.exists(shard_path):
            continue
        with open(shard_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("config_sha256") != cfg_sha:
                    raise RuntimeError(
                        f"Mismatched config_sha256 in {shard_path}: {rec.get('config_sha256')} != {cfg_sha}"
                    )
                ex_id = str(rec["example_id"])
                if ex_id in merged_by_id:
                    raise RuntimeError(f"Duplicate prediction for {ex_id} in {shard_path}")
                merged_by_id[ex_id] = rec

    all_tasks = load_tasks(args)
    merged_path = os.path.join(args.output_dir, "predictions.jsonl")
    with open(merged_path, "w", encoding="utf-8") as fout:
        for t in all_tasks:
            ex_id = t["example_id"]
            if ex_id not in merged_by_id:
                raise RuntimeError(
                    f"Missing prediction for {ex_id} (got {len(merged_by_id)}/{len(all_tasks)})"
                )
            fout.write(json.dumps(merged_by_id[ex_id], ensure_ascii=False) + "\n")
    print(
        f"[Master] Merged {len(merged_by_id)} predictions into {merged_path}",
        flush=True,
    )


def launch_multi_workers(args: argparse.Namespace) -> None:
    proto = build_protocol_meta(args)
    verify_or_write_protocol(args.output_dir, proto)
    max_new_tokens = proto["max_new_tokens"]

    num_workers = args.launch_workers
    gpu_tokens = resolve_worker_visible_devices(num_workers)
    procs = []
    log_handles = []

    base_cmd = [
        sys.executable,
        "-I",
        os.path.abspath(__file__),
        "--arch",
        args.arch,
        "--dataset_mode",
        args.dataset_mode,
        "--frame_source",
        args.frame_source,
        "--prompt_mode",
        args.prompt_mode,
        "--max_new_tokens",
        str(max_new_tokens),
        "--max_frames_num",
        str(args.max_frames_num),
        "--model_dir",
        args.model_dir,
        "--video_root",
        args.video_root,
        "--output_dir",
        args.output_dir,
        "--num_shards",
        str(num_workers),
        "--thinking",
        args.thinking,
    ]
    if args.repo_dir:
        base_cmd.extend(["--repo_dir", args.repo_dir])
    if args.vision_dir:
        base_cmd.extend(["--vision_dir", args.vision_dir])
    if args.adapter_dir:
        base_cmd.extend(["--adapter_dir", args.adapter_dir])
    if args.meta_jsonl:
        base_cmd.extend(["--meta_jsonl", args.meta_jsonl])
    if args.prepared_dir:
        base_cmd.extend(["--prepared_dir", args.prepared_dir])
    if args.data2_root:
        base_cmd.extend(["--data2_root", args.data2_root])
    if args.limit > 0:
        base_cmd.extend(["--limit", str(args.limit)])
    if args.cp_unpad:
        base_cmd.append("--cp_unpad")
    if args.disable_camera_tokens:
        base_cmd.append("--disable_camera_tokens")

    for shard_id in range(num_workers):
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = gpu_tokens[shard_id]
        log_path = os.path.join(args.output_dir, f"worker_{shard_id:02d}.log")
        lf = open(log_path, "a", encoding="utf-8")
        log_handles.append(lf)
        cmd = base_cmd + ["--shard_id", str(shard_id)]
        p = subprocess.Popen(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT)
        procs.append((shard_id, p))

    failed = []
    for shard_id, p in procs:
        rc = p.wait()
        if rc != 0:
            failed.append((shard_id, rc))
    for lf in log_handles:
        lf.close()

    if failed:
        raise RuntimeError(f"Workers failed: {failed}")

    args.num_shards = num_workers
    merge_shards_only(args)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--arch", choices=["cp", "cs", "q35"], required=True)
    p.add_argument(
        "--dataset_mode", choices=["official_full", "prepared_cell"], required=True
    )
    p.add_argument(
        "--frame_source",
        choices=["video_128", "video_32", "prepared_32"],
        required=True,
    )
    p.add_argument("--prompt_mode", choices=["official", "ours"], required=True)
    p.add_argument("--thinking", choices=["auto", "on", "off"], default="auto")
    p.add_argument("--max_new_tokens", type=int, default=None)
    p.add_argument("--max_frames_num", type=int, default=None)
    p.add_argument("--model_dir", required=True)
    p.add_argument("--adapter_dir", default="")
    p.add_argument("--repo_dir", default="")
    p.add_argument("--vision_dir", default="")
    p.add_argument("--video_root", required=True)
    p.add_argument("--meta_jsonl", default="")
    p.add_argument("--prepared_dir", default="")
    p.add_argument("--data2_root", default="")
    p.add_argument("--output_dir", required=True)
    p.add_argument("--num_shards", type=int, default=1)
    p.add_argument("--shard_id", type=int, default=0)
    p.add_argument("--launch_workers", type=int, default=0)
    p.add_argument("--merge_only", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--cp_unpad", action="store_true")
    p.add_argument("--disable_camera_tokens", action="store_true")
    args = p.parse_args()
    if args.max_frames_num is None:
        if args.frame_source == "video_32" or args.frame_source == "prepared_32":
            args.max_frames_num = 32
        else:
            args.max_frames_num = 128
    return args


def main() -> None:
    args = parse_args()
    if args.merge_only:
        merge_shards_only(args)
    elif args.launch_workers > 0:
        launch_multi_workers(args)
    else:
        run_worker(args)


if __name__ == "__main__":
    main()
