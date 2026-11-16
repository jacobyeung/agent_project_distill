"""vla_libero trainer: StarVLA's train_starvla.py (commit 985c2238) with five changes, identical for every arm.

1. A local `wandb` stand-in appends logged metrics to <output_dir>/metrics.jsonl (no W&B account or network).
2. Step-indexed sampling. StarVLA's mixture dataset draws (episode, frame) from hash(epoch, index, seed), but the
   trainer never advances the dataset epoch, so every pass replays the same draws. Here the DataLoader reads the
   index stream start, start+1, ... with no wrap, so draw i of the run is index i: fresh draws every pass, and the
   batch at global step s depends only on s. Resume needs no skipping and reproduces the uninterrupted order.
3. Weight checkpoints only at the steps in trainer.save_steps (e.g. [1000,2000,5000,10000]); save_interval is unused.
4. Full training state (accelerator.save_state: model, optimizer, RNG) at trainer.state_steps under
   <output_dir>/state/steps_<n>, and exact resume with trainer.resume_state=<dir>|latest. StarVLA's own is_resume
   reloads weights only (fresh optimizer moments), which is why it is not used.
5. A per-step trace <output_dir>/trace.jsonl (step, loss, lr, step seconds, samples/s, global grad norm, peak memory,
   batch fingerprint, the norms of the head's zero-initialised proprio/where maps; every trainer.trace_module_every steps
   the parameter norms of the head and the LM) that the stall guard watches, and framework.head_hook=<module>:<factory>
   to replace the OFT action head (see HEADS_HOOK.md).
6. The model is built under set_seed(seed), so the action head's initialisation is a function of the seed (StarVLA seeds
   only later, in prepare_training, which left every run's head init random).
7. Self-stop (all ranks together): a non-finite loss on any rank, a step slower than trainer.stop_slow_factor (3) x the
   median of the last 200 steps (after 20 warm steps), or, in the first trainer.early_loss_steps (50) steps of a fresh run,
   a rank-mean loss above trainer.early_loss_factor (off unless set; arm_testL.yaml: 5) x the step-1 rank-mean loss, writes <output_dir>/STOP_REASON.json
   and exits with code 3. A disk too full for the next weight export exits with code 5 (STOP_REASON.json says so).
   trainer.state_every=N keeps ONE rolling full state: every N steps it writes state/steps_<n>, marks it complete
   (vl_meta.json written last), points the symlink state/current at it (os.replace, atomic) and only then removes the
   previous rolling state, so a complete state exists at every instant and the disk holds two only during a save.
   Before each state save rank 0 checks the free space (the last state's size, or trainer.state_gb_est before the first,
   plus trainer.disk_margin_gb); if short, that save is skipped and logged in summary.jsonl. Weight exports are checked
   the same way against trainer.export_gb_est. resume_state=latest picks the newest complete state.
8. VLL_DETERMINISTIC=1 (environment, read before torch starts): torch.use_deterministic_algorithms(True, warn_only=True),
   cuDNN deterministic without benchmark, CUBLAS_WORKSPACE_CONFIG=:4096:8 and FLASH_ATTENTION_DETERMINISTIC=1 (the
   flash-attn backward). The fla Triton kernels and causal-conv1d's backward have no such switch.
9. The weight export at the final step doubles as final_model/pytorch_model.pt through a hard link (no second copy);
   trainer.final_export=false skips the final weights when no export exists (test runs).
   summary.jsonl records the size of every export and state.

Run it exactly like train_starvla.py: accelerate launch ... vl_train.py --config_yaml X.yaml key=value ...
"""
import glob
import hashlib
import importlib
import math
import statistics
import importlib.machinery
import json
import os
import shutil
import sys
import time
import types

import numpy as np

DETERMINISTIC = os.environ.get("VLL_DETERMINISTIC") == "1"
if DETERMINISTIC:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    os.environ.setdefault("FLASH_ATTENTION_DETERMINISTIC", "1")


class _MetricsLog(types.ModuleType):
    path = None

    def init(self, dir=None, **kwargs):
        self.path = os.path.join(os.path.dirname(dir), "metrics.jsonl")

    def log(self, metrics, step=None):
        if self.path:
            with open(self.path, "a") as f:
                f.write(json.dumps({"step": step, **{k: float(v) for k, v in metrics.items()}}) + "\n")

    def finish(self):
        pass


sys.modules["wandb"] = _MetricsLog("wandb")
sys.modules["wandb"].__spec__ = importlib.machinery.ModuleSpec("wandb", None)

