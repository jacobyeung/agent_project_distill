"""CPU check of the head hook (vl_heads_hook.make) on a tiny random Qwen3.5 and real LIBERO frames.

1. Step-0 parity: StarVLA's QwenOFT with its own L1 head on examples without 'state', and the hooked model (vla_heads head
   (a) with StarVLA's head weights copied in, proprio through the zero-initialised map) on the same examples with 'state',
   give the same loss. This also shows that the hook keeps the state out of the prompt; stock QwenOFT fed the state
   appends it as text and gives a different loss.
2. One backward: the proprio map and the LM receive non-zero gradients.
3. Inference: predict_action returns [B, 8, 7] inside [-1, 1].
4. Server path: a framework rebuilt with VLL_NO_FIT=1 loads the hooked state dict strictly, recovers the proprio
   statistics and predicts the same actions.
5. Eligible chunk starts (drop_incomplete_action_chunks) and the proprio statistics against StarVLA's merged state stats.
usage: hook_check.py CONFIG.yaml TINY_MODEL DATA_ROOT MIX OUT_DIR"""
import copy
import json
import os
import sys

import numpy as np
import torch
from omegaconf import OmegaConf

cfg_path, tiny, root, mix, out = sys.argv[1:6]
os.makedirs(out, exist_ok=True)
cfg = OmegaConf.load(cfg_path)
cfg = OmegaConf.merge(cfg, OmegaConf.create({
    "output_dir": out, "framework": {"qwenvl": {"base_vlm": tiny, "attn_implementation": "sdpa", "vl_hidden_dim": 64}},
    "datasets": {"vla_data": {"data_root_dir": root, "data_mix": mix, "num_workers": 0}}}))
from starVLA.model.framework.share_tools import apply_config_compat  # noqa: E402
cfg = apply_config_compat(cfg)
from starVLA.model.framework.base_framework import build_framework  # noqa: E402
from starVLA.dataloader.lerobot_datasets import get_vla_dataset  # noqa: E402
import vl_data_patch  # noqa: E402,F401  (every frame a chunk start; action_mask past the episode end)
import vl_heads_hook  # noqa: E402

res = {}
torch.manual_seed(0)
m0 = build_framework(cfg).float().eval()
ds = get_vla_dataset(data_cfg=cfg.datasets.vla_data)  # the trainer's call (build_dataloader): default weights
res["eligible_bounds"] = [list(b) for b in getattr(ds, "_valid_step_bounds", [])]
res["drop_incomplete"] = bool(getattr(ds, "drop_incomplete_action_chunks", False))
ex = [ds[i] for i in range(3)]
assert all("state" in e for e in ex), "include_state=true must put 'state' in every example"
res["state_shape"] = list(np.asarray(ex[0]["state"]).shape)
# a chunk that runs past its episode end (searched over the first 4,000 draws): masked tail, last action repeated
tail = next((ds[i] for i in range(4000) if ds[i]["vl_meta"][2] < 8), None)
if tail is not None:
    n = tail["vl_meta"][2]; a = np.asarray(tail["action"])
    res["tail_chunk"] = {"valid": n, "mask_rows": np.asarray(tail["action_mask"]).astype(bool).tolist(),
                         "mask_dtype": str(np.asarray(tail["action_mask"]).dtype), "repeats_last": bool(np.all(a[n:] == a[n - 1])),
                         "episode_id": tail["episode_id"], "t": tail["t"]}
    ex[2] = tail
no_state = [{k: v for k, v in e.items() if k != "state"} for e in ex]
for e in no_state:  # stock QwenOFT on the schema's gripper label g = 1 - 2 a6 and its own [K, 7] mask, for parity
    e["action"] = np.array(e["action"], dtype=np.float32, copy=True); e["action"][:, 6] = 1 - 2 * e["action"][:, 6]
    e["action_mask"] = np.repeat(np.asarray(e["action_mask"])[:, None] > 0.5, 7, 1)
    for k in ("episode_id", "t", "vl_meta"):
        e.pop(k, None)

m1 = vl_heads_hook.make(copy.deepcopy(m0), cfg).float().eval()
theirs, ours = m0.action_model.model, m1.action_model.head
pairs = [(ours.norm, theirs.layer_norm1), (ours.inp, theirs.fc1), (ours.final_norm, theirs.layer_norm2), (ours.out, theirs.fc2)]
for blk, ref in zip(ours.blocks, theirs.mlp_resnet_blocks):
    pairs += [(blk.norm, ref.ffn[0]), (blk.fc1, ref.ffn[1])]
with torch.no_grad():
    for a, b in pairs:
        a.weight.copy_(b.weight); a.bias.copy_(b.bias)
n_ours = sum(p.numel() for p in m1.action_model.parameters())
n_theirs = sum(p.numel() for p in m0.action_model.parameters())
res["head_params"] = {"hook": n_ours, "starvla": n_theirs, "proprio_map": ours.proprio.weight.numel() + ours.proprio.bias.numel()}

with torch.no_grad():
    l0 = float(m0.forward(copy.deepcopy(no_state))["action_loss"])
    l1 = float(m1.forward(copy.deepcopy(ex))["action_loss"])
    ex_text = copy.deepcopy(ex)  # stock QwenOFT with the state (written as text) and its own [K, 7] mask
    for e in ex_text:
        e["action_mask"] = np.repeat(np.asarray(e["action_mask"])[:, None] > 0.5, 7, 1)
        for k in ("episode_id", "t", "vl_meta"):
            e.pop(k, None)
    l0_state_text = float(m0.forward(ex_text)["action_loss"])
res["loss_starvla_no_state"], res["loss_hook_with_state"], res["loss_starvla_state_as_text"] = l0, l1, l0_state_text
res["step0_parity"] = abs(l0 - l1) <= 1e-6 * max(1.0, abs(l0))

