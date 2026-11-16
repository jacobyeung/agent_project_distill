# vla_heads: action heads that turn the student VLM into a VLA

Pure PyTorch (no StarVLA, no simulator). One interface covers three heads, so the head type is a
config value: (a) `regression`, an OFT-style parallel head; (b) `flow`, an action expert trained by
flow matching or DDPM/DDIM; (c) `tokens`, action tokens the LM writes (uniform bins, DCT, FAST,
VLA-0 digits or navigation text). A `cond` switch adds the model's own spatial outputs.
`VLAPolicy` joins a backbone adapter, the cond projector and one head behind `loss(batch)` and
`predict(batch)`.

Interface version: `vla_heads_interface_v2` (`vla_heads.INTERFACE_VERSION`). The cross-lane
contracts (where layout, run-spec mapping, nav grammar) are PROVISIONAL until the revised design
record publishes one typed schema; the internals and tests below do not depend on it.

## Environment and tests

```bash
cd /scratch/jjyeung/orch_cd/vla_heads
source work/vla_heads/env.sh   # CPU only; the tree's CPU-gate interpreter (envs/p1cpu) and packages
python -m pytest work/vla_heads/tests -q
python work/vla_heads/examples/train_step.py --cond both        # one step per head on the tiny student
python work/vla_heads/examples/overfit.py                       # toy overfit + bimodal toy (stub backbone)
python -m vla_heads.params                                      # parameter table at hidden 4096
```

`env.sh` puts the package, the integ_v3 tree (`VLA_TREE`) and the environment's site-packages on
`PYTHONPATH`. Dependencies: torch, transformers (Qwen3.5 classes), numpy, `tokenizers` (FAST BPE),
peft (only for `train_mode=lora`), scipy (only one test, to pin the FAST formula).

## Layout