import torch  # noqa: E402
import torch.distributed as dist  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402
from torch.utils.data import DataLoader, Sampler  # noqa: E402

if DETERMINISTIC:
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = True, False

import starVLA.training.train_starvla as T  # noqa: E402  (builds the Accelerator)
import vl_data_patch  # noqa: E402,F401  (schema v1: every frame a chunk start, action_mask past the episode end)
from starVLA.model.framework.share_tools import apply_config_compat  # noqa: E402
from starVLA.training.trainer_utils.trainer_tools import normalize_dotlist_args  # noqa: E402

RESUME = {"step": 0, "path": None}


class StepIndexSampler(Sampler):
    """Yields start, start+1, ..., total-1. accelerate shards the batches across ranks round-robin."""

    def __init__(self, start, total):
        self.start, self.total = int(start), int(total)

    def __iter__(self):
        return iter(range(self.start, self.total))

    def __len__(self):
        return self.total - self.start


def _world():
    return int(os.environ.get("WORLD_SIZE", "1"))


def _rank():
    return dist.get_rank() if dist.is_initialized() else int(os.environ.get("RANK", "0"))


_orig_build_dataloader = T.build_dataloader


def build_dataloader(cfg, dataset_py="lerobot_datasets"):
    dl = _orig_build_dataloader(cfg=cfg, dataset_py=dataset_py)
    vd = cfg.datasets.vla_data
    bs = int(vd.per_device_batch_size)
    accum = int(cfg.trainer.get("gradient_accumulation_steps", 1))
    per_step = bs * _world() * accum
    total = (int(cfg.trainer.max_train_steps) + 2) * per_step
    start = RESUME["step"] * per_step
    nw = int(vd.get("num_workers", 4))
    kw = dict(batch_size=bs, collate_fn=dl.collate_fn, num_workers=nw, pin_memory=bool(vd.get("pin_memory", True)),
              sampler=StepIndexSampler(start, total), drop_last=True)
    if nw > 0:
        kw.update(persistent_workers=bool(vd.get("persistent_workers", True)), prefetch_factor=int(vd.get("prefetch_factor", 2)))
    T.logger.info(f"StepIndexSampler start={start} total={total} per_step={per_step}")
    return DataLoader(dl.dataset, **kw)


T.build_dataloader = build_dataloader


def _fingerprint(batch):
    h = hashlib.sha1()
    for ex in batch:
        h.update(str(ex["lang"]).encode())
        h.update(np.ascontiguousarray(np.asarray(ex["action"], dtype=np.float32)).tobytes())
    return h.hexdigest()[:16]


