"""Spatial-V2 Stage-2 Data Pipeline: RoomExclusionGuard + K1 3D + E05 Multi-Turn Epistemic Traces + 4D Masking.

Enforces:
  1. Fail-closed `Stage2RoomExclusionGuard` across all 6 canonical lab blocklists (`R0`, `dev-S1`,
     `BENCH_v2`, `withheld-80`, `K1-heldout`, and `ReSTI_ScanNet` `scene0000..0149`) on BOTH 3D capture
     records AND `E05` trace JSONL rows. Refuses to load any held-out room into training.
  2. Multi-turn `E05` epistemic trace tokenization (`<verify>`, `<think>`, `<geo>`, `<tool_response>`,
     `<tool_obs>`, `<answer>`) with loss strictly on assistant turns (`labels != -100`) and `-100`
     masking on user prompts, visual tokens, `<tool_response>`, and `<tool_obs>`.
  3. Capture/epoch-keyed deterministic view selection + dedicated DataLoader generator (fixing Codex
     Stage-1A item #2 so Arm B and Arm C receive identical sample & frame ordering under the same seed).
  4. `has_4d_teacher` dynamic 4D teacher tensor schema (`y_stat_gt`, `delta_p_gt`, `flow_valid`) so
     static 3D rooms and dynamic 4D clips train in the same batch.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from .data_k1_local import (
    DEFAULT_EXCL_DIR,
    DEFAULT_FRAMES_ROOT,
    DEFAULT_MANIFEST_PATH,
    IMAGENET_MEAN,
    IMAGENET_STD,
    QWEN_MEAN,
    QWEN_STD,
    CaptureRecord,
    RoomExclusionGuard,
    _load_rgb_tensor,
    _masked_downsample_depth,
    _scale_intrinsics,
    build_clean_k1_splits,
    canonical_room_keys,
)
from .geo_heads import (
    build_intrinsics_matrix,
    compute_gravity_leveled_poses,
    compute_plucker_rays,
    so3_exp,
    unproject_depth,
)

DEFAULT_E05_JSONL = "/scratch/jjyeung/orch_home_distill/e05_api_factory/pilot0_smoke.jsonl"

_SPAN_TAG_RE = re.compile(
    r"(<(?:verify|think|geo|tool_response|tool_obs|answer)>.*?</(?:verify|think|geo|tool_response|tool_obs|answer)>)",
    re.DOTALL,
)
_ASSISTANT_TAGS = ("<verify>", "<think>", "<geo>", "<answer>")
_TOOL_TAGS = ("<tool_response>", "<tool_obs>")


class Stage2RoomExclusionGuard(RoomExclusionGuard):
    """Extends RoomExclusionGuard with ReSTI ScanNet 0000..0149 blocklist & hard train assertion."""

    def __init__(self, excl_dir: str | Path = DEFAULT_EXCL_DIR) -> None:
        self.resti_scannet: set[str] = {f"scannet/scene{i:04d}" for i in range(150)}
        super().__init__(excl_dir=excl_dir)
        self.blocklists["ReSTI_ScanNet"] = set()
        self._add_many("ReSTI_ScanNet", self.resti_scannet)
        # Verify ReSTI ScanNet canary with synthetic rescan suffix
        if "ReSTI_ScanNet" not in self.hits_for_capture("scannet/scene0042_99", "scannet/scene0042"):
            raise RuntimeError("ReSTI_ScanNet canary check failed for scannet/scene0042_99")

    def assert_room_allowed_for_train(
        self, canonical: str, room: Optional[str] = None, k1_split: Optional[str] = None
    ) -> None:
        hits = self.hits_for_capture(canonical, room, k1_split=k1_split)
        if hits:
            raise RuntimeError(
                f"RoomExclusionGuard REFUSED held-out/forbidden room in Stage-2 train: "
                f"canonical={canonical!r}, room={room!r}, hits={hits}"
            )


# ---------------------------------------------------------------------------
# E05 Multi-Turn Epistemic Trace Formatting & Assistant-Only Loss Masking
# ---------------------------------------------------------------------------


@dataclass
class EncodedEpistemicTrace:
    input_ids: torch.Tensor  # [seq_len] long
    attention_mask: torch.Tensor  # [seq_len] long
    labels: torch.Tensor  # [seq_len] long (-100 on prompt & tool_response/tool_obs; token_id on assistant turns)
    assistant_token_count: int
    masked_token_count: int
    wire_text: str


class DeterministicTraceTokenizer:
    """Self-contained deterministic word/XML tokenizer for offline tests & zero-disk VRAM smoke runs."""

    def __init__(self, vocab_size: int = 248320, pad_token_id: int = 0, eos_token_id: int = 2) -> None:
        self.vocab_size = vocab_size
        self.pad_token_id = pad_token_id
        self.eos_token_id = eos_token_id
        self._special = {
            "<pad>": 0,
            "<bos>": 1,
            "<eos>": 2,
            "<verify>": 10,
            "</verify>": 11,
            "<think>": 12,
            "</think>": 13,
            "<geo>": 14,
            "</geo>": 15,
            "<tool_response>": 16,
            "</tool_response>": 17,
            "<tool_obs>": 18,
            "</tool_obs>": 19,
            "<answer>": 20,
            "</answer>": 21,
        }
        self._tok_re = re.compile(r"</?[a-z_]+>|[A-Za-z0-9_.\-]+|[^\sA-Za-z0-9_.\-]")

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        tokens = self._tok_re.findall(text)
        ids: List[int] = []
        mod = max(self.vocab_size - 64, 256)
        for tok in tokens:
            if tok in self._special:
                ids.append(self._special[tok])
            else:
                h = int.from_bytes(hashlib.md5(tok.encode("utf-8")).digest()[:4], "little")
                ids.append(64 + (h % mod))
        if add_special_tokens:
            ids.append(self.eos_token_id)
        return ids


def build_spans_from_e05_row(
    prompt: str,
    trace_turns: Optional[Sequence[Dict[str, object]]] = None,
    wire_xml: Optional[str] = None,
) -> List[Tuple[Literal["user", "assistant", "tool"], str]]:
    """Convert an E05 row (`trace_turns` or `wire_xml`) into role-tagged spans for strict assistant masking.

    Guarantees that:
      - User prompt spans have role `"user"` (`labels = -100`).
      - `<verify>...</verify>`, `<think>...</think>`, `<geo>...</geo>`, `<answer>...</answer>`
        have role `"assistant"` (`labels = input_ids`).
      - `<tool_response>...</tool_response>` and `<tool_obs>...</tool_obs>` have role `"tool"` (`labels = -100`).
    """
    spans: List[Tuple[Literal["user", "assistant", "tool"], str]] = [
        ("user", f"<|im_start|>user\n{prompt.strip()}<|im_end|>\n<|im_start|>assistant\n")
    ]

    if trace_turns:
        for turn in trace_turns:
            if "verify" in turn and turn["verify"]:
                v_txt = str(turn["verify"]).strip()
                if not v_txt.startswith("<verify>"):
                    v_txt = f"<verify>{v_txt}</verify>"
                spans.append(("assistant", v_txt + "\n"))
            if "think" in turn and turn["think"]:
                t_txt = str(turn["think"]).strip()
                if not t_txt.startswith("<think>"):
                    t_txt = f"<think>{t_txt}</think>"
                spans.append(("assistant", t_txt + "\n"))
            call_txt = turn.get("call") or turn.get("geo")
            if call_txt:
                c_str = str(call_txt).strip()
                if not c_str.startswith("<geo>"):
                    c_str = f"<geo>{c_str}</geo>"
                spans.append(("assistant", c_str + "\n"))
            if "tool_response" in turn and turn["tool_response"] is not None:
                tr = str(turn["tool_response"]).strip()
                if not tr.startswith("<tool_response>"):
                    tr = f"<tool_response>{tr}</tool_response>"
                spans.append(("tool", tr + "\n"))
            if "tool_obs" in turn and turn["tool_obs"] is not None:
                to = str(turn["tool_obs"]).strip()
                if not to.startswith("<tool_obs>"):
                    to = f"<tool_obs>{to}</tool_obs>"
                spans.append(("tool", to + "\n"))
            if "answer" in turn and turn["answer"] is not None:
                ans = str(turn["answer"]).strip()
                if not ans.startswith("<answer>"):
                    ans = f"<answer>{ans}</answer>"
                spans.append(("assistant", ans + "<|im_end|>\n"))
        return spans

    if wire_xml:
        parts = _SPAN_TAG_RE.split(wire_xml.strip())
        for part in parts:
            s = part.strip()
            if not s:
                continue
            if any(s.startswith(tag) for tag in _TOOL_TAGS):
                spans.append(("tool", s + "\n"))
            elif any(s.startswith(tag) for tag in _ASSISTANT_TAGS):
                suffix = "<|im_end|>\n" if s.startswith("<answer>") else "\n"
                spans.append(("assistant", s + suffix))
            else:
                spans.append(("assistant", s + "\n"))
        return spans

    raise ValueError("E05 trace row must provide either trace_turns or wire_xml")


def encode_e05_epistemic_trace(
    prompt: str,
    trace_turns: Optional[Sequence[Dict[str, object]]] = None,
    wire_xml: Optional[str] = None,
    tokenizer: Optional[object] = None,
    max_seq_len: int = 512,
    vocab_size: int = 248320,
) -> EncodedEpistemicTrace:
    """Encode an E05 multi-turn epistemic trace with loss strictly on assistant turns."""
    tok = tokenizer if tokenizer is not None else DeterministicTraceTokenizer(vocab_size=vocab_size)
    spans = build_spans_from_e05_row(prompt=prompt, trace_turns=trace_turns, wire_xml=wire_xml)

    input_ids: List[int] = []
    labels: List[int] = []
    wire_chunks: List[str] = []

    for role, text in spans:
        wire_chunks.append(text)
        if hasattr(tok, "encode"):
            piece_ids = list(tok.encode(text, add_special_tokens=False))
        else:
            piece_ids = list(tok(text, add_special_tokens=False)["input_ids"])
        input_ids.extend(piece_ids)
        if role == "assistant":
            labels.extend(piece_ids)
        else:
            labels.extend([-100] * len(piece_ids))

    # Truncate or right-pad to max_seq_len, ensuring both masked prompt and assistant tokens remain
    if len(input_ids) > max_seq_len:
        if all(l == -100 for l in labels[:max_seq_len]) and any(l != -100 for l in labels):
            first_asst = next(i for i, l in enumerate(labels) if l != -100)
            keep_prompt = max(1, min(first_asst, max_seq_len // 3))
            keep_rest = max_seq_len - keep_prompt
            input_ids = input_ids[:keep_prompt] + input_ids[first_asst : first_asst + keep_rest]
            labels = labels[:keep_prompt] + labels[first_asst : first_asst + keep_rest]
        else:
            input_ids = input_ids[:max_seq_len]
            labels = labels[:max_seq_len]

    valid_len = len(input_ids)
    attn_mask = [1] * valid_len
    pad_id = int(getattr(tok, "pad_token_id", 0) or 0)
    if valid_len < max_seq_len:
        pad_n = max_seq_len - valid_len
        input_ids.extend([pad_id] * pad_n)
        labels.extend([-100] * pad_n)
        attn_mask.extend([0] * pad_n)

    ids_t = torch.tensor(input_ids, dtype=torch.long)
    attn_t = torch.tensor(attn_mask, dtype=torch.long)
    lbl_t = torch.tensor(labels, dtype=torch.long)
    asst_cnt = int((lbl_t != -100).sum().item())
    masked_cnt = int(((lbl_t == -100) & (attn_t == 1)).sum().item())

    return EncodedEpistemicTrace(
        input_ids=ids_t,
        attention_mask=attn_t,
        labels=lbl_t,
        assistant_token_count=asst_cnt,
        masked_token_count=masked_cnt,
        wire_text="".join(wire_chunks),
    )


def load_clean_e05_traces(
    jsonl_path: str | Path = DEFAULT_E05_JSONL,
    guard: Optional[Stage2RoomExclusionGuard] = None,
) -> Tuple[List[Dict[str, object]], Dict[str, List[Dict[str, object]]]]:
    """Load E05 multi-turn traces and verify zero held-out/benchmark room leakage."""
    active_guard = guard if guard is not None else Stage2RoomExclusionGuard()
    rows: List[Dict[str, object]] = []
    by_scene: Dict[str, List[Dict[str, object]]] = {}

    path = Path(jsonl_path)
    if not path.is_file():
        return rows, by_scene

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            row = json.loads(s)
            scene = str(row.get("canonical_scene", row.get("canonical", "")))
            room = str(row.get("canonical_room", row.get("room", scene)))
            # Hard assertion: refuse any row belonging to a held-out or benchmark room
            active_guard.assert_room_allowed_for_train(scene, room)
            rows.append(row)
            by_scene.setdefault(scene, []).append(row)
    return rows, by_scene


# ---------------------------------------------------------------------------
# Stage-2 Unified Spatial Dataset (K1 3D + E05 Multi-Turn Traces + 4D Masking)
# ---------------------------------------------------------------------------


class Stage2SpatialDataset(Dataset):
    """Stage-2 dataset combining clean K1 3D captures, E05 multi-turn traces, and 4D teacher masking."""

    def __init__(
        self,
        split: Literal["train", "val"] = "train",
        num_views: int = 8,
        grid_h: int = 20,
        grid_w: int = 20,
        max_seq_len: int = 256,
        vocab_size: int = 248320,
        flow_horizons: Tuple[int, ...] = (-1, 1, 4, 16),
        manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
        frames_root: str | Path = DEFAULT_FRAMES_ROOT,
        excl_dir: str | Path = DEFAULT_EXCL_DIR,
        e05_jsonl: Optional[str | Path] = DEFAULT_E05_JSONL,
        records_override: Optional[Sequence[CaptureRecord]] = None,
        random_subsample: bool = False,
        seed: int = 20261128,
        max_captures: Optional[int] = None,
        tokenizer: Optional[object] = None,
    ) -> None:
        super().__init__()
        if grid_h % 2 != 0 or grid_w % 2 != 0:
            raise ValueError(f"grid_h and grid_w must be even, got {(grid_h, grid_w)}")

        self.guard = Stage2RoomExclusionGuard(excl_dir=excl_dir)
        self.split = split
        self.num_views = num_views
        self.grid_h = grid_h
        self.grid_w = grid_w
        self.hm = grid_h // 2
        self.wm = grid_w // 2
        self.max_seq_len = max_seq_len
        self.vocab_size = vocab_size
        self.flow_horizons = tuple(flow_horizons)
        self.random_subsample = random_subsample and (split == "train")
        self.seed = seed
        self.epoch = 0
        self.tokenizer = tokenizer if tokenizer is not None else DeterministicTraceTokenizer(vocab_size=vocab_size)

        if records_override is not None:
            recs = list(records_override)
        else:
            train_recs, val_recs, _, summary = build_clean_k1_splits(
                manifest_path=manifest_path,
                frames_root=frames_root,
                excl_dir=excl_dir,
            )
            self.split_summary = summary
            recs = train_recs if split == "train" else val_recs

        # Enforce hard RoomExclusionGuard verification on every training capture
        if split == "train":
            for r in recs:
                self.guard.assert_room_allowed_for_train(r.canonical, r.room, k1_split=r.k1_split)

        if max_captures is not None:
            recs = recs[:max_captures]
        self.records: List[CaptureRecord] = recs

        self.e05_rows: List[Dict[str, object]] = []
        self.e05_by_scene: Dict[str, List[Dict[str, object]]] = {}
        if split == "train" and e05_jsonl is not None and Path(e05_jsonl).is_file():
            self.e05_rows, self.e05_by_scene = load_clean_e05_traces(e05_jsonl, guard=self.guard)

    def set_epoch(self, epoch: int) -> None:
        self.epoch = int(epoch)

    def __len__(self) -> int:
        return len(self.records)

    def _select_indices_deterministic(self, canonical: str, valid_flags: np.ndarray) -> np.ndarray:
        """Capture/epoch-keyed view sampling (fixes Codex Stage-1A item #2)."""
        n_total = len(valid_flags)
        valid_idx = np.where(valid_flags)[0]
        pool = valid_idx if len(valid_idx) >= self.num_views else np.arange(n_total)
        if len(pool) == self.num_views:
            return pool.astype(np.int64)
        if self.random_subsample and len(pool) > self.num_views:
            key_str = f"{canonical}::seed={self.seed}::epoch={self.epoch}"
            sub_seed = int.from_bytes(hashlib.sha256(key_str.encode("utf-8")).digest()[:8], "little")
            local_rng = np.random.default_rng(sub_seed)
            edges = np.linspace(0, len(pool), self.num_views + 1)
            chosen = []
            for i in range(self.num_views):
                lo = int(math.floor(edges[i]))
                hi = min(max(lo + 1, int(math.floor(edges[i + 1]))), len(pool))
                chosen.append(pool[int(local_rng.integers(lo, hi))])
            return np.asarray(chosen, dtype=np.int64)
        pos = np.linspace(0, len(pool) - 1, self.num_views).round().astype(np.int64)
        return pool[pos].astype(np.int64)

    def _build_trace_for_capture(
        self,
        rec: CaptureRecord,
        idx: int,
        depth_gt: torch.Tensor,
        depth_valid: torch.Tensor,
        trans_gt: torch.Tensor,
    ) -> EncodedEpistemicTrace:
        scene_rows = self.e05_by_scene.get(rec.canonical)
        if scene_rows:
            row = scene_rows[(idx + self.epoch) % len(scene_rows)]
            return encode_e05_epistemic_trace(
                prompt=str(row["prompt"]),
                trace_turns=row.get("trace_turns"),  # type: ignore[arg-type]
                wire_xml=row.get("wire_xml"),  # type: ignore[arg-type]
                tokenizer=self.tokenizer,
                max_seq_len=self.max_seq_len,
                vocab_size=self.vocab_size,
            )
        if self.e05_rows:
            row = self.e05_rows[(idx + self.epoch) % len(self.e05_rows)]
            return encode_e05_epistemic_trace(
                prompt=str(row["prompt"]),
                trace_turns=row.get("trace_turns"),  # type: ignore[arg-type]
                wire_xml=row.get("wire_xml"),  # type: ignore[arg-type]
                tokenizer=self.tokenizer,
                max_seq_len=self.max_seq_len,
                vocab_size=self.vocab_size,
            )

        # Fallback grounded multi-turn epistemic trace from real capture metric depth & camera translation
        med_d = float(depth_gt[depth_valid].median().item()) if depth_valid.any() else 2.0
        cam_disp = float((trans_gt[-1] - trans_gt[0]).norm().item())
        ans_val = round(med_d, 2)
        turns = [
            {
                "verify": f"Check camera baseline ({cam_disp:.2f} m across {self.num_views} views) and depth conditioning.",
                "think": "Intent: measure primary anchor distance in meters using gravity-leveled 3D slots.",
                "call": '<geo>{"op":"locate","q":"anchor_surface"}</geo>',
                "tool_response": json.dumps(
                    {"status": "OK", "count": 1, "slots": [{"id": "s1", "z_med_m": ans_val}], "pose_cond_deg": 1.5}
                ),
            },
            {
                "think": f"Slot s1 verified with OK status at {ans_val:.2f} m. Emit final metric answer.",
                "answer": f"{ans_val:.2f}",
            },
        ]
        return encode_e05_epistemic_trace(
            prompt="In meters, report the verified 3D distance to the primary visible surface.",
            trace_turns=turns,
            tokenizer=self.tokenizer,
            max_seq_len=self.max_seq_len,
            vocab_size=self.vocab_size,
        )

    def __getitem__(self, idx: int) -> Dict[str, object]:
        rec = self.records[idx]
        if self.split == "train":
            self.guard.assert_room_allowed_for_train(rec.canonical, rec.room, k1_split=rec.k1_split)

        with np.load(rec.gt_path, allow_pickle=False) as z:
            depth_all = z["depth"]
            K_all = z["K_frames"] if "K_frames" in z.files else np.broadcast_to(z["K"], (32, 3, 3)).copy()
            c2w_all = z["c2w"]
            valid_all = z["valid"].astype(bool)

        finite_pose = np.isfinite(c2w_all).all(axis=(1, 2)) & np.isfinite(K_all).all(axis=(1, 2))
        sel = self._select_indices_deterministic(rec.canonical, valid_all & finite_pose)

        depth_sel = depth_all[sel]
        K_sel = K_all[sel]
        c2w_sel = c2w_all[sel].astype(np.float64)
        vm_sel = (valid_all & finite_pose)[sel]
        src_h, src_w = depth_sel.shape[1], depth_sel.shape[2]

        R_c2w = c2w_sel[:, :3, :3]
        t_c2w = c2w_sel[:, :3, 3]
        R_w2c = np.swapaxes(R_c2w, -1, -2)
        t_w2c = -np.einsum("nij,nj->ni", R_w2c, t_c2w)

        z_world = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        grav_cam = np.einsum("nij,j->ni", R_w2c, z_world)
        grav_cam = grav_cam / np.linalg.norm(grav_cam, axis=-1, keepdims=True).clip(min=1e-7)

        rot_t = torch.from_numpy(R_w2c.astype(np.float32)).unsqueeze(0)
        trans_t = torch.from_numpy(t_w2c.astype(np.float32)).unsqueeze(0)
        grav_t = torch.from_numpy(grav_cam.astype(np.float32)).unsqueeze(0)
        rot_canon, trans_canon = compute_gravity_leveled_poses(rot_t, trans_t, grav_t[:, 0])
        rot_gt = rot_canon.squeeze(0)
        trans_gt = trans_canon.squeeze(0)
        gravity_gt = grav_t.squeeze(0)

        fx_w = np.clip(np.abs(K_sel[:, 0, 0]) / float(src_w), 0.1, 10.0)
        fy_h = np.clip(np.abs(K_sel[:, 1, 1]) / float(src_h), 0.1, 10.0)
        log_fx_w_gt = torch.from_numpy(np.log(fx_w).astype(np.float32))
        log_fy_h_gt = torch.from_numpy(np.log(fy_h).astype(np.float32))

        depth_fine, depth_valid = _masked_downsample_depth(depth_sel, self.grid_h, self.grid_w)
        depth_gt = torch.from_numpy(depth_fine)
        depth_valid_t = torch.from_numpy(depth_valid) & torch.from_numpy(vm_sel)[:, None, None]

        K_fine = torch.from_numpy(_scale_intrinsics(K_sel, src_h, src_w, self.grid_h, self.grid_w))
        K_merged = torch.from_numpy(_scale_intrinsics(K_sel, src_h, src_w, self.hm, self.wm))

        plucker_gt = compute_plucker_rays(K_merged, rot_gt, trans_gt, self.hm, self.wm)
        pmap_gt = unproject_depth(depth_gt, K_fine, rot_gt, trans_gt)
        pmap_gt = torch.where(depth_valid_t.unsqueeze(-1), pmap_gt, torch.zeros_like(pmap_gt))

        frame_paths = [rec.anchor_frame_paths[int(i)] for i in sel]
        timestamps = torch.tensor([rec.anchor_timestamps[int(i)] for i in sel], dtype=torch.float32)

        trace = self._build_trace_for_capture(rec, idx, depth_gt, depth_valid_t, trans_gt)
        n_horiz = len(self.flow_horizons)

        return {
            "rgb_qwen": _load_rgb_tensor(frame_paths, self.grid_h * 16, self.grid_w * 16, QWEN_MEAN, QWEN_STD),
            "rgb_da3": _load_rgb_tensor(frame_paths, self.grid_h * 14, self.grid_w * 14, IMAGENET_MEAN, IMAGENET_STD),
            "input_ids": trace.input_ids,
            "attention_mask": trace.attention_mask,
            "labels": trace.labels,
            "depth_gt": depth_gt,
            "depth_valid": depth_valid_t,
            "rot_gt": rot_gt,
            "trans_gt": trans_gt,
            "gravity_gt": gravity_gt,
            "log_fx_w_gt": log_fx_w_gt,
            "log_fy_h_gt": log_fy_h_gt,
            "K_fine": K_fine,
            "K_merged": K_merged,
            "plucker_gt": plucker_gt,
            "pmap_gt": pmap_gt,
            "metric_scale_locked": torch.tensor(1.0, dtype=torch.float32),
            "has_4d_teacher": torch.tensor(False, dtype=torch.bool),
            "y_stat_gt": torch.ones((self.num_views, self.grid_h, self.grid_w), dtype=torch.float32),
            "delta_p_gt": torch.zeros((self.num_views, self.grid_h, self.grid_w, n_horiz, 3), dtype=torch.float32),
            "flow_valid": torch.zeros((self.num_views, self.grid_h, self.grid_w, n_horiz), dtype=torch.bool),
            "view_mask": torch.from_numpy(vm_sel.astype(bool)),
            "timestamps": timestamps,
            "capture_id": rec.canonical,
            "room_id": rec.room,
            "dataset": rec.dataset,
        }


def collate_stage2_batch(items: Sequence[Dict[str, object]]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for k in items[0].keys():
        v0 = items[0][k]
        if torch.is_tensor(v0):
            out[k] = torch.stack([it[k] for it in items], dim=0)
        else:
            out[k] = [it[k] for it in items]
    return out


def build_synthetic_stage2_batch(
    batch_size: int = 1,
    num_views: int = 8,
    grid_h: int = 20,
    grid_w: int = 20,
    seq_len: int = 128,
    vocab_size: int = 248320,
    teacher_dim: int = 3072,
    flow_horizons: Tuple[int, ...] = (-1, 1, 4, 16),
    has_4d_teacher: bool = True,
    include_vla: bool = False,
    device: Optional[torch.device] = None,
    dtype: torch.dtype = torch.float32,
    seed: int = 42,
) -> Tuple[Dict[str, torch.Tensor], torch.Tensor]:
    """Build an exact-shape synthetic Stage-2 batch + teacher features (`0 GB` disk footprint)."""
    gen = torch.Generator(device="cpu").manual_seed(seed)
    hm, wm = grid_h // 2, grid_w // 2
    n_horiz = len(flow_horizons)

    rgb_qwen = torch.randn((batch_size, num_views, 3, grid_h * 16, grid_w * 16), generator=gen, dtype=dtype)
    rgb_da3 = torch.randn((batch_size, num_views, 3, grid_h * 14, grid_w * 14), generator=gen, dtype=dtype)

    # Encode a realistic multi-turn E05 trace with assistant-only labels
    trace = encode_e05_epistemic_trace(
        prompt="In meters, compute the shortest unobstructed 3D surface gap between the chair and table.",
        trace_turns=[
            {
                "verify": "Verify wide-baseline parallax >= 15 deg across frames [2, 19].",
                "think": "Intent: locate chair and table in canonical +Z-up coordinates.",
                "call": '<geo>{"op":"locate","q":"chair"} ; {"op":"locate","q":"table"}</geo>',
                "tool_response": '{"batch":[{"q":"chair","status":"OK","slots":[{"id":"s1"}]},{"q":"table","status":"OK","slots":[{"id":"s2"}]}]}',
            },
            {
                "think": "Both slots localized with OK status. Measure surface_gap in meters.",
                "call": '<geo>{"op":"measure","op_type":"surface_gap","a":"s1","b":"s2","unit":"m"}</geo>',
                "tool_response": '{"status":"OK","val_num":1.42,"unit":"m"}',
            },
            {
                "think": "Tool confirmed 1.42 m. Emit final answer.",
                "answer": "1.42",
            },
        ],
        max_seq_len=seq_len,
        vocab_size=vocab_size,
    )
    input_ids = trace.input_ids.unsqueeze(0).expand(batch_size, -1).clone()
    attention_mask = trace.attention_mask.unsqueeze(0).expand(batch_size, -1).clone()
    labels = trace.labels.unsqueeze(0).expand(batch_size, -1).clone()

    depth_gt = torch.empty((batch_size, num_views, grid_h, grid_w), dtype=torch.float32).uniform_(0.8, 4.5, generator=gen)
    depth_valid = torch.ones((batch_size, num_views, grid_h, grid_w), dtype=torch.bool)
    w_rot = torch.randn((batch_size, num_views, 3), generator=gen, dtype=torch.float32) * 0.15
    w_rot[:, 0] = 0.0
    rot_gt = so3_exp(w_rot)
    trans_gt = torch.randn((batch_size, num_views, 3), generator=gen, dtype=torch.float32) * 0.4
    trans_gt[:, 0] = 0.0
    gravity_gt = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float32).view(1, 1, 3).expand(batch_size, num_views, 3).clone()
    rot_gt, trans_gt = compute_gravity_leveled_poses(rot_gt, trans_gt, gravity_gt[:, 0])

    log_fx_w_gt = torch.zeros((batch_size, num_views), dtype=torch.float32)
    log_fy_h_gt = torch.zeros((batch_size, num_views), dtype=torch.float32)
    K_fine = build_intrinsics_matrix(log_fx_w_gt, log_fy_h_gt, width=grid_w, height=grid_h)
    K_merged = build_intrinsics_matrix(log_fx_w_gt, log_fy_h_gt, width=wm, height=hm)
    plucker_gt = compute_plucker_rays(K_merged, rot_gt, trans_gt, hm, wm)
    pmap_gt = unproject_depth(depth_gt, K_fine, rot_gt, trans_gt)

    batch: Dict[str, torch.Tensor] = {
        "rgb_qwen": rgb_qwen,
        "rgb_da3": rgb_da3,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
        "depth_gt": depth_gt,
        "depth_valid": depth_valid,
        "rot_gt": rot_gt,
        "trans_gt": trans_gt,
        "gravity_gt": gravity_gt,
        "log_fx_w_gt": log_fx_w_gt,
        "log_fy_h_gt": log_fy_h_gt,
        "plucker_gt": plucker_gt,
        "pmap_gt": pmap_gt,
        "metric_scale_locked": torch.ones((batch_size,), dtype=torch.float32),
        "has_4d_teacher": torch.full((batch_size,), bool(has_4d_teacher), dtype=torch.bool),
        "y_stat_gt": (torch.rand((batch_size, num_views, grid_h, grid_w), generator=gen) > 0.2).float(),
        "delta_p_gt": torch.randn((batch_size, num_views, grid_h, grid_w, n_horiz, 3), generator=gen) * 0.05,
        "flow_valid": torch.ones((batch_size, num_views, grid_h, grid_w, n_horiz), dtype=torch.bool),
        "view_mask": torch.ones((batch_size, num_views), dtype=torch.bool),
        "timestamps": torch.linspace(0.0, 1.0, num_views).unsqueeze(0).expand(batch_size, -1).clone(),
    }
    if include_vla:
        batch["actions_gt"] = torch.randn((batch_size, 8, 7), generator=gen, dtype=dtype)
        batch["proprio"] = torch.randn((batch_size, 8), generator=gen, dtype=dtype)

    teacher_feats = torch.randn((batch_size, num_views, hm * wm, teacher_dim), generator=gen, dtype=dtype)

    if device is not None:
        batch = {k: v.to(device, non_blocking=True) for k, v in batch.items()}
        teacher_feats = teacher_feats.to(device, non_blocking=True)
    return batch, teacher_feats
