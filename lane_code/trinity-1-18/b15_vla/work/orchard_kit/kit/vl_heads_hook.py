"""framework.head_hook=vl_heads_hook:make: run StarVLA's QwenOFT with vla_heads' head (a) and normalised proprioception.

What changes (identical for every arm):
- `model.action_model` becomes `HookHead`, which wraps `vla_heads.RegressionHead` configured as StarVLA's
  L1RegressionActionHead (reg_block oft, relu, input activation, final LayerNorm, hidden 2 x 4096, 2 blocks; parity with
  StarVLA's head is vla_heads' test_parity_starvla). It keeps StarVLA's contract predict_action(queries [B, 8, 4096]).
- Proprioception (LeRobot observation.state, 8-D: eef xyz, eef axis-angle, 2 finger joints) enters through the head's
  zero-initialised Linear(8 -> 8192), so at step 0 the policy predicts exactly what it predicts without proprio.
  Normalisation (schema v1 section 7): per-dimension min-max over the training subset mapped to [-1, 1], clipped;
  constant dimensions map to 0. min/max live in the head as buffers, so the checkpoint carries them; the run dir gets
  proprio_norm.json and action_norm.json ({kind: minmax_subset_v1, min, max, count, subset_sha}).
- Gripper (schema v2 section 7): the head regresses g = 1 - 2 a6 (-1 open, +1 close; IPEC a6 = 1 is open), not
  normalised. At inference the hook returns a6 = 0 if g >= 0 else 1, so StarVLA's client (env = 1 - 2 [a6 > 0.5]) sends
  +1 (close) iff g >= 0, the tie g = 0 included, as the schema requires.
- Prompt (schema v1 section 4, template TEMPLATE_ID): build_lang() is the one builder for training and the closed-loop
  server: the instruction, then (U1) the where line; QwenOFT appends the action-query suffix. TEMPLATE_SHA256 is written
  to the run dir, the head buffers' companion JSON and the server log.
- QwenOFT appends the state to the prompt as 256-bin text whenever an example carries 'state'. The patched forward and
  predict_action remove 'state', 'where', 'where_mask' and 'where_line' before StarVLA sees the examples.
- U1 (where input): examples carry 'where' [2, 18], 'where_mask' [2] and 'where_line'; set framework.vla_heads.cond=spatial_readouts.

Config (framework.vla_heads.*): proprio_dim (8), cond (none), reg_hidden (null = 2 x VLM width, StarVLA's), reg_blocks (2).
"""
import glob
import hashlib
import json
import os
import sys
import types

import numpy as np
import torch
from torch import nn

from vla_heads import HeadInputs, VLAConfig
from vla_heads.heads import make_head


TEMPLATE_ID = "starvla_qwenoft_985c2238_v1"
SUFFIX = " Please predict the next 8 robot actions: <action>" + "\U0001F50D" * 8 + "<action>."
TEMPLATE = "{instruction}{where}" + SUFFIX
TEMPLATE_SHA256 = hashlib.sha256((TEMPLATE_ID + "\n" + TEMPLATE).encode()).hexdigest()


def build_lang(instruction, where_line=None):
    """The text QwenOFT receives as 'lang' (it appends SUFFIX itself): B0/B1 the instruction, U1 instruction + where line."""
    return instruction if not where_line else f"{instruction} {where_line}"


def full_prompt(instruction, where_line=None):
    return build_lang(instruction, where_line) + SUFFIX


def _get(o, k, d=None):
    if o is None:
        return d
    if isinstance(o, dict):
        return o.get(k, d)
    if hasattr(o, "get") and not isinstance(o, types.SimpleNamespace):
        try:
            return o.get(k, d)
        except TypeError:
            pass
    return getattr(o, k, d)