| Module | Contents |
|---|---|
| `config.py` | `VLAConfig`: every key below, validation, `from_dict` (rejects unknown keys), `from_spec` (design-record run spec), `sha256()` |
| `interface.py` | `HeadInputs`, `ActionHead` |
| `heads/regression.py`, `heads/flow.py`, `heads/tokens.py` | (a) `RegressionHead`, (b) `FlowExpert`, (c) `TokensHead` |
| `codecs/` | `UniformBins`, `DCTCodec`, `FastCodec`, `DigitsCodec`, `nav_text`, `reserved` (rare-id maps) |
| `cond.py` | cond tensor contracts, `where_features`, `G3TProjector`, `ReadoutProjector`, `CondProjector` |
| `adapters/` | `BackboneBase` (contract), `StubBackbone` (tests), `StudentAdapter` (the tree's Qwen3.5 student) |
| `policy.py` | `VLAPolicy` |
| `utils/` | `Normalizer`, gripper maps, `make_chunks`, `TemporalEnsembler`, `ChunkExecutor`, `ProprioEncoder`, `warmup_cosine` |
| `data.py`, `checkpoint.py` | `EpochSampler`; `save_checkpoint` / `load_checkpoint` |
| `params.py`, `testing.py`, `toy.py` | parameter counts (meta device); CPU fixtures (tiny native Qwen3.5); toy tasks |

## The head interface

Batch first. B batch, T LM context, D LM width, n taps, N cond tokens, Dc = `cond_dim`, E = where
entities (18 features each), P = `proprio_dim`, K = `chunk`, A = `action_dim`, Q appended positions.

`HeadInputs(lm_states [B,T,D], lm_mask [B,T], query_states [B,Q,D]?, cond_tokens [B,N,Dc]?,
cond_mask [B,N]?, proprio [B,P]?, decoder?, tap_states [n,B,T,D]?, where [B,E,18]?, where_mask [B,E]?)`

- `head.loss(inputs, actions [B,K,A], action_mask [B,K] | [B,K,A] | None) -> {'loss': fp32 scalar, 'parts': {name: detached}}`
- `head.predict(inputs) -> [B,K,A]` in the normalised space [-1, 1], dtype of `lm_states`.

Heads compute in their parameter dtype, return fp32 losses, hold no device constants, run in bf16
and build on the meta device. Masks hide padding; a learned null token keeps every attention row
non-empty.

| Head | Reads | Loss | Inference |
|---|---|---|---|
| regression | `query_states`: the last tap at K learnable query tokens appended to the LM input; LN, Linear(D->H), `reg_blocks` residual blocks, Linear(H->A); proprio and where through zero-init maps, cond tokens through zero-init cross-attention | L1 | one forward |
| flow | each tap in `taps` (LN, Linear(D->W), tap embedding) + cond + where tokens as cross-attention context; self-attention over [proprio token] + K action tokens; time by concat (pi0) or adaLN | `flow`: openpi convention, x_tau = tau eps + (1 - tau) a, target u = eps - a, tau ~ Beta(1.5, 1); `ddpm`: cosine schedule, target eps (or x0 with `ddpm_prediction=sample`) | Euler from tau = 1 or DDIM eta 0, `flow_steps` steps |
| tokens | `query_states[:, j]`: the LM state that predicts codec symbol j (teacher forcing) | cross-entropy, full vocabulary or codec ids only | the LM writes symbols greedily, constrained to codec ids, until the end symbol, the fixed length or `tok_max_tokens`; an unparsable row decodes to zeros with `head.last_ok[row]` False |

Gradient paths. `detach_backbone=True` (flow only) detaches the expert's inputs: the flow loss sends
exactly zero gradient into the LM (tested). With `lm_token_loss=<codec>` the policy adds the codec's
token loss on the same chunk; that loss still trains the LM, so knowledge insulation keeps the LM
trainable, not unchanged, and how much spatial skill it retains is unmeasured. Flow and regression
also differ in objective and gradient path, not only in head size.

## The policy and the LM input layout

```
[left-padded context] [cond and where tokens if cond_inject=lm] [proprio token if proprio_inject=lm] [head block]
head block: regression = K query embeddings; tokens = the chunk's codec ids except the last (training);
            flow with lm_token_loss = the same codec ids (training only)
```

The adapter left-pads every row, so the appended block occupies the same last columns of every row.
The flow head reads only prefix positions, which causal attention keeps independent of the appended
codec ids. The tokens head always reads cond and proprio through the LM.

Step-0 parity. Every cond path ends in a zero-initialised layer and is built under a forked RNG, so
with `cond_inject=head` and identical LM tokens a cond arm's first prediction equals the no-cond
arm's exactly (tested). With `cond_inject=lm` the LM attends to the extra (zero-valued) tokens:
context states stay equal, predictions do not (tested). A prompt that adds text changes the input,
so an arm with extra text need not equal one without it at step 0.

### Batch keys

| Key | Shape | Needed when |
|---|---|---|
| `input_ids`, `attention_mask` | [B, T] | always (processor output; any contiguous padding) |
| `pixel_values`, `image_grid_thw` / `pixel_values_videos`, `video_grid_thw`, `mm_token_type_ids` | processor output | StudentAdapter with images; `mm_token_type_ids` is derived when absent |
| `proprio` | [B, P] normalised | `proprio_dim > 0` |
| `cond` | dict (below) | `cond != none` |
| `actions` | [B, K, A] normalised | `loss` |
| `action_mask` | [B, K] or [B, K, A] bool | optional; False marks steps past an episode end |

### Trainer

```python
from vla_heads import VLAConfig, VLAPolicy, StudentAdapter, Normalizer, make_chunks, EpochSampler, \
    save_checkpoint, load_checkpoint, warmup_cosine
cfg, rest = VLAConfig.from_spec(run_spec)                     # or VLAConfig.from_dict(flat_dict)
adapter = StudentAdapter.from_pretrained(base_dir, cfg)        # B0: base Qwen3.5-9B, bf16
adapter = StudentAdapter.from_export(base_dir, milestone_dir, cfg)   # B1: student full-weights export
policy = VLAPolicy(cfg, adapter).cuda()                       # sets requires_grad per train_mode / train_vision
norm = Normalizer.fit(train_actions, skip=[6], subset_sha=sha); norm.save(run_dir / 'action_norm.json')
chunks, mask = make_chunks(norm.normalize(episode_actions), cfg.chunk)
opt = torch.optim.AdamW([p for p in policy.parameters() if p.requires_grad], lr=lr)
sched = torch.optim.lr_scheduler.LambdaLR(opt, warmup_cosine(total_steps))   # warm-up < run, enforced
out = policy.loss(batch); out['loss'].backward(); opt.step(); sched.step()
save_checkpoint(path, policy, opt, sched, step=step, extra={'sampler': sampler.state_dict()})
payload = load_checkpoint(path, policy, opt, sched); sampler.load_state_dict(payload['extra']['sampler'])
```

`policy.module_groups()` splits parameters into vision / lm / codec_rows / head / cond / lm_inject
for separate learning rates. The checkpoint stores trainable tensors plus every non-backbone tensor,
optimizer moments, scheduler, all RNG streams, the config hash and the step; a policy with another
config refuses it. For FAST, fit the codec on the training subset (`FastCodec(...).fit(chunks)`),
`save(path)` it and set `tok_codec_path`; the returned sha256 pins it.

### Closed-loop evaluator

```python
policy.eval(); norm = Normalizer.load(run_dir / 'action_norm.json')
ens = TemporalEnsembler(cfg.chunk, m=0.01)       # or ChunkExecutor(replan=n) for open-loop chunks
ens.reset()                                      # at every episode start
for obs in episode:
    batch = processor_rows(obs) | {'proprio': prop_norm.normalize(state)[None], 'cond': cond}
    chunk = policy.predict(batch)[0]             # [K, A] in [-1, 1]
    action = norm.denormalize(ens.update(chunk))
    action[6] = gripper_from_unit(action[6:7])   # snap to -1 open / +1 close (LIBERO)
```

`policy.predict(batch, noise=..., steps=...)` fixes the flow noise and step count;
`policy.predict(batch, use_cache=False)` re-encodes instead of using the KV cache (tokens head; both
agree to 1e-5 on CPU).

Normalisation and gripper. `Normalizer` maps the training subset's 1st-99th percentiles to [-1, 1]
and clips: values inside the range round-trip exactly, values outside decode to the nearest bound
(tested). `skip` dimensions keep raw values; for LIBERO the gripper (dim 6, -1 open, +1 close) is
skipped and snapped by sign at execution. `gripper_to_unit` / `gripper_from_unit` convert datasets
with 0/1 conventions.

## Conditioning contracts (`cond`)

`none` is the pure backbone swap. The others read `batch['cond']` (full contract in `cond.py`):

| Key | Shape | Meaning / source |
|---|---|---|
| `where`, `where_mask` | [B, E, 18], [B, E] | `spatial_readouts`: the where-provider's entity rows (0 target, 1 place): presence, valid, uv agent and wrist in [0, 1], X_wrist and X_agent (m), size (m), scale-source one-hot [proprio, vc, metric]; invalid rows all zero; dropped for `where_dropout` of training rows |
| `g3t_cam`, `g3t_mask` | [B, V, 2058], [B, V] | `g3t_tokens`: `g3t_online` feature `cam_l23_2048_pose9_disagreement1_v1`: layer-23 frame and global camera tokens (2 x 1024), pose9 relative to frame 0 with mean-radius-normalised translation, then the absolute local yaw (`g3t_online.disagreement`) |
| `g3t_patch` | [B, V, H, W, 2048] | optional, read when `g3t_patch_grid > 0` |
| `pose9`, `depth_grid` or `point_depth` + `point_uv`, `gravity_up`, `step_scale` | see `cond.py` | optional readout tokens under `spatial_readouts` |

The policy does not compute these: the harness supplies them from the provider.

## Backbone adapters

`StudentAdapter(model, taps=(-1,), tap_norm=False)` wraps `student_pilot.students.model_class('qwen35')`
(`Qwen3_5ForConditionalGeneration`) or a `CarrierC1` around it. Appended positions enter as the pad
id, and a forward hook on the input embedding substitutes their embeddings, so M-RoPE, image
placement and the hybrid DeltaNet / full attention run natively.

Taps are one-based decoder-layer numbers. Tap i in [1, L) is the output of
`language_model.layers[i - 1]` before the final norm (transformers' `hidden_states[i]`; `tap_norm`
applies the final norm); tap L or -1 is `last_hidden_state`, after the final norm. For the 32-layer
9B LM the design's taps 16 and 32 are `[16, -1]`. The adapter captures taps with its own forward
hooks and keeps their gradient; it does not share the tree's grounding capture
(`grounding_features.py`, layers 16, 24 and the final norm, detached).

Loading. B0: `from_pretrained(<Qwen3.5-9B snapshot>, cfg)`. B1: `from_export(<base>, <export>, cfg)`
loads the base in bf16 and replaces every base tensor through `student_pilot.full_ft.load_export`
(manifest `full_weights.json`, each file verified); a milestone directory is first verified by
`full_ft.read_milestone` (tested on the tiny model with the tree's own `save_export`). The VLA reads
the LM and vision tower only: `auxiliary_heads.pt`, `geometry/`, MDG artifacts
(`mdg_decode_attach.attach_mdg`) and the routed decoder are not used.

Codec ids (`tok_ids`): `append` adds n new embedding and output rows after the vocabulary
(Qwen3.5-9B: from 248,320); a path loads a reserved-id JSON such as
`out/qwen35_9b_c2022362_rare_ids_1025.json` (the 1,025 rarest non-special, non-digit ids, sha inside).
`train_mode`: `full` trains the LM and LM head; `lora` injects peft LoRA into the LM decoder layers;
`frozen` trains no LM weight. `train_vision` also trains the vision tower. Heads, projectors and
appended rows always train.

## Codecs (`tok_codec`, also `lm_token_loss`)

| Codec | Symbols | Round trip |
|---|---|---|
| `bins` | K A values, time-major, `tok_bins` uniform bins over [-1, 1] | max error <= 1 / bins |
| `dct` | round(scale DCT-II_ortho(chunk over time)), first `tok_dct_keep` frequencies, frequency-major, clipped to +-`tok_dct_clip` | max error <= sqrt(K) 0.5 / scale (keep = K, no clip) |
| `fast` | `dct` integers, then BPE (HF `tokenizers`) to `tok_vocab` symbols, variable length + end symbol | as `dct` |
| `digits` | VLA-0: integers 0..resolution as text through the LM's own tokenizer | <= 1 / resolution |
| `nav` | navigation text, "forward 0.50, turn_left 30" (grammar provisional) | exact |

FAST is pinned to physical-intelligence/fast `processing_action_tokenizer.py`: the integer stream
equals `round(scale * scipy.fft.dct(chunk, axis=time, norm='ortho')).flatten()` and the inverse uses
`idct` (tested). Differences, by design: integers are offset by +clip (FAST subtracts the fitted
minimum) and clipped; integer i maps to `chr(0x4E00 + i)` under a plain BPE model (FAST uses
`ByteLevelBPETokenizer`); a wrong-length decode pads or truncates and flags the row (FAST returns
zeros). Token ids therefore differ from the official files; the BPE is fitted per training subset.

## Config keys and defaults

| Key | Default | Meaning |
|---|---|---|
| `head` | `regression` | `regression` \| `flow` \| `tokens` (aliases `generative`, `diffusion`, `discrete`) |
| `action_dim`, `chunk` | 7, 8 | A, K |
| `hidden_size` | 4096 | D; must equal the backbone width |
| `proprio_dim`, `proprio_inject` | 8, `head` | P (0 disables); `head` \| `lm` (one projected token) |
| `taps`, `tap_norm` | `[]`, false | one-based LM layers, -1 = last; `[]` = `[16, -1]` for flow, `[-1]` otherwise; final norm on lower taps |
| `detach_backbone` | false | flow only: the expert sends no gradient into the LM |
| `lm_token_loss`, `lm_token_weight` | `none`, 1.0 | flow only: a codec the LM also writes, and its loss weight |
| `cond`, `cond_dim`, `cond_inject` | `none`, 1024, `head` | cond mode; cond token width; `head` \| `lm` |
| `where_entities`, `where_features`, `where_dropout` | 2, 18, 0.2 | where rows (target, place); fixed 18; training dropout share |
| `max_views` | 32 | V limit |
| `g3t_cam_dim`, `g3t_patch_dim`, `g3t_patch_grid` | 2058, 2048, 0 | G3T widths; pooled patch grid (0 = camera tokens only) |
| `readout_depth_grid`, `readout_hidden` | 4, 256 | readout projector |
| `reg_hidden`, `reg_blocks`, `reg_block`, `reg_act` | 1024, 2, `mlp2`, `gelu` | regression MLP; `oft` blocks reproduce StarVLA's L1 head |
| `reg_input_act`, `reg_final_norm`, `reg_cond_heads` | false, false, 8 | OFT options; cond cross-attention heads |
| `flow_layers`, `flow_width`, `flow_heads`, `flow_mlp_ratio`, `flow_dropout` | 8, 1024, 16, 4.0, 0.0 | expert size |
| `flow_objective`, `flow_time_dist`, `flow_time_cond`, `flow_steps` | `flow`, `beta`, `concat`, 10 | `flow` \| `ddpm`; `beta` \| `uniform` \| `logit_normal`; `concat` \| `adaln`; sampler steps |
| `ddpm_train_steps`, `ddpm_clip_sample`, `ddpm_prediction` | 100, true, `epsilon` | cosine schedule length (>= `flow_steps`); clip x0; `epsilon` \| `sample` |
| `tok_codec`, `tok_vocab`, `tok_bins` | `fast`, 1024, 256 | codec; FAST BPE vocabulary; bins |
| `tok_dct_scale`, `tok_dct_keep`, `tok_dct_clip` | 10.0, 0, 127 | DCT quantisation (keep 0 = all K) |
| `tok_max_tokens`, `tok_ids`, `tok_ce`, `tok_codec_path` | 64, `append`, `full`, `''` | decode cap; id source; CE scope; fitted codec file |
| `train_mode`, `train_vision` | `full`, false | `full` \| `lora` \| `frozen` |
| `lora_rank`, `lora_alpha`, `lora_dropout`, `lora_targets` | 32, 64, 0.05, q/k/v/o, gate/up/down, in_proj_qkv, in_proj_z, out_proj | LoRA |

`VLAConfig.from_spec(spec)` maps the design record's nested spec (`vla.head.type`,
`vla.head.flow.taps`, `vla.head.tokens.codec`, ...) onto these keys and returns the other sections
untouched.

## Parameter counts at Qwen3.5-9B width (hidden 4096; meta device, no weights)

New parameters only; the 9B backbone is unchanged. "new LM rows" are appended codec embedding and
output rows (`tok_ids=append`).

| Head | cond | head | cond projector | LM injection | new LM rows | total new |
|---|---|---:|---:|---:|---:|---:|
| (a) regression, H 1024 (design) | none | 8,455,175 | 0 | 0 | 0 | 8,455,175 |
| (a) regression, H 1024 (design) | spatial_readouts | 13,744,135 | 1,099,068 | 0 | 0 | 14,843,203 |
| (a) regression, H 1024 (design) | g3t_tokens | 13,706,247 | 2,145,300 | 0 | 0 | 15,851,547 |
| (a) regression, H 1024 (design) | both | 13,744,135 | 3,244,368 | 0 | 0 | 16,988,503 |
| (a) regression, StarVLA OFT (H 8192) | none | 168,017,927 | 0 | 0 | 0 | 168,017,927 |
| (a) regression, StarVLA OFT (H 8192) | spatial_readouts | 445,210,631 | 1,099,068 | 0 | 0 | 446,309,699 |
| (a) regression, StarVLA OFT (H 8192) | g3t_tokens | 444,907,527 | 2,145,300 | 0 | 0 | 447,052,827 |
| (a) regression, StarVLA OFT (H 8192) | both | 445,210,631 | 3,244,368 | 0 | 0 | 448,454,999 |
| (b) flow, 8 x 1024, taps 16+32 | none | 145,974,279 | 0 | 0 | 0 | 145,974,279 |
| (b) flow, 8 x 1024, taps 16+32 | spatial_readouts | 147,045,383 | 1,099,068 | 0 | 0 | 148,144,451 |
| (b) flow, 8 x 1024, taps 16+32 | g3t_tokens | 147,025,927 | 2,145,300 | 0 | 0 | 149,171,227 |
| (b) flow, 8 x 1024, taps 16+32 | both | 148,094,983 | 3,244,368 | 0 | 0 | 151,339,351 |
| (b) flow, 8 x 1024, + FAST LM loss | none | 145,974,279 | 0 | 0 | 8,396,800 | 154,371,079 |
| (b) flow, 8 x 1024, + FAST LM loss | spatial_readouts | 147,045,383 | 1,099,068 | 0 | 8,396,800 | 156,541,251 |
| (b) flow, 8 x 1024, + FAST LM loss | g3t_tokens | 147,025,927 | 2,145,300 | 0 | 8,396,800 | 157,568,027 |
| (b) flow, 8 x 1024, + FAST LM loss | both | 148,094,983 | 3,244,368 | 0 | 8,396,800 | 159,736,151 |
| (b) flow, 16 x 1024 (large) | none | 280,364,039 | 0 | 0 | 0 | 280,364,039 |
| (b) flow, 16 x 1024 (large) | spatial_readouts | 281,435,143 | 1,099,068 | 0 | 0 | 282,534,211 |
| (b) flow, 16 x 1024 (large) | g3t_tokens | 281,415,687 | 2,145,300 | 0 | 0 | 283,560,987 |
| (b) flow, 16 x 1024 (large) | both | 282,484,743 | 3,244,368 | 0 | 0 | 285,729,111 |
| (c) tokens, FAST 1024 | none | 0 | 0 | 1,054,976 | 8,396,800 | 9,451,776 |
| (c) tokens, FAST 1024 | spatial_readouts | 0 | 1,099,068 | 1,132,800 | 8,396,800 | 10,628,668 |
| (c) tokens, FAST 1024 | g3t_tokens | 0 | 2,145,300 | 5,253,376 | 8,396,800 | 15,795,476 |
| (c) tokens, FAST 1024 | both | 0 | 3,244,368 | 5,331,200 | 8,396,800 | 16,972,368 |
| (c) tokens, 256 bins | none | 0 | 0 | 1,054,976 | 2,097,152 | 3,152,128 |
| (c) tokens, 256 bins | spatial_readouts | 0 | 1,099,068 | 1,132,800 | 2,097,152 | 4,329,020 |
| (c) tokens, 256 bins | g3t_tokens | 0 | 2,145,300 | 5,253,376 | 2,097,152 | 9,495,828 |
| (c) tokens, 256 bins | both | 0 | 3,244,368 | 5,331,200 | 2,097,152 | 10,672,720 |

## Toy evidence (CPU)

Overfit of 64 synthetic (state, chunk) pairs on the stub backbone (width 64; K = 4, A = 7), full-batch AdamW, single process on a loaded node (`tests/test_training.py`, 2026-11-11):

| Head | Steps | Final loss | mean / max abs error | Bound (mean / max) | Time |
|---|---:|---:|---:|---|---:|
| regression (L1) | 400 | 0.018 | 0.020 / 0.098 | 0.03 / 0.15 | 7 s |
| flow (10 Euler steps) | 1500 | 0.045 | 0.047 / 0.339 | 0.08 / 0.40 | 34 s |
| ddpm, epsilon (10 DDIM steps) | 1500 | 0.020 | 0.055 / 1.10 (q99 0.36) | 0.08 / q99 0.40 | 37 s |
| ddpm, x0 (`ddpm_prediction=sample`) | 1500 | 0.000 | 0.004 / 0.019 | 0.02 / 0.10 | 35 s |
| tokens, bins (32) | 400 | 0.001 | 0.016 / 0.031 | 0.03 / 1/32 | 17 s |
| tokens, dct (scale 20) | 400 | 0.001 | 0.012 / 0.042 | 0.03 / 0.08 | 18 s |
| tokens, fast (BPE, scale 20) | 500 | 0.001 | 0.012 / 0.042 | 0.03 / 0.08 | 24 s |

Epsilon prediction recovers x0 as (x - sqrt(1 - ab) eps) / sqrt(ab), which multiplies the eps error by up to 1 / sqrt(ab) (about 2000 at the last cosine step); a few of 1,792 elements stay wrong, so that case bounds the 99th percentile. x0 prediction on the same setup has max error 0.02.

Bimodal toy (each state's chunk is +m or -m with equal odds, 32 samples per state): the flow expert puts 0.90 of its samples within 0.15 of a mode and draws the minority mode 0.34 of the time (mean distance to the nearest mode 0.10); the L1 regression head puts none near a mode (distance 0.99: it predicts the conditional median between the modes).

First batch through the tiny native Qwen3.5 student (2 hybrid layers, width 32, real vocabulary; `examples/train_step.py --cond both`, one AdamW step): regression loss 0.690 (grad norm LM 0.91, head 3.12); flow 1.865 (LM 1.65, head 4.65, cond 1.60); tokens 12.43 CE over the full vocabulary (LM 0.17, codec rows 1.50, LM injection 7.19); flow with `detach_backbone` + bins LM loss 14.29 (flow 1.86 + CE 12.43; the LM gradient 0.17 comes from the token loss only). Every head and cond value passes forward, loss, backward, step and predict in `tests/test_student.py`.
