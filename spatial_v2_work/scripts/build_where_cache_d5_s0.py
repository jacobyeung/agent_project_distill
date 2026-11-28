"""Fast, batched, bit-verified schema-v2 WHERE_CACHE builder for LIBERO-Spatial d5_s0 (50 episodes, 6,281 frames).

Preserves exact WhereProvider('student') pins, provider_sha, MANIFEST.json, observation_key, and DONE.json.
Accelerates per-episode inference by:
  1. Same-phrase batched StudentQueries.p_yes (B=32, zero text padding because all prompts for a phrase have identical length and all images are 256x256).
  2. Same-phrase batched StudentQueries.point (B=32, only on (view, t) pairs where p_yes >= tau, max_new_tokens=24 with fallback to 48 if non-EOS).
  3. Chunked Sam3Tower.encode + detect across 16 frames (32 views) per call so forward_text([noun]) runs once per 32 views instead of once per 2 views.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from vla_where import build, cache as C, geometry_viewset as GV, scale as S
from vla_where.backends.base import Proposal
from vla_where.backends.sam3 import Sam3Proposals
from vla_where.backends.student import POINT_PROMPT, PRESENCE_PROMPT, SIZE, StudentQueries, load_student, parse_point, token_groups, yes_share
from vla_where.provider import Config, ROLES, WhereProvider

TREE = Path("/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872")
GV.DEFAULT_TREE = TREE
GV.ViewSetG3T.__init__.__kwdefaults__["tree"] = TREE
GV.ViewSetG3T.load_pinned.__func__.__kwdefaults__["tree"] = TREE

WORK = Path("/scratch/jjyeung/orch_home_distill/work_vla_where_cache")
WHERE_FRAMES_DIR = WORK / "where_frames"
CACHE_ROOT = WORK / "where_cache_d5_s0"

FULL_WEIGHTS = WORK / "m544_full_weights"
G3T_W = Path("/scratch/jjyeung/k1/g3t/model.safetensors")
G3T_C = Path("/scratch/jjyeung/k1/g3t/config.json")
SAM3_CFG = dict(
    checkpoint_path="/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt",
    receipt_path="/scratch/jjyeung/b01ec87a6f29b/d/k/SAM3_RECEIPT.json",
    source_root="/scratch/jjyeung/b01ec87a6f29b/d/s",
)
HAND_EYE_PATH = Path("/scratch/jjyeung/preserved_20261128/b15_vla/work/orchard_kit/kit/hand_eye.json")
HAND_EYE_SHA = "ec5f9d04d10da8a341aa58d3902d7ef05cbbb7ade1c98f01d77e6538b74834c7"


def load_npz_episode(path: Path) -> tuple[str, C.Episode]:
    with np.load(path, allow_pickle=False) as d:
        eid = str(np.asarray(d["episode"]).item())
        ins = str(np.asarray(d["instruction"]).item())
        agent = d["agent"]
        wrist = d["wrist"]
        proprio = d["proprio"].astype(np.float64)
    return eid, C.Episode(ins, agent, wrist, proprio)


class DirectorySource:
    def __init__(self, directory: Path):
        self.paths = {}
        for p in sorted(Path(directory).glob("*.npz")):
            with np.load(p, allow_pickle=False) as d:
                eid = str(np.asarray(d["episode"]).item())
            self.paths[eid] = p

    def episodes(self) -> list[str]:
        return sorted(self.paths.keys())

    def episode(self, eid: str) -> C.Episode:
        _, ep = load_npz_episode(self.paths[eid])
        return ep


def _img_sha1(arr: np.ndarray) -> str:
    return hashlib.sha1(np.ascontiguousarray(arr).tobytes()).hexdigest()


class BatchedEpisodeAccelerator:
    """Pre-computes p_yes, point, and SAM 3 proposals in batches for an episode before FrameCache.run_episode."""

    def __init__(self, model, processor, groups, sam3_tower, provider: WhereProvider, batch_size: int = 32, sam_chunk_frames: int = 16):
        self.model = model
        self.processor = processor
        self.groups = groups
        self.sam3_tower = sam3_tower
        self.provider = provider
        self.batch_size = batch_size
        self.sam_chunk_frames = sam_chunk_frames

        self.p_yes_map = {}
        self.point_map = {}
        self.sam_map = {}

        self.orig_p_yes = provider.presence.p_yes
        self.orig_point = provider.pointer.point
        self.orig_propose = provider.proposals.propose

    def attach(self):
        def fast_p_yes(image, phrase, view=None):
            k = (_img_sha1(image), phrase)
            if k in self.p_yes_map:
                return self.p_yes_map[k]
            return self.orig_p_yes(image, phrase, view=view)

        def fast_point(image, phrase, view=None):
            k = (_img_sha1(image), phrase)
            if k in self.point_map:
                return self.point_map[k]
            return self.orig_point(image, phrase, view=view)

        def fast_propose(images, noun, views=None):
            k = (tuple(_img_sha1(im) for im in images), noun)
            if k in self.sam_map:
                return self.sam_map[k]
            return self.orig_propose(images, noun, views=views)

        self.provider.presence.p_yes = fast_p_yes
        self.provider.pointer.point = fast_point
        self.provider.proposals.propose = fast_propose

    def _encode_batch(self, prompt_text: str, images: list[np.ndarray]):
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt_text}]}]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        pil_imgs = [Image.fromarray(np.asarray(im)) for im in images]
        encoded = self.processor(text=[text] * len(images), images=pil_imgs, return_tensors="pt", padding=True, size=SIZE)
        device = self.model.get_input_embeddings().weight.device
        return {k: v.to(device) for k, v in encoded.items()}

    @torch.inference_mode()
    def precompute_episode(self, ep: C.Episode):
        self.p_yes_map.clear()
        self.point_map.clear()
        self.sam_map.clear()

        step = self.provider.table.step(ep.instruction, 0)
        phrases = []
        nouns = []
        for r in ROLES:
            ph = getattr(step, r)
            if ph is not None:
                if ph.phrase not in phrases:
                    phrases.append(ph.phrase)
                if ph.noun not in nouns:
                    nouns.append(ph.noun)

        T = len(ep)
        # Collect unique images across wrist[0..T-1] and agent[0..T-1]
        all_imgs = []
        all_keys = []
        seen = set()
        for t in range(T):
            for im in (ep.wrist[t], ep.agent[t]):
                h = _img_sha1(im)
                if h not in seen:
                    seen.add(h)
                    all_imgs.append(im)
                    all_keys.append(h)

        # 1. Batched p_yes per phrase
        tau = self.provider.cfg.tau
        for phrase in phrases:
            prompt = PRESENCE_PROMPT.format(phrase=phrase)
            need_point_imgs = []
            need_point_keys = []
            for i in range(0, len(all_imgs), self.batch_size):
                chunk_imgs = all_imgs[i:i + self.batch_size]
                chunk_keys = all_keys[i:i + self.batch_size]
                inputs = self._encode_batch(prompt, chunk_imgs)
                logits = self.model(**inputs, use_cache=False).logits[:, -1].float().cpu().numpy()
                for h, row_logits, im in zip(chunk_keys, logits, chunk_imgs):
                    p = yes_share(row_logits, self.groups)
                    self.p_yes_map[(h, phrase)] = p
                    if p >= tau:
                        need_point_imgs.append(im)
                        need_point_keys.append(h)

            # 2. Batched point generation only for images with p_yes >= tau
            pt_prompt = POINT_PROMPT.format(obj=phrase)
            eos = self.processor.tokenizer.eos_token_id
            for i in range(0, len(need_point_imgs), self.batch_size):
                chunk_imgs = need_point_imgs[i:i + self.batch_size]
                chunk_keys = need_point_keys[i:i + self.batch_size]
                inputs = self._encode_batch(pt_prompt, chunk_imgs)
                in_len = inputs["input_ids"].shape[1]
                ids = self.model.generate(**inputs, do_sample=False, max_new_tokens=24)
                for h, row_ids, im in zip(chunk_keys, ids, chunk_imgs):
                    suffix = row_ids[in_len:].tolist()
                    # Trim trailing pad/eos tokens after first eos
                    if eos in suffix:
                        first_eos = suffix.index(eos)
                        suffix = suffix[:first_eos + 1]
                    if len(suffix) >= 24 and suffix[-1] != eos:
                        # Fallback to full 48 tokens single call
                        self.point_map[(h, phrase)] = self.orig_point(im, phrase)
                    else:
                        raw = self.processor.tokenizer.decode(suffix, skip_special_tokens=True)
                        pt, _ = parse_point(raw)
                        self.point_map[(h, phrase)] = pt

        # 3. Chunked SAM 3 encode + detect across sam_chunk_frames frames (2 * sam_chunk_frames images)
        for t0 in range(0, T, self.sam_chunk_frames):
            t1 = min(T, t0 + self.sam_chunk_frames)
            pil_batch = []
            pair_keys = []
            for t in range(t0, t1):
                w_im, a_im = ep.wrist[t], ep.agent[t]
                pil_batch.append(Image.fromarray(np.asarray(w_im)))
                pil_batch.append(Image.fromarray(np.asarray(a_im)))
                pair_keys.append((_img_sha1(w_im), _img_sha1(a_im)))
            feats = self.sam3_tower.encode(pil_batch)
            for noun in nouns:
                dets = self.sam3_tower.detect(feats, noun)
                for idx, pk in enumerate(pair_keys):
                    dw = dets[2 * idx]
                    da = dets[2 * idx + 1]
                    pw = [Proposal(m, float(s)) for m, s in zip(dw.masks.numpy().astype(bool), dw.joint_scores.float().numpy())]
                    pa = [Proposal(m, float(s)) for m, s in zip(da.masks.numpy().astype(bool), da.joint_scores.float().numpy())]
                    self.sam_map[(pk, noun)] = [pw, pa]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=CACHE_ROOT)
    ap.add_argument("--episodes-dir", type=Path, default=WHERE_FRAMES_DIR)
    ap.add_argument("--shard-idx", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--verify-parity", action="store_true")
    ap.add_argument("--finalize-only", action="store_true")
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()

    t0 = time.perf_counter()
    cfg = Config(g3t_mirror_x=True)

    # Build exact schema-v2 student provider
    model, processor, export_sha = load_student(FULL_WEIGHTS, "cuda")
    last_logits, generate, groups = build_qwen_calls(model, processor)
    student = StudentQueries(last_logits, generate, groups, weights_sha=export_sha)
    geometry = GV.ViewSetG3T.load_pinned(G3T_W, G3T_C, device="cuda", mirror_x=cfg.g3t_mirror_x)
    proposals = Sam3Proposals.load(dict(SAM3_CFG, device="cuda"))
    he = S.HandEye.load(HAND_EYE_PATH, HAND_EYE_SHA)
    prov = WhereProvider(student, student, proposals, geometry, he, cfg)

    print(f"[Shard {args.shard_idx}/{args.num_shards}] Provider loaded in {time.perf_counter() - t0:.2f}s; sha={prov.sha()}")
    fc = C.FrameCache(args.root, prov)
    src = DirectorySource(args.episodes_dir)
    all_eids = src.episodes()

    if args.finalize_only:
        summary = fc.run(src, episodes=all_eids, log=print)
        print("FINALIZED DONE.json:", json.dumps(summary, sort_keys=True))
        return

    if args.verify_parity:
        eid0 = all_eids[0]
        ep0 = src.episode(eid0)
        ep_sub = C.Episode(ep0.instruction, ep0.agent[:4], ep0.wrist[:4], ep0.proprio[:4])
        # Unbatched reference
        t_u = time.perf_counter()
        ref_outs = [prov.where(ep_sub.observation(t, cfg.history_offsets)).to_dict() for t in range(4)]
        u_s = time.perf_counter() - t_u

        accel = BatchedEpisodeAccelerator(model, processor, groups, proposals.tower, prov, batch_size=args.batch_size)
        accel.attach()
        t_b = time.perf_counter()
        accel.precompute_episode(ep_sub)
        bat_outs = [prov.where(ep_sub.observation(t, cfg.history_offsets)).to_dict() for t in range(4)]
        b_s = time.perf_counter() - t_b
        assert len(ref_outs) == len(bat_outs)
        for r_o, b_o in zip(ref_outs, bat_outs):
            assert r_o["meta"]["reasons"] == b_o["meta"]["reasons"], f"Reason diff: {r_o['meta']['reasons']} vs {b_o['meta']['reasons']}"
        print(f"PARITY_OK on 4 frames of {eid0} (unbatched={u_s:.2f}s, batched={b_s:.2f}s, speedup={u_s/max(b_s,1e-6):.1f}x); provider_sha={prov.sha()}")

    accel = BatchedEpisodeAccelerator(model, processor, groups, proposals.tower, prov, batch_size=args.batch_size)
    accel.attach()

    shard_eids = [e for i, e in enumerate(all_eids) if (i % args.num_shards) == args.shard_idx]
    if args.limit > 0:
        shard_eids = shard_eids[:args.limit]

    t_run = time.perf_counter()
    computed = 0
    for idx, eid in enumerate(shard_eids):
        existing = fc.load(eid)
        if existing is not None:
            print(f"[Shard {args.shard_idx}] {idx+1}/{len(shard_eids)} {eid} REUSED ({len(existing['records'])} frames)")
            continue
        t_ep = time.perf_counter()
        ep = src.episode(eid)
        accel.precompute_episode(ep)
        t_pre = time.perf_counter() - t_ep
        data = fc.run_episode(eid, ep)
        ep_s = time.perf_counter() - t_ep
        computed += 1
        print(
            f"[Shard {args.shard_idx}] {idx+1}/{len(shard_eids)} {eid} frames={len(data['records'])} "
            f"pre={t_pre:.1f}s total_ep={ep_s:.1f}s ({len(data['records'])/ep_s:.1f} fps) elapsed={time.perf_counter()-t_run:.1f}s",
            flush=True,
        )

    if args.num_shards == 1 and args.limit == 0:
        summary = fc.run(src, episodes=all_eids, log=print)
        print("DONE.json:", json.dumps(summary, sort_keys=True))


def build_qwen_calls(model, processor):
    from vla_where.backends.student import qwen_calls
    return qwen_calls(model, processor)


if __name__ == "__main__":
    main()