m1.train()
loss = m1.forward(copy.deepcopy(ex))["action_loss"]
loss.backward()
g_prop = float(ours.proprio.weight.grad.norm())
g_lm = sum(float(p.grad.norm()) for n, p in m1.named_parameters() if "language_model" in n and p.grad is not None)
res["grad_norm_proprio_map"], res["grad_norm_lm_sum"] = g_prop, g_lm
m1.eval()
with torch.no_grad():
    ours.proprio.weight.add_(0.01 * torch.randn_like(ours.proprio.weight))  # a trained-looking gate, so proprio matters below
pred = m1.predict_action(copy.deepcopy(ex))["normalized_actions"]
res["predict_shape"] = list(pred.shape)
res["predict_in_range"] = bool(np.all(np.abs(pred) <= 1.0))

os.environ["VLL_NO_FIT"] = "1"
sd = m1.state_dict()
m2 = vl_heads_hook.make(build_framework(cfg), cfg).float().eval()
assert float(m2.action_model.prop_fitted) == 0.0
missing = m2.load_state_dict(sd, strict=True)
pred2 = m2.predict_action(copy.deepcopy(ex))["normalized_actions"]
res["server_strict_load"] = True
res["server_pred_max_abs_diff"] = float(np.abs(pred2 - pred).max())
shuffled = copy.deepcopy(ex)
for e in shuffled:
    e["state"] = np.asarray(e["state"]) + 0.05
res["proprio_changes_prediction"] = float(np.abs(m2.predict_action(shuffled)["normalized_actions"] - pred2).max()) > 0

stats = json.load(open(os.path.join(out, "proprio_norm.json")))
res["proprio_norm"] = stats
res["action_norm"] = json.load(open(os.path.join(out, "action_norm.json")))
res["prompt_template"] = json.load(open(os.path.join(out, "prompt_template.json")))
res["full_prompt_example"] = vl_heads_hook.full_prompt(ex[0]["lang"])
res["gripper_in_prediction"] = sorted(set(np.asarray(pred)[..., 6].ravel().tolist()))
ok = (res["step0_parity"] and g_prop > 0 and g_lm > 0 and res["predict_in_range"] and res["server_pred_max_abs_diff"] < 1e-5
      and res["proprio_changes_prediction"] and not res["drop_incomplete"] and stats["kind"] == "minmax_subset_v1"
      and res.get("tail_chunk", {}).get("repeats_last", False) and set(res["gripper_in_prediction"]) <= {0.0, 1.0})
# where dropout (schema 5.5): the hook's training view against vla_heads' draw over 1,000 (episode_id, t) rows
from vla_heads.cond import withheld_draw
from vla_where.failure import is_withheld
ids = [(ds[i]["episode_id"], ds[i]["t"]) for i in range(0, 200)]
rows = [(eid, t + k) for eid, t in ids for k in range(5)]
draw = [is_withheld(e, t, 17, 0.2) for e, t in rows]
res["dropout"] = {"rows": len(rows), "withheld": int(sum(draw)), "rate": sum(draw) / len(rows),
                  "agrees_with_vla_heads": all(d == withheld_draw(e, t, 17, 0.2) for d, (e, t) in zip(draw, rows))}
p_hat = res["dropout"]["rate"]
res["dropout"]["within_3sd"] = abs(p_hat - 0.2) <= 3 * (0.2 * 0.8 / len(rows)) ** 0.5
ok = ok and res["dropout"]["agrees_with_vla_heads"] and res["dropout"]["within_3sd"]

# flow expert through the hook (taps of the tiny 4-layer model: [2, -1]); detach_backbone on and off
for detach in (False, True):
    fcfg = OmegaConf.merge(cfg, OmegaConf.create({"framework": {"vla_heads": {"head": "flow", "taps": [2, -1], "detach_backbone": detach,
                                                                             "reg_hidden": None, "reg_blocks": None}}}))
    os.environ.pop("VLL_NO_FIT", None)
    torch.manual_seed(0)
    mf = vl_heads_hook.make(copy.deepcopy(m0), fcfg).float().train()
    lf = mf.forward(copy.deepcopy(ex))["action_loss"]
    lf.backward()
    g_lm_f = sum(float(p.grad.norm()) for n_, p in mf.named_parameters() if "language_model" in n_ and p.grad is not None)
    g_head_f = sum(float(p.grad.norm()) for n_, p in mf.action_model.named_parameters() if p.grad is not None)
    mf.eval(); torch.manual_seed(1)
    pf = mf.predict_action(copy.deepcopy(ex))["normalized_actions"]
    os.environ["VLL_NO_FIT"] = "1"
    mf2 = vl_heads_hook.make(build_framework(fcfg), fcfg).float().eval(); mf2.load_state_dict(mf.state_dict(), strict=True)
    torch.manual_seed(1)
    pf2 = mf2.predict_action(copy.deepcopy(ex))["normalized_actions"]
    res[f"flow_detach_{detach}"] = {"loss": float(lf), "finite": bool(torch.isfinite(lf)), "grad_lm": g_lm_f, "grad_head": g_head_f,
                                    "predict_shape": list(pf.shape), "in_range": bool(np.all(np.abs(pf) <= 1)),
                                    "server_same_with_seed": float(np.abs(pf - pf2).max())}
    ok = ok and bool(torch.isfinite(lf)) and g_head_f > 0 and ((g_lm_f == 0) if detach else (g_lm_f > 0)) and list(pf.shape) == [3, 8, 7] \
        and float(np.abs(pf - pf2).max()) < 1e-5
res["verdict"] = "HOOK_OK" if ok else "HOOK_FAIL"
json.dump(res, open(os.path.join(out, "hook_check.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
print(res["verdict"])