class Trainer(T.VLATrainer):
    def _cfg_list(self, key):
        v = self.config.trainer.get(key, None)
        return set() if v is None else {int(x) for x in v}

    def _init_checkpointing(self):
        if RESUME["path"]:
            self.checkpoint_dir = os.path.join(self.config.output_dir, "checkpoints")
            os.makedirs(self.checkpoint_dir, exist_ok=True)
            self.completed_steps = RESUME["step"]
            self.resume_from_checkpoint = RESUME["path"]
            return
        super()._init_checkpointing()

    def prepare_training(self):
        super().prepare_training()
        if RESUME["path"]:
            self.accelerator.load_state(RESUME["path"])
            T.logger.info(f"Resumed full state from {RESUME['path']} at step {self.completed_steps}")
        self._mem0 = round(torch.cuda.memory_allocated() / 2**30, 2) if torch.cuda.is_available() else None
        self._trace_path = os.path.join(self.config.output_dir, "trace.jsonl")
        self._t0 = time.time()

    def _train_step(self, batch_vla, batch_vlm=None):
        fp = _fingerprint(batch_vla)
        t_start = time.time()
        out = super()._train_step(batch_vla, batch_vlm)
        dt = time.time() - t_start
        loss = float(out["action_dit_loss"])
        step = self.completed_steps + 1
        dts = getattr(self, "_dts", [])
        self._dts = dts
        reason = 0
        if not math.isfinite(loss):
            reason = 1
        factor = float(self.config.trainer.get("stop_slow_factor", 3.0) or 0)
        med = statistics.median(dts[-200:]) if len(dts) >= 20 else None
        if factor and med and dt > factor * med:
            reason = max(reason, 2)
        dts.append(dt)
        e_steps = int(self.config.trainer.get("early_loss_steps", 50) or 0)
        e_factor = float(self.config.trainer.get("early_loss_factor", 0) or 0)
        mean_loss = None
        if e_factor and RESUME["step"] == 0 and step <= e_steps:  # same condition on every rank, so the collective matches
            mean_loss = loss
            if dist.is_initialized():
                t = torch.tensor([loss], device=self.accelerator.device, dtype=torch.float64)
                dist.all_reduce(t, op=dist.ReduceOp.SUM)
                mean_loss = float(t.item()) / dist.get_world_size()
            if step == 1:
                self._loss1 = mean_loss
            elif getattr(self, "_loss1", None) is not None and mean_loss > e_factor * self._loss1:
                reason = max(reason, 4)
        if dist.is_initialized():
            flag = torch.tensor([float(reason)], device=self.accelerator.device)
            dist.all_reduce(flag, op=dist.ReduceOp.MAX)
            reason = int(flag.item())
        if self.accelerator.is_main_process:
            per_step = int(self.config.datasets.vla_data.per_device_batch_size) * _world()
            rec = {"step": step, "loss": loss, "lr": self.lr_scheduler.get_last_lr(), "batch_fp": fp, "step_s": round(dt, 3),
                   "samples_per_s": round(per_step / max(dt, 1e-9), 2),
                   "t": round(time.time() - self._t0, 2), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            gn = getattr(self.model, "get_global_grad_norm", None)
            if callable(gn):
                try:
                    v = gn()
                    rec["grad_norm"] = None if v is None else float(v)
                except Exception:  # noqa: BLE001
                    pass
            if torch.cuda.is_available():
                rec["gpu_peak_gib"] = round(torch.cuda.max_memory_allocated() / 2**30, 2)
                rec["gpu_after_prepare_gib"] = self._mem0
            m = T._unwrap_model(self.accelerator, self.model)
            rec.update(_gate_norms(m))
            every = int(self.config.trainer.get("trace_module_every", 100) or 0)
            if every and (step % every == 0 or step == 1):
                rec["param_norms"] = _module_norms(m)
            if self.config.trainer.get("trace_param_sums", False):
                rec["param_sums"] = _param_sums(m)
            if mean_loss is not None:
                rec["loss_rank_mean"] = mean_loss
            if reason:
                msg = {1: lambda: "non-finite loss", 2: lambda: f"step {dt:.2f}s > {factor} x median {med:.2f}s",
                       4: lambda: f"early loss blow-up: rank-mean loss {mean_loss} > {e_factor} x step-1 loss "
                                  f"{getattr(self, '_loss1', None)} (step {step} <= {e_steps})"}.get(reason)
                rec["stop"] = msg() if msg and (reason != 2 or med) else "other rank"
            with open(self._trace_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            if reason:
                json.dump({"step": step, "reason": rec["stop"], "utc": rec["utc"]},
                          open(os.path.join(self.config.output_dir, "STOP_REASON.json"), "w"))
        if reason:
            T.logger.error(f"self-stop at step {step}: reason code {reason}")
            raise SystemExit(3)
        return out

    def _summary(self, rec):
        if self.accelerator.is_main_process:
            with open(os.path.join(self.config.output_dir, "summary.jsonl"), "a") as f:
                f.write(json.dumps({"steps": self.completed_steps, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **rec}) + "\n")

    def _room(self, path, need_gb):
        """Rank 0 measures the free space under path; every rank gets the same verdict (True = need_gb fits)."""
        free = shutil.disk_usage(path).free / 2**30 if self.accelerator.is_main_process else 0.0
        ok = 1.0 if (not self.accelerator.is_main_process or free >= need_gb) else 0.0
        if dist.is_initialized():
            t = torch.tensor([ok], device=self.accelerator.device)
            dist.all_reduce(t, op=dist.ReduceOp.MIN)
            ok = float(t.item())
        return ok == 1.0, round(free, 1)

    def _need_gb(self, last_key, est_key, est_default):
        margin = float(self.config.trainer.get("disk_margin_gb", 10))
        last = getattr(self, last_key, None)
        return round((last * 1.05 if last else float(self.config.trainer.get(est_key, est_default))) + margin, 1)

    def _save_weights(self, path):
        need = self._need_gb("_export_gb", "export_gb_est", 20)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        ok, free = self._room(os.path.dirname(path), need)
        if not ok:  # refuse to fill the disk: stop with a reason instead of a torn export
            self._summary({"export_refused": path, "free_gb": free, "need_gb": need})
            if self.accelerator.is_main_process:
                json.dump({"step": self.completed_steps, "reason": f"disk: {free} GB free < {need} GB for export {path}"},
                          open(os.path.join(self.config.output_dir, "STOP_REASON.json"), "w"))
            T.logger.error(f"disk full for export {path}: {free} GB free, need {need} GB")
            raise SystemExit(5)
        # every rank enters get_state_dict (a collective under ZeRO-3); rank 0 writes. StarVLA calls it on rank 0 only.
        sd = T._get_state_dict(self.accelerator, self.model)
        if self.accelerator.is_main_process:
            torch.save(sd, path + ".tmp")
            os.replace(path + ".tmp", path)
            self._export_gb = os.path.getsize(path) / 2**30
            self._summary({"path": path, "kind": "export", "gb": round(self._export_gb, 2), "free_gb_before": free})
            if isinstance(self.config, T.AccessTrackedConfig):
                self.config.save_accessed_config(os.path.join(self.config.output_dir, "config.yaml"), use_original_values=False)
        del sd
        self.accelerator.wait_for_everyone()

    def _finalize_training(self):
        final = os.path.join(self.config.output_dir, "final_model", "pytorch_model.pt")
        same = os.path.join(self.checkpoint_dir, f"steps_{self.completed_steps}_pytorch_model.pt")
        if os.path.exists(same):  # the last export is the final model: hard link, no second copy
            if self.accelerator.is_main_process:
                os.makedirs(os.path.dirname(final), exist_ok=True)
                if os.path.exists(final):
                    os.replace(final, final + ".old")
                os.link(same, final)
                self._summary({"path": final, "kind": "final_link", "of": same})
            self.accelerator.wait_for_everyone()
        elif self.config.trainer.get("final_export", True):
            self._save_weights(final)
        if self.accelerator.is_main_process:
            open(os.path.join(self.config.output_dir, "TRAIN_COMPLETE"), "w").write(str(self.completed_steps))

    def _save_state(self, d, n):
        meta = os.path.join(d, "vl_meta.json")
        if self.accelerator.is_main_process and os.path.exists(meta):
            json.dump({"step": -1, "writing": n}, open(meta, "w"))  # the state is incomplete until the save ends
        self.accelerator.wait_for_everyone()
        self.accelerator.save_state(d)
        self.accelerator.wait_for_everyone()
        if self.accelerator.is_main_process:
            json.dump({"step": n, "world": _world(), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                      open(meta, "w"))
            self._state_gb = _tree_gb(d)
            self._summary({"path": d, "kind": "state", "gb": round(self._state_gb, 2)})

    def _save_checkpoint(self):
        n = self.completed_steps
        if n in self._cfg_list("save_steps"):
            self._save_weights(os.path.join(self.checkpoint_dir, f"steps_{n}_pytorch_model.pt"))
        sdir = os.path.join(self.config.output_dir, "state")
        if n in self._cfg_list("state_steps"):
            self._save_state(os.path.join(sdir, f"steps_{n}"), n)
        every = int(self.config.trainer.get("state_every", 0) or 0)
        if every and n % every == 0 and n < int(self.config.trainer.max_train_steps):
            os.makedirs(sdir, exist_ok=True)
            need = self._need_gb("_state_gb", "state_gb_est", 125)
            ok, free = self._room(sdir, need)
            if not ok:
                self._summary({"state_skipped": n, "free_gb": free, "need_gb": need})
                T.logger.warning(f"rolling state at step {n} skipped: {free} GB free < {need} GB")
                return
            cur = os.path.join(sdir, "current")
            prev = os.path.realpath(cur) if os.path.islink(cur) else None
            d = os.path.join(sdir, f"steps_{n}")
            self._save_state(d, n)
            if self.accelerator.is_main_process:
                tmp = cur + ".tmp"
                if os.path.lexists(tmp):
                    os.remove(tmp)
                os.symlink(os.path.basename(d), tmp)
                os.replace(tmp, cur)  # atomic: current names a complete state before and after this line
                keep = {os.path.realpath(os.path.join(sdir, f"steps_{s}")) for s in self._cfg_list("state_steps")}
                if prev and prev != os.path.realpath(d) and prev not in keep and os.path.dirname(prev) == os.path.realpath(sdir):
                    shutil.rmtree(prev)  # this run's own previous rolling state, superseded by a complete one
                    self._summary({"rolled": n, "removed": prev})
            self.accelerator.wait_for_everyone()


def _tree_gb(d):
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(d) for f in fs) / 2**30


def _gate_norms(model):
    """Norms of the head's zero-initialised input maps (proprio, where): 0 at step 0, growing as the head starts to use them."""
    out = {}
    head = getattr(getattr(model, "action_model", None), "head", None)
    for name in ("proprio", "where"):
        mod = getattr(head, name, None) if head is not None else None
        if mod is not None:
            out[f"gate_{name}"] = float(mod.weight.detach().float().norm())
    return out


def _module_norms(model):
    """Parameter norms per module group (the LM by decoder layer thirds); compare across steps for update size."""
    groups = {}
    for name, p in model.named_parameters():
        if name.startswith("action_model."):
            g = "head"
        elif ".visual." in name:
            g = "vision"
        elif ".layers." in name:
            i = int(name.split(".layers.")[1].split(".")[0])
            g = f"lm_layers_{(i // 11) * 11:02d}"
        else:
            g = "lm_other"
        t = p.ds_tensor if hasattr(p, "ds_tensor") else p
        groups[g] = groups.get(g, 0.0) + float(t.detach().float().pow(2).sum())
    return {g: round(math.sqrt(v), 4) for g, v in sorted(groups.items())}


def _param_sums(model):
    """Cheap fingerprint of the weights: float64 sums of the head and of four named backbone tensors (ZeRO-3 safe on rank 0 only
    when parameters are gathered; under ZeRO-3 the partitioned tensors are summed locally, so compare runs of equal world size)."""
    out = {}
    for name, p in model.named_parameters():
        if name.startswith("action_model.") or name.endswith(("layers.0.mlp.down_proj.weight", "layers.31.mlp.down_proj.weight",
                                                                "embed_tokens.weight", "visual.blocks.0.attn.qkv.weight")):
            t = p.ds_tensor if hasattr(p, "ds_tensor") else p
            out[name] = float(t.detach().sum(dtype=torch.float64))
    head = sum(v for k, v in out.items() if k.startswith("action_model."))
    return {"head": head, **{k: v for k, v in out.items() if not k.startswith("action_model.")}}


T.VLATrainer = Trainer
_orig_build_framework = T.build_framework


def build_framework(cfg):
    """framework.head_hook=<module>:<factory> swaps the action head right after the framework is built, before the
    optimizer's parameter groups exist; factory(model, cfg) returns the model to train (see HEADS_HOOK.md)."""
    from accelerate.utils import set_seed
    set_seed(int(cfg.seed))  # StarVLA seeds only in prepare_training, after the model exists: heads were initialised unseeded
    model = _orig_build_framework(cfg)
    if cfg.trainer.get("gradient_checkpointing", False):
        # StarVLA's Qwen3.5 wrapper ignores trainer.gradient_checkpointing; the kit applies it to the VLM here.
        model.qwen_vl_interface.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.qwen_vl_interface.model.config.use_cache = False
        T.logger.info("gradient checkpointing enabled on the VLM")
    if os.environ.get("VLL_CPU_FP32") == "1" and not torch.cuda.is_available():
        model.float()  # CPU smoke only: there is no CUDA autocast to reconcile the bf16 VLM with the fp32 head
    hook = cfg.framework.get("head_hook", None)
    if hook:
        mod, fn = str(hook).split(":")
        model = getattr(importlib.import_module(mod), fn)(model, cfg)
        T.logger.info(f"head_hook {hook} applied: action_model={type(model.action_model).__name__}")
    return model


T.build_framework = build_framework


def _resolve_resume(cfg):
    r = cfg.trainer.get("resume_state", None)
    if not r:
        return
    if r == "latest":
        cands = [p for p in glob.glob(os.path.join(cfg.run_root_dir, cfg.run_id, "state", "*", "vl_meta.json"))
                 if json.load(open(p)).get("step", -1) > 0]
        cands = sorted(cands, key=lambda p: json.load(open(p))["step"])
        if not cands:
            T.logger.warning("resume_state=latest but no complete state; starting fresh")
            return
        r = os.path.dirname(cands[-1])
    meta = json.load(open(os.path.join(r, "vl_meta.json")))
    if meta["world"] != _world():
        raise SystemExit(f"state {r} was saved with world {meta['world']}, now {_world()}")
    RESUME.update(step=int(meta["step"]), path=r)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--config_yaml", required=True)
    args, rest = ap.parse_known_args()
    cfg = OmegaConf.merge(OmegaConf.load(args.config_yaml), OmegaConf.from_dotlist(normalize_dotlist_args(rest)))
    cfg = apply_config_compat(cfg)
    cfg.config_yaml = args.config_yaml
    _resolve_resume(cfg)
    T.main(cfg)
