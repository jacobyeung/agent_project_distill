"""Run vla_where P-1..P-5 LIBERO replays (step-544 + SAM 3 + G3T) and paired G3T vs DA3 diagnostic."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
import time
import types
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from vla_where import build, geometry as G, geometry_viewset as GV, precheck, renders, scale as S
from vla_where.backends.gt import GTGeometry, GTPointer, GTPresence, GTProposals, GTStore
from vla_where.provider import Config, WhereProvider

TREE = Path("/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872")
GV.DEFAULT_TREE = TREE
GV.ViewSetG3T.__init__.__kwdefaults__["tree"] = TREE
GV.ViewSetG3T.load_pinned.__func__.__kwdefaults__["tree"] = TREE

WORK = Path("/scratch/jjyeung/orch_home_distill/work_vla_where_cache")
RENDERS_DIR = WORK / "renders"
OUT_DIR = WORK / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

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
T11_PATH = Path("/scratch/jjyeung/orch_home_distill/work_vla_prechecks/out/t11_parity_gpu6_bf16.json")

DA3_SRC = Path("/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src")
DA3_SITE = Path("/scratch/jjyeung/geo_bakeoff_kit/runtime/site")
DA3_WEIGHTS = Path("/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors")


def _img_key(image: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(image))
    return hashlib.sha1(arr.tobytes()).hexdigest()


def add_memo_to_provider(prov: WhereProvider):
    """Memoize presence.p_yes, pointer.point, and proposals.propose by image bytes + text."""
    orig_p_yes = prov.presence.p_yes
    orig_point = prov.pointer.point
    orig_propose = prov.proposals.propose
    p_yes_cache = {}
    point_cache = {}
    prop_cache = {}
    timings = dict(p_yes_calls=0, p_yes_s=0.0, point_calls=0, point_s=0.0, sam3_calls=0, sam3_s=0.0)

    def cached_p_yes(image, phrase, view=None):
        k = (_img_key(image), phrase)
        if k not in p_yes_cache:
            t0 = time.perf_counter()
            p_yes_cache[k] = orig_p_yes(image, phrase, view=view)
            timings["p_yes_calls"] += 1
            timings["p_yes_s"] += time.perf_counter() - t0
        return p_yes_cache[k]

    def cached_point(image, phrase, view=None):
        k = (_img_key(image), phrase)
        if k not in point_cache:
            t0 = time.perf_counter()
            point_cache[k] = orig_point(image, phrase, view=view)
            timings["point_calls"] += 1
            timings["point_s"] += time.perf_counter() - t0
        return point_cache[k]

    def cached_propose(images, noun, views=None):
        k = (tuple(_img_key(img) for img in images), noun)
        if k not in prop_cache:
            t0 = time.perf_counter()
            prop_cache[k] = orig_propose(images, noun, views=views)
            timings["sam3_calls"] += 1
            timings["sam3_s"] += time.perf_counter() - t0
        return prop_cache[k]

    prov.presence.p_yes = cached_p_yes
    prov.pointer.point = cached_point
    prov.proposals.propose = cached_propose
    return timings


class ViewSetDA3:
    """ViewSet adapter wrapping DA3-Nested Giant-Large with identical ViewSetResult contract."""

    def __init__(self, model, *, mirror_x: bool = True, process_res: int = 504):
        self.model = model
        self.mirror_x = bool(mirror_x)
        self.process_res = int(process_res)

    def pin(self):
        return dict(model="da3nested-giant-large", weights= str(DA3_WEIGHTS), process_res=self.process_res)

    def sha(self):
        return hashlib.sha256(f"viewset_da3|{self.process_res}|mirror_x={self.mirror_x}".encode()).hexdigest()

    @torch.inference_mode()
    def run(self, images, views=None):
        pil_imgs = [Image.fromarray(np.asarray(im, dtype=np.uint8)) for im in images]
        pred = self.model.inference(pil_imgs, process_res=self.process_res)
        ext = np.asarray(pred.extrinsics, dtype=np.float64)
        S_n = len(images)
        w2c = np.broadcast_to(np.eye(4, dtype=np.float64), (S_n, 4, 4)).copy()
        w2c[:, :3, :4] = ext[:, :3, :4]
        T0 = np.stack([w2c[0] @ np.linalg.inv(w2c[k]) for k in range(S_n)])

        raw_depth = np.asarray(pred.depth, dtype=np.float32)  # [S, Hd, Wd]
        raw_conf = (
            np.asarray(pred.conf, dtype=np.float32)
            if getattr(pred, "conf", None) is not None
            else np.ones_like(raw_depth, dtype=np.float32)
        )
        raw_K = np.asarray(pred.intrinsics, dtype=np.float64)  # [S, 3, 3] at (Hd, Wd)
        Hd, Wd = raw_depth.shape[1:3]

        K_list, fov_list, depths, confs = [], [], [], []
        for k in range(S_n):
            h, w = np.asarray(images[k]).shape[:2]
            dt = torch.from_numpy(raw_depth[k:k+1, None])
            ct = torch.from_numpy(raw_conf[k:k+1, None])
            d_hw = torch.nn.functional.interpolate(dt, size=(h, w), mode="bilinear", align_corners=False)[0, 0].numpy().astype(np.float64)
            c_hw = torch.nn.functional.interpolate(ct, size=(h, w), mode="bilinear", align_corners=False)[0, 0].numpy().astype(np.float64)
            depths.append(d_hw)
            confs.append(c_hw)
            sx, sy = w / float(Wd), h / float(Hd)
            Kk = np.array([
                [raw_K[k, 0, 0] * sx, 0.0, raw_K[k, 0, 2] * sx],
                [0.0, raw_K[k, 1, 1] * sy, raw_K[k, 1, 2] * sy],
                [0.0, 0.0, 1.0],
            ], dtype=np.float64)
            K_list.append(Kk)
            fov_list.append([2 * np.arctan(h / (2 * Kk[1, 1])), 2 * np.arctan(w / (2 * Kk[0, 0]))])
        up = np.stack([w2c[k][:3, :3] @ np.array([0.0, -1.0, 0.0]) for k in range(S_n)])
        return GV.ViewSetResult(
            list(views) if views is not None else [(None, k) for k in range(S_n)],
            T0,
            np.array(fov_list, dtype=np.float64),
            np.stack(K_list),
            depths,
            confs,
            up=up,
            mirror=self.mirror_x,
            extra=dict(w2c=w2c),
        )


def load_da3(device="cuda"):
    if "depth_anything_3.utils.export" not in sys.modules:
        sys.modules["depth_anything_3.utils.export"] = types.SimpleNamespace(export=None)
    for p in (str(DA3_SRC), str(DA3_SITE)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import safetensors.torch as st
    from depth_anything_3.api import DepthAnything3
    model = DepthAnything3(model_name="da3nested-giant-large")
    state = st.load_file(str(DA3_WEIGHTS), device="cpu")
    model.load_state_dict(state, strict=False)
    return model.to(device).eval()


def geodesic_rot_deg(R1: np.ndarray, R2: np.ndarray) -> float:
    d = np.linalg.norm(R1 - R2, ord="fro") / (2.0 * math.sqrt(2.0))
    return float(math.degrees(2.0 * math.asin(min(1.0, max(0.0, d)))))


def trans_dir_deg(t1: np.ndarray, t2: np.ndarray) -> float | None:
    n1, n2 = float(np.linalg.norm(t1)), float(np.linalg.norm(t2))
    if n1 < 1e-6 or n2 < 1e-6:
        return None
    c = float(np.clip(np.dot(t1 / n1, t2 / n2), -1.0, 1.0))
    return float(math.degrees(math.acos(c)))


def si_abs_rel(d_pred: np.ndarray, d_gt: np.ndarray, mask: np.ndarray) -> dict:
    ok = mask & np.isfinite(d_pred) & np.isfinite(d_gt) & (d_pred > 1e-4) & (d_gt > 0.05) & (d_gt < 3.0)
    if ok.sum() < 10:
        return dict(n=int(ok.sum()), si_abs_rel=None, d1=None, scale_gt=None)
    p = d_pred[ok]
    g = d_gt[ok]
    s = float(np.median(g / p))
    ps = p * s
    abs_rel = float(np.mean(np.abs(ps - g) / g))
    ratio = np.maximum(ps / g, g / ps)
    d1 = float(np.mean(ratio < 1.25))
    return dict(n=int(ok.sum()), si_abs_rel=abs_rel, d1=d1, scale_gt=s)


def evaluate_geometry_diagnostic(geo_runner, raw_eps, he, stride=2, history_offsets=(2, 4, 8)):
    """Detailed LIBERO 5-view depth, relative pose (wrist<-agent, wrist<-history), scale, and GT-perception 3D lift accuracy."""
    M4 = np.diag([-1.0, 1.0, 1.0, 1.0])
    records = []
    for ep, st, eid in raw_eps:
        for t in range(0, len(ep), stride):
            obs = ep.observation(t, history_offsets)
            # Build view list as WhereProvider.where does
            views = [("wrist", t), ("agent", t)]
            images = [obs.wrist[t], obs.agent]
            for dt in history_offsets:
                step = t - dt
                if step in obs.wrist and step != t:
                    views.append(("wrist", step))
                    images.append(obs.wrist[step])
            res = geo_runner.run(images, views)

            # 1. Depth accuracy on wrist_t and agent_t (full valid & target/place masks)
            w_gt_d = np.asarray(st.view(("wrist", t))["depth"], dtype=np.float64)
            a_gt_d = np.asarray(st.view(("agent", t))["depth"], dtype=np.float64)
            w_full = si_abs_rel(res.depth[0], w_gt_d, np.ones_like(w_gt_d, dtype=bool))
            a_full = si_abs_rel(res.depth[1], a_gt_d, np.ones_like(a_gt_d, dtype=bool))

            # Target & place masks
            obj_depths = []
            for phrase, obj_name in st.names.items():
                for v_idx, v_name, gt_d in ((0, "wrist", w_gt_d), (1, "agent", a_gt_d)):
                    m = st.view((v_name, t))["seg"].get(obj_name)
                    if m is not None and m.sum() >= 20:
                        od = si_abs_rel(res.depth[v_idx], gt_d, m)
                        if od["si_abs_rel"] is not None:
                            obj_depths.append(od["si_abs_rel"])

            # 2. Relative pose accuracy: T_wrist_t <- agent_t
            T_b_w0 = st.view(("wrist", t))["T_base_cam"]
            T_b_a0 = st.view(("agent", t))["T_base_cam"]
            T_w0_a0_gt = np.linalg.inv(T_b_w0) @ T_b_a0
            # Un-mirror predicted T0[1] if mirror=True
            T_w0_a0_pred = (M4 @ res.T0[1] @ M4) if res.mirror else res.T0[1]
            rot_err_wa = geodesic_rot_deg(T_w0_a0_pred[:3, :3], T_w0_a0_gt[:3, :3])
            tdir_err_wa = trans_dir_deg(T_w0_a0_pred[:3, 3], T_w0_a0_gt[:3, 3])

            # Cross-view scale Anchor from FK wrist-agent baseline
            fk_wa_dist = float(np.linalg.norm(T_w0_a0_gt[:3, 3]))
            pred_wa_dist = float(np.linalg.norm(T_w0_a0_pred[:3, 3]))
            s_fk_wa = (fk_wa_dist / pred_wa_dist) if pred_wa_dist > 1e-4 else None

            # 3. Relative pose accuracy on wrist history views
            hist_rot_errs = []
            for k in range(2, len(views)):
                _, h_step = views[k]
                T_b_wk = st.view(("wrist", h_step))["T_base_cam"]
                T_w0_wk_gt = np.linalg.inv(T_b_w0) @ T_b_wk
                T_w0_wk_pred = (M4 @ res.T0[k] @ M4) if res.mirror else res.T0[k]
                hist_rot_errs.append(geodesic_rot_deg(T_w0_wk_pred[:3, :3], T_w0_wk_gt[:3, :3]))

            # 4. Proprio-handeye scale vs s_GT
            hist = {k: obs.proprio[k] for r, k in views[2:]}
            centres = {k: res.centre(i) for i, (r, k) in enumerate(views) if i >= 2}
            s_prop, s_meta = S.proprio_handeye(obs.proprio[t], hist, centres, he)
            s_gt = w_full["scale_gt"]
            s_ag_gt = a_full["scale_gt"]
            cross_view_scale_ratio = (s_ag_gt / s_gt) if (s_gt and s_ag_gt) else None

            records.append(dict(
                episode=eid,
                t=t,
                wrist_si_abs_rel=w_full["si_abs_rel"],
                wrist_d1=w_full["d1"],
                agent_si_abs_rel=a_full["si_abs_rel"],
                agent_d1=a_full["d1"],
                obj_si_abs_rel=float(np.mean(obj_depths)) if obj_depths else None,
                rot_err_wrist_agent_deg=rot_err_wa,
                tdir_err_wrist_agent_deg=tdir_err_wa,
                rot_err_wrist_hist_med_deg=float(np.median(hist_rot_errs)) if hist_rot_errs else None,
                s_gt=s_gt,
                s_agent_gt=s_ag_gt,
                cross_view_scale_ratio=cross_view_scale_ratio,
                s_prop=s_prop,
                s_prop_ratio=(s_prop / s_gt) if (s_prop is not None and s_gt) else None,
                s_fk_wa=s_fk_wa,
                s_fk_wa_ratio=(s_fk_wa / s_gt) if (s_fk_wa is not None and s_gt) else None,
            ))

    def _med(key):
        vals = [r[key] for r in records if r[key] is not None and np.isfinite(r[key])]
        return float(np.median(vals)) if vals else None

    def _mean(key):
        vals = [r[key] for r in records if r[key] is not None and np.isfinite(r[key])]
        return float(np.mean(vals)) if vals else None

    prop_ratios = [r["s_prop_ratio"] for r in records if r["s_prop_ratio"] is not None]
    fk_ratios = [r["s_fk_wa_ratio"] for r in records if r["s_fk_wa_ratio"] is not None]
    late = [r for r in records if r["t"] >= 2]
    summary = dict(
        n_frames=len(records),
        wrist_si_abs_rel_median=_med("wrist_si_abs_rel"),
        wrist_d1_mean=_mean("wrist_d1"),
        agent_si_abs_rel_median=_med("agent_si_abs_rel"),
        agent_d1_mean=_mean("agent_d1"),
        obj_si_abs_rel_median=_med("obj_si_abs_rel"),
        rot_err_wrist_agent_med_deg=_med("rot_err_wrist_agent_deg"),
        tdir_err_wrist_agent_med_deg=_med("tdir_err_wrist_agent_deg"),
        rot_err_wrist_hist_med_deg=_med("rot_err_wrist_hist_med_deg"),
        cross_view_scale_ratio_med=_med("cross_view_scale_ratio"),
        s_prop_ratio_med=_med("s_prop_ratio"),
        s_prop_in_band_08_125=float(np.mean([0.8 <= x <= 1.25 for x in prop_ratios])) if prop_ratios else None,
        s_prop_coverage_t_ge_2=float(np.mean([r["s_prop"] is not None for r in late])) if late else None,
        s_fk_wa_ratio_med=_med("s_fk_wa_ratio"),
        s_fk_wa_in_band_08_125=float(np.mean([0.8 <= x <= 1.25 for x in fk_ratios])) if fk_ratios else None,
    )
    return summary, records


def main():
    t_start = time.perf_counter()
    t11 = json.loads(T11_PATH.read_text())
    he = S.HandEye.load(HAND_EYE_PATH, HAND_EYE_SHA)
    raw_eps = list(renders.episodes(RENDERS_DIR))
    print(f"Loaded {len(raw_eps)} LIBERO render episodes ({sum(len(e) for e, _, _ in raw_eps)} frames)")

    # 1. Build real step-544 student provider
    cfg = Config(g3t_mirror_x=True)
    params = dict(
        full_weights=str(FULL_WEIGHTS),
        g3t_weights=str(G3T_W),
        g3t_config=str(G3T_C),
        sam3=SAM3_CFG,
        hand_eye=str(HAND_EYE_PATH),
        hand_eye_sha256=HAND_EYE_SHA,
        device="cuda",
    )
    t_load0 = time.perf_counter()
    prov = build.build_provider("student", params=params, config=cfg)
    load_s = time.perf_counter() - t_load0
    print(f"Loaded WhereProvider('student') in {load_s:.2f}s; provider_sha={prov.sha()}")
    print("Pins:", json.dumps(prov.pins(), sort_keys=True))
    timings = add_memo_to_provider(prov)

    shared = GTStore()
    def make_gen():
        for ep, st, eid in raw_eps:
            shared.bind(st.frames, st.names, st.nouns, st.episode)
            yield ep, shared, eid

    ref = build.build_provider("reference", config=cfg, hand_eye=he, store=shared)

    # 2. Presence pass & tau refit at stride=8 and stride=2
    scores_s8, labels_s8 = precheck.presence_pass(prov, make_gen(), stride=8)
    tau_refit_s8 = precheck.refit_tau(scores_s8, labels_s8)
    auroc_all_s8 = precheck.auroc(scores_s8, labels_s8)

    scores_s2, labels_s2 = precheck.presence_pass(prov, make_gen(), stride=2)
    tau_refit_s2 = precheck.refit_tau(scores_s2, labels_s2)
    auroc_all_s2 = precheck.auroc(scores_s2, labels_s2)
    print(f"Presence pass: stride=8 n={len(scores_s8)} auroc_both={auroc_all_s8:.4f} tau_refit={tau_refit_s8}; "
          f"stride=2 n={len(scores_s2)} auroc_both={auroc_all_s2:.4f} tau_refit={tau_refit_s2}")

    # 3. Evaluate P-1..P-5 across configurations
    results = {}

    for label, stride, tau, h_off in [
        ("g3t_stride8_tau050_hoff8", 8, 0.5, (8, 16, 32)),
        ("g3t_stride8_taurefit_hoff8", 8, tau_refit_s8 if tau_refit_s8 is not None else 0.5, (8, 16, 32)),
        ("g3t_stride2_tau050_hoff8", 2, 0.5, (8, 16, 32)),
        ("g3t_stride2_taurefit_hoff8", 2, tau_refit_s2 if tau_refit_s2 is not None else 0.5, (8, 16, 32)),
        ("g3t_stride2_taurefit_hoff2", 2, tau_refit_s2 if tau_refit_s2 is not None else 0.5, (2, 4, 8)),
    ]:
        prov.cfg = Config(tau=float(tau), history_offsets=h_off, g3t_mirror_x=True)
        ref.cfg = Config(tau=float(tau), history_offsets=h_off, g3t_mirror_x=True)
        rows, summary = precheck.evaluate(prov, ref, make_gen(), stride=stride, t11=t11)
        rep = precheck.report(summary, label=label, tau=float(tau))
        print("\n" + rep)
        precheck.dump(OUT_DIR / f"precheck_{label}.jsonl", rows, summary)
        results[label] = dict(tau=float(tau), stride=stride, history_offsets=list(h_off), summary=summary)

    # Also test GT perception + real G3T geometry (isolating geometry contribution to P-2 and P-4)
    gt_perc_g3t = WhereProvider(
        GTPresence(shared), GTPointer(shared), GTProposals(shared), prov.geometry, he,
        Config(tau=0.5, history_offsets=(2, 4, 8), g3t_mirror_x=True)
    )
    ref.cfg = Config(tau=0.5, history_offsets=(2, 4, 8), g3t_mirror_x=True)
    rows_gtg3t, sum_gtg3t = precheck.evaluate(gt_perc_g3t, ref, make_gen(), stride=2, t11=t11)
    print("\n" + precheck.report(sum_gtg3t, label="gt_perception_plus_real_g3t_stride2_hoff2", tau=0.5))
    results["gt_perception_plus_real_g3t_stride2_hoff2"] = dict(summary=sum_gtg3t)

    # 4. Run detailed G3T geometry diagnostic on LIBERO renders
    g3t_diag_sum, g3t_diag_recs = evaluate_geometry_diagnostic(prov.geometry, raw_eps, he, stride=2, history_offsets=(2, 4, 8))
    print("\nG3T Geometry Diagnostic Summary:", json.dumps(g3t_diag_sum, indent=2, sort_keys=True))

    # 4b. Detailed Perception Breakdown (SAM 3 proposals vs student point vs erosion/min_pixels)
    perc_rows = []
    for ep, st, eid in raw_eps:
        step_info = prov.table.step(ep.instruction)
        for t in range(0, len(ep), 2):
            found_t = prov.proposals.propose([ep.wrist[t], ep.agent[t]], step_info.target.noun)
            for v_idx, v_name, img in ((0, "wrist", ep.wrist[t]), (1, "agent", ep.agent[t])):
                gt_m = st.mask((v_name, t), step_info.target.phrase)
                gt_px = int(gt_m.sum()) if gt_m is not None else 0
                props = found_t[v_idx]
                ious = [precheck.iou(p.mask, gt_m) for p in props] if gt_m is not None else []
                max_sam_iou = max(ious) if ious else 0.0
                top1_sam_iou = ious[0] if ious else 0.0
                pt = prov.pointer.point(img, step_info.target.phrase, (v_name, t))
                p_yes = prov.presence.p_yes(img, step_info.target.phrase, (v_name, t))
                pt_in_gt = False
                pt_in_sam = False
                hit_sam_iou = 0.0
                hit_eroded_px = 0
                if pt is not None:
                    uv = ((min(pt[0], 999) + 0.5) / 1000.0, (min(pt[1], 999) + 0.5) / 1000.0)
                    if gt_m is not None:
                        pt_in_gt = bool(G.mask_contains(gt_m, uv))
                    hits = [p for p in props if G.mask_contains(p.mask, uv)]
                    if hits:
                        pt_in_sam = True
                        best = max(hits, key=lambda p: p.score)
                        hit_sam_iou = precheck.iou(best.mask, gt_m)
                        hit_eroded_px = int(G.erode(best.mask, 2).sum())
                perc_rows.append(dict(
                    episode=eid, t=t, view=v_name, gt_px=gt_px,
                    n_sam_props=len(props), max_sam_iou=max_sam_iou, top1_sam_iou=top1_sam_iou,
                    p_yes=p_yes, point=pt, pt_in_gt=pt_in_gt, pt_in_sam=pt_in_sam,
                    hit_sam_iou=hit_sam_iou, hit_eroded_px=hit_eroded_px,
                ))
    vis_agent = [r for r in perc_rows if r["view"] == "agent" and r["gt_px"] >= 20]
    vis_wrist = [r for r in perc_rows if r["view"] == "wrist" and r["gt_px"] >= 20]
    abs_wrist = [r for r in perc_rows if r["view"] == "wrist" and r["gt_px"] < 20]
    perc_summary = dict(
        agent_vis_n=len(vis_agent),
        agent_gt_px_median=float(np.median([r["gt_px"] for r in vis_agent])) if vis_agent else None,
        agent_sam_oracle_iou05_rate=float(np.mean([r["max_sam_iou"] >= 0.5 for r in vis_agent])) if vis_agent else None,
        agent_sam_top1_iou05_rate=float(np.mean([r["top1_sam_iou"] >= 0.5 for r in vis_agent])) if vis_agent else None,
        agent_point_nonnull_rate=float(np.mean([r["point"] is not None for r in vis_agent])) if vis_agent else None,
        agent_point_in_gt_rate=float(np.mean([r["pt_in_gt"] for r in vis_agent])) if vis_agent else None,
        agent_point_in_sam_rate=float(np.mean([r["pt_in_sam"] for r in vis_agent])) if vis_agent else None,
        agent_hit_sam_iou05_rate=float(np.mean([r["hit_sam_iou"] >= 0.5 for r in vis_agent])) if vis_agent else None,
        agent_hit_eroded_ge20_rate=float(np.mean([r["hit_eroded_px"] >= 20 for r in vis_agent])) if vis_agent else None,
        wrist_vis_n=len(vis_wrist),
        wrist_abs_n=len(abs_wrist),
        wrist_sam_oracle_iou05_rate=float(np.mean([r["max_sam_iou"] >= 0.5 for r in vis_wrist])) if vis_wrist else None,
        wrist_point_in_gt_rate=float(np.mean([r["pt_in_gt"] for r in vis_wrist])) if vis_wrist else None,
        sample_points_agent=[dict(ep=r["episode"], t=r["t"], pt=r["point"], gt_px=r["gt_px"], max_sam_iou=r["max_sam_iou"], hit_sam_iou=r["hit_sam_iou"], hit_eroded_px=r["hit_eroded_px"]) for r in vis_agent[:8]],
        sample_raw_traces=prov.pointer.trace[:10],
    )
    print("\nPerception Breakdown Summary:", json.dumps(perc_summary, indent=2, sort_keys=True))

    # 5. Free student LLM weights to load DA3-Nested Giant-Large cleanly while keeping memoized student/SAM3 cache!
    g3t_geom = prov.geometry
    torch.cuda.empty_cache()

    t_da3 = time.perf_counter()
    da3_model = load_da3("cuda")
    da3_geom = ViewSetDA3(da3_model, mirror_x=True, process_res=504)
    print(f"Loaded DA3-Nested Giant-Large in {time.perf_counter() - t_da3:.2f}s")

    # Evaluate P-1..P-4 with student+SAM3+DA3 and GT-perception+DA3
    prov.geometry = da3_geom
    for label, stride, tau, h_off in [
        ("da3_stride8_taurefit_hoff8", 8, tau_refit_s8 if tau_refit_s8 is not None else 0.5, (8, 16, 32)),
        ("da3_stride2_taurefit_hoff2", 2, tau_refit_s2 if tau_refit_s2 is not None else 0.5, (2, 4, 8)),
    ]:
        prov.cfg = Config(tau=float(tau), history_offsets=h_off, g3t_mirror_x=True)
        ref.cfg = Config(tau=float(tau), history_offsets=h_off, g3t_mirror_x=True)
        rows, summary = precheck.evaluate(prov, ref, make_gen(), stride=stride, t11=t11)
        rep = precheck.report(summary, label=label, tau=float(tau))
        print("\n" + rep)
        precheck.dump(OUT_DIR / f"precheck_{label}.jsonl", rows, summary)
        results[label] = dict(tau=float(tau), stride=stride, history_offsets=list(h_off), summary=summary)

    gt_perc_da3 = WhereProvider(
        GTPresence(shared), GTPointer(shared), GTProposals(shared), da3_geom, he,
        Config(tau=0.5, history_offsets=(2, 4, 8), g3t_mirror_x=True)
    )
    ref.cfg = Config(tau=0.5, history_offsets=(2, 4, 8), g3t_mirror_x=True)
    rows_gtda3, sum_gtda3 = precheck.evaluate(gt_perc_da3, ref, make_gen(), stride=2, t11=t11)
    print("\n" + precheck.report(sum_gtda3, label="gt_perception_plus_real_da3_stride2_hoff2", tau=0.5))
    results["gt_perception_plus_real_da3_stride2_hoff2"] = dict(summary=sum_gtda3)

    da3_diag_sum, da3_diag_recs = evaluate_geometry_diagnostic(da3_geom, raw_eps, he, stride=2, history_offsets=(2, 4, 8))
    print("\nDA3 Geometry Diagnostic Summary:", json.dumps(da3_diag_sum, indent=2, sort_keys=True))

    out_payload = dict(
        wall_s=time.perf_counter() - t_start,
        timings=timings,
        tau_refit_s8=tau_refit_s8,
        tau_refit_s2=tau_refit_s2,
        auroc_both_views_s8=auroc_all_s8,
        auroc_both_views_s2=auroc_all_s2,
        prechecks=results,
        perception_breakdown=perc_summary,
        geometry_diagnostic=dict(
            g3t=g3t_diag_sum,
            da3=da3_diag_sum,
        ),
    )
    (OUT_DIR / "p1_p4_and_da3_diag.json").write_text(json.dumps(out_payload, indent=2, sort_keys=True) + "\n")
    print("\nSAVED:", OUT_DIR / "p1_p4_and_da3_diag.json")


if __name__ == "__main__":
    main()