def _plain(o):
    """OmegaConf / StarVLA AccessTrackedConfig / namespace / dict tree -> plain dict (the trainer wraps the config in
    AccessTrackedConfig, the policy server rebuilds it as a namespace)."""
    if type(o).__name__ == "AccessTrackedConfig" and hasattr(o, "_cfg"):
        o = o._cfg
    try:
        from omegaconf import DictConfig, ListConfig, OmegaConf
        if isinstance(o, (DictConfig, ListConfig)):
            return OmegaConf.to_container(o, resolve=True)
    except ImportError:
        pass
    if isinstance(o, dict):
        return {k: _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if hasattr(o, "__dict__") and not isinstance(o, (str, bytes)):
        return {k: _plain(v) for k, v in vars(o).items()}
    return o


SUPPORTED = ("regression", "flow")


def head_config(cfg, hidden):
    """The head's VLAConfig. A schema-10 `vla:` tree in the run config wins (VLAConfig.from_spec refuses a wrong schema
    tag); otherwise framework.vla_heads: head (regression | flow), proprio_dim, cond, taps, detach_backbone, flow_*.
    hidden = the VLM width QwenOFT sized its own head with; the regression head is StarVLA's (hidden 2 x width)."""
    spec = _get(cfg, "vla", None)
    if spec is not None:
        vc, _ = VLAConfig.from_spec({"vla": _plain(spec)}, hidden_size=int(hidden))
    else:
        hc = _plain(_get(cfg.framework, "vla_heads", None)) or {}
        head = hc.pop("head", "regression")
        base = dict(head=head, hidden_size=int(hidden), chunk=int(_get(cfg.framework.action_model, "action_horizon", 8)),
                    action_dim=int(_get(cfg.framework.action_model, "action_dim", 7)), proprio_dim=int(hc.pop("proprio_dim", 8)),
                    proprio_inject="head", cond=str(hc.pop("cond", "none")))
        if head == "regression":
            base.update(reg_arch="starvla_oft_985c2238", reg_hidden=int(hc.pop("reg_hidden", None) or 2 * int(hidden)),
                        reg_blocks=int(hc.pop("reg_blocks", 2)), reg_block="oft", reg_act="relu", reg_input_act=True, reg_final_norm=True)
        base.update({k: v for k, v in hc.items() if v is not None})
        vc = VLAConfig.from_dict(base)
    if vc.head not in SUPPORTED:
        raise ValueError(f"the LIBERO hook runs heads {SUPPORTED}; {vc.head!r} needs VLAPolicy (token heads write with the LM)")
    if vc.lm_token_loss != "none":
        raise ValueError("lm_token_loss (F1's FAST loss) needs the LM to write codec tokens; the StarVLA hook does not wire it")
    return vc


class HookHead(nn.Module):
    def __init__(self, vcfg):
        super().__init__()
        self.vcfg = vcfg
        self.head = make_head(vcfg)
        p = max(vcfg.proprio_dim, 1)
        self.register_buffer("prop_min", torch.zeros(p))
        self.register_buffer("prop_max", torch.zeros(p))
        self.register_buffer("prop_fitted", torch.zeros(()))
        self._ctx = {}

    def fit_proprio(self, states):
        self.prop_min.copy_(torch.as_tensor(states.min(0), dtype=torch.float32))
        self.prop_max.copy_(torch.as_tensor(states.max(0), dtype=torch.float32))
        self.prop_fitted.fill_(1.0)

    def norm_proprio(self, raw):
        """Schema 7 min-max to [-1, 1], clipped; only an exactly constant span maps to 0 (as vla_heads.utils.norm)."""
        lo, hi = self.prop_min.float().to(raw.device), self.prop_max.float().to(raw.device)
        rng = hi - lo
        x = torch.where(rng > 0, 2 * (raw.float() - lo) / torch.where(rng > 0, rng, torch.ones_like(rng)) - 1, torch.zeros_like(raw.float()))
        return x.clamp(-1, 1)

    def set_context(self, examples, device):
        ctx = {}
        if self.vcfg.proprio_dim:
            if float(self.prop_fitted) != 1.0:
                raise RuntimeError("proprio statistics were never fitted (training) or loaded (checkpoint)")
            if any("state" not in e for e in examples):
                raise ValueError("proprio_dim > 0 but an example has no 'state' (set datasets.vla_data.include_state=true; "
                                 "the eval client must send the 8-D LIBERO state)")
            raw = torch.as_tensor(np.stack([np.asarray(e["state"], np.float32).reshape(-1)[: self.vcfg.proprio_dim]
                                            for e in examples]), device=device)
            ctx["proprio"] = self.norm_proprio(raw)  # fp32 at the head boundary (schema 1)
        if self.vcfg.cond in ("spatial_readouts", "both"):
            ctx["where"] = torch.as_tensor(np.stack([np.asarray(e["where"], np.float32) for e in examples]), device=device)
            ctx["where_mask"] = torch.as_tensor(np.stack([np.asarray(e["where_mask"], bool) for e in examples]), device=device)
        self._ctx = ctx

    def inputs(self, lm_states, lm_mask, query_states=None, tap_states=None):
        c = self._ctx
        prop = c.get("proprio")
        return HeadInputs(lm_states=lm_states, lm_mask=lm_mask, query_states=query_states, tap_states=tap_states,
                          proprio=None if prop is None else prop.float(), where=c.get("where"), where_mask=c.get("where_mask"))

    def predict_action(self, queries):  # StarVLA's contract (regression): queries [B, K, D] -> [B, K, A]
        b, k, _ = queries.shape
        return self.head(self.inputs(queries, torch.ones(b, k, dtype=torch.bool, device=queries.device), query_states=queries))


def prepare_where(examples, vcfg, training):
    """Schema 5.5: in training, the cached unwithheld provider output (where_output, from vl_data_patch with
    VLL_WHERE_CACHE) passes through vla_where.failure.training_view, so chunk (episode_id, t) is withheld iff its sha256
    draw falls below where_dropout (seed where_seed); text and vector are withheld together. At evaluation an example
    carries where_output from the online provider (no dropout) or ready where / where_mask / where_line."""
    if vcfg.cond not in ("spatial_readouts", "both"):
        return examples
    from vla_where.failure import training_view
    from vla_where.types import WhereOutput
    out = []
    for e in examples:
        if "where_output" not in e:
            if training or "where" not in e:
                raise ValueError("U1 examples need where_output (training: with episode_id and t)")
            out.append(e)
            continue
        w = WhereOutput.from_dict(e["where_output"]) if isinstance(e["where_output"], dict) else e["where_output"]
        if training and vcfg.where_dropout > 0:
            w = training_view(w, e["episode_id"], int(e["t"]), vcfg.where_seed, vcfg.where_dropout)
        out.append(dict(e, where=w.vector(), where_mask=w.mask(), where_line=w.line))
    return out


def _mixture_dirs(cfg):
    from starVLA.dataloader.gr00t_lerobot.registry import DATASET_NAMED_MIXTURES
    vd = cfg.datasets.vla_data
    return [os.path.join(str(vd.data_root_dir), name) for name, _, _ in DATASET_NAMED_MIXTURES[str(vd.data_mix)]]


def training_columns(cfg, column):
    """Every frame's `column` over the training mixture (subset views list only their own episodes), and the subset sha."""
    import pyarrow.parquet as pq
    out, ids = [], []
    for d in _mixture_dirs(cfg):
        info = json.load(open(os.path.join(d, "meta/info.json")))
        for line in open(os.path.join(d, "meta/episodes.jsonl")):
            i = json.loads(line)["episode_index"]
            ids.append(f"{os.path.basename(d)}/{i}")
            f = os.path.join(d, info["data_path"].format(episode_chunk=i // info["chunks_size"], episode_index=i))
            col = pq.read_table(f, columns=[column]).column(column).to_numpy(zero_copy_only=False)
            out.append(np.stack(col).astype(np.float64))
    return np.concatenate(out), hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def minmax_json(x, sha):
    return {"kind": "minmax_subset_v1", "min": x.min(0).tolist(), "max": x.max(0).tolist(), "count": int(len(x)), "subset_sha": sha}


DROP = ("state", "where", "where_mask", "where_line", "where_output", "episode_id", "t", "vl_meta")


def postprocess(normalized):
    """Clip the prediction to [-1, 1] (schema v2 section 7) and turn the regressed g into the a6 StarVLA's server and client
    expect: a6 = 0 if g >= 0 else 1, so the client sends env +1 (close) iff g >= 0. Returns (actions, g)."""
    a = np.clip(np.asarray(normalized, dtype=np.float32), -1.0, 1.0)
    g = a[..., 6].copy()
    a[..., 6] = np.where(g >= 0, 0.0, 1.0)
    return a, g


def client_gripper(a6):
    """StarVLA's LIBERO client rule (model2libero_interface / vl_eval.py)."""
    return 1.0 - 2.0 * float(float(a6) > 0.5)


def _prepare(examples, training):
    out = []
    for e in examples:
        f = {k: v for k, v in e.items() if k not in DROP}
        f["lang"] = build_lang(e["lang"], e.get("where_line"))
        if training:
            a = np.array(e["action"], dtype=np.float32, copy=True)
            a[:, 6] = 1.0 - 2.0 * a[:, 6]  # schema section 7: g = 1 - 2 a6
            f["action"] = a
        m = e.get("action_mask")
        if m is not None:
            m = np.asarray(m)
            f["action_mask"] = (np.repeat(m[:, None], np.asarray(e["action"]).shape[-1], 1) > 0.5) if m.ndim == 1 else m.astype(bool)
        out.append(f)
    return out


def _flow_forward(model, examples, training):
    """The flow (or DDPM) expert through the same prompt and images as QwenOFT: taps of the VLM's hidden states over the
    whole prompt (one-based layer l = hidden_states[l]; -1 = hidden_states[-1], after the final norm), the head's own
    loss (masked by action_mask [B, K]) or sampler. Returns QwenOFT's dict keys."""
    mod = sys.modules[type(model).__module__]
    hh, qi = model.action_model, model.qwen_vl_interface
    images = [e["image"] for e in examples]
    if not training:
        images = [mod.to_pil_preserve(x) for x in images]
        size = getattr(model.config.datasets.vla_data, "obs_image_size", None)
        if size:
            images = mod.resize_images(images, target_size=size)
    instructions = [e["lang"] + SUFFIX for e in examples]
    inputs = qi.build_qwenvl_inputs(images=images, instructions=instructions)
    with torch.autocast("cuda", dtype=torch.bfloat16):
        out = qi(**inputs, output_hidden_states=True, return_dict=True)
    hs = out.hidden_states
    taps = list(hh.vcfg.taps) or [16, -1]
    tap_states = torch.stack([hs[-1] if t == -1 else hs[t] for t in taps])
    lm_mask = inputs["attention_mask"].bool()
    hin = hh.inputs(hs[-1], lm_mask, tap_states=tap_states)
    k = hh.vcfg.chunk
    if training:
        acts = torch.as_tensor(np.stack([np.asarray(e["action"], np.float32)[-k:] for e in examples]), device=lm_mask.device)
        m = [e.get("action_mask") for e in examples]
        mask = None if m[0] is None else torch.as_tensor(np.stack([np.asarray(x)[-k:].astype(bool).any(-1) if np.asarray(x).ndim == 2
                                                                    else np.asarray(x)[-k:] > 0.5 for x in m]), device=lm_mask.device)
        return {"action_loss": hh.head.loss(hin, acts, mask)["loss"]}
    with torch.no_grad():
        return {"normalized_actions": hh.head.predict(hin).float().cpu().numpy()}


def make(model, cfg):
    vcfg = head_config(cfg, model.action_model.model.fc1.in_features)
    hh = HookHead(vcfg)
    if vcfg.proprio_dim and os.environ.get("VLL_NO_FIT") != "1":  # the policy server loads the statistics from the checkpoint
        states, sha = training_columns(cfg, "observation.state")
        assert states.shape[1] >= vcfg.proprio_dim, states.shape
        hh.fit_proprio(states[:, : vcfg.proprio_dim])
        out = _get(cfg, "output_dir", None)
        if out and int(os.environ.get("RANK", "0")) == 0:
            os.makedirs(out, exist_ok=True)
            json.dump(dict(minmax_json(states[:, : vcfg.proprio_dim], sha), data_mix=str(cfg.datasets.vla_data.data_mix)),
                      open(os.path.join(out, "proprio_norm.json"), "w"))
            acts, _ = training_columns(cfg, "action")
            json.dump(dict(minmax_json(acts[:, :6], sha), data_mix=str(cfg.datasets.vla_data.data_mix), gripper="g = 1 - 2 a6, not normalised"),
                      open(os.path.join(out, "action_norm.json"), "w"))
            json.dump({"template_id": TEMPLATE_ID, "template_sha256": TEMPLATE_SHA256, "template": TEMPLATE},
                      open(os.path.join(out, "prompt_template.json"), "w"), ensure_ascii=False)
    model.action_model = hh
    orig_forward, orig_predict = type(model).forward, type(model).predict_action

    flow = vcfg.head == "flow"

    def forward(self, examples=None, **kw):
        examples = prepare_where(examples, self.action_model.vcfg, training=True)
        self.action_model.set_context(examples, next(self.action_model.parameters()).device)
        if flow:
            return _flow_forward(self, _prepare(examples, training=True), training=True)
        return orig_forward(self, _prepare(examples, training=True), **kw)

    def predict_action(self, examples=None, **kw):
        if type(examples) is not list:
            examples = [examples]
        examples = prepare_where(examples, self.action_model.vcfg, training=False)
        self.action_model.set_context(examples, next(self.action_model.parameters()).device)
        if flow:
            out = _flow_forward(self, _prepare(examples, training=False), training=False)
        else:
            out = orig_predict(self, _prepare(examples, training=False), **kw)
        out["normalized_actions"], out["predicted_g"] = postprocess(out["normalized_actions"])
        return out

    model.forward = types.MethodType(forward, model)
    model.predict_action = types.MethodType(predict_action, model)
    model.vl_head_hook = {"head": f"vla_heads {vcfg.head}", "proprio_dim": vcfg.proprio_dim, "cond": vcfg.cond,
                          "template_id": TEMPLATE_ID, "template_sha256": TEMPLATE_SHA256, "schema": "vla_schema_v2",
                          "vla_heads_cfg_sha": vcfg.sha256() if hasattr(vcfg, "sha256") else None}
    return model
