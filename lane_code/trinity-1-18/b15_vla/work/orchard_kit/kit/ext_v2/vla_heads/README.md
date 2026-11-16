# vla_heads: action heads that turn the student VLM into a VLA

Pure PyTorch (no StarVLA, no simulator). One interface covers three heads, so the head type is a
config value: (a) `regression`, StarVLA's QwenOFT L1 head (the default); (b) `flow`, an action expert
trained by flow matching or DDPM/DDIM; (c) `tokens`, action tokens the LM writes (FAST, uniform bins,
DCT or VLA-0 digits; navigation text uses the LM's ordinary text). A `cond` switch adds the model's own
spatial outputs. `VLAPolicy` joins a backbone adapter, the cond projector and one head behind
`loss(batch)` and `predict(batch)`.

The package implements `vla_schema_v2` (`vla_heads.SCHEMA`; `/scratch/jjyeung/orch_cd/vla_design_review/VLA_SCHEMA.md`)
sections 1-3, 7 and 8.1, with interface `vla_heads_interface_v2` (`vla_heads.INTERFACE_VERSION`). The schema wins
over this file where they differ.

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
`PYTHONPATH`. Dependencies: torch, transformers (Qwen3.5 classes; FAST's `PreTrainedTokenizerFast`),
numpy, scipy and `tokenizers` (FAST), peft (only for `train_mode=lora`).

Conformance tests owned here (schema 12): T-2, T-12 and the head side of T-1 (`tests/test_schema_conformance.py`,
expected values from the schema's own generators, vendored by sha256 in `tests/fixtures/schema_v2/`),
T-5 (`test_tokens_actions.py::test_t5_action_normalisation_and_gripper`), T-8 (`test_heads.py::test_t8_invalid_taps_raise`,
`test_student.py::test_t8_taps_on_the_student`), T-9 (`test_heads.py::test_t9_gated_cond_leaves_step0_unchanged`,
`test_training.py::test_detach_with_lm_token_loss`).

## Layout

| Module | Contents |
|---|---|
| `config.py` | `VLAConfig`: every key below, validation, `from_dict` (rejects unknown keys), `from_spec` (the schema-10 `vla:` tree), `sha256()` |
| `interface.py` | `HeadInputs` (v2), `ActionHead` |
| `heads/regression.py`, `heads/flow.py`, `heads/tokens.py` | (a) `RegressionHead`, (b) `FlowExpert`, (c) `TokensHead` |
| `codecs/` | `FastCodec` (calls the vendored reference `fast_reference.py`), `UniformBins`, `DCTCodec`, `DigitsCodec`, `nav_text` (`nav_grammar_v1`), `reserved` (rare-id maps) |
| `cond.py` | cond tensor contracts, `where_features`, `withheld_draw`, `G3TProjector`, `ReadoutProjector`, `CondProjector` |
| `adapters/` | `BackboneBase` (contract, taps), `StubBackbone` (tests), `StudentAdapter` (the tree's Qwen3.5 student) |
| `policy.py` | `VLAPolicy`, `QUERY_TOKEN`, `query_token_id`, `query_positions` |
| `utils/` | `Normalizer` (`minmax_subset_v1`), gripper maps, `make_chunks`, `TemporalEnsembler`, `ChunkExecutor`, `ProprioEncoder`, `warmup_cosine` |
| `data.py`, `checkpoint.py` | `EpochSampler`; `save_checkpoint` / `load_checkpoint` |
| `params.py`, `testing.py`, `toy.py` | parameter counts (meta device); CPU fixtures (tiny native Qwen3.5); toy tasks |

## The head interface (schema 1-3)

B batch, T tokens, K = 8, A = 7, D = 4096 (LIBERO, Qwen3.5-9B).

| Name | Shape | Dtype | Meaning |
|---|---|---|---|
| `query_states` | [B, 8, D] | bf16 | tap -1 at the prompt's 8 query tokens (regression) |
| `lm_states`, `lm_mask` | [B, T, D], [B, T] | bf16, bool | the last configured tap over all positions; True = real token (left padding False) |
| `tap_states` | [n_taps, B, T, D] | bf16 | every configured tap in config order (flow) |
| `cond_tokens`, `cond_mask` | [B, N, 1024], [B, N] | fp32, bool | projected G3T / readout tokens (`cond: g3t_tokens` or `both` only) |
| `where`, `where_mask` | [B, 2, 18], [B, 2] | fp32, bool | where records after dropout; mask = valid AND NOT withheld |
| `proprio` | [B, 8] | fp32 | normalised proprioception |
| `actions`, `action_mask` | [B, 8, 7], [B, 8] | fp32, {0, 1} | normalised targets; 0 = step past the episode end |

- `head.loss(inputs, actions, action_mask) -> {'loss': fp32 scalar, 'parts': {name: detached}}`; the loss averages over unmasked entries.
- `head.predict(inputs) -> fp32 [B, 8, 7]` normalised actions, clipped to [-1, 1].
- Heads cast inputs to fp32 at their first LayerNorm (the backbone runs under bf16 autocast) and build on the meta device. Masks hide padding; learned null tokens keep every attention row non-empty.

| Head | Reads | Loss | Inference |
|---|---|---|---|
| regression (default, `reg_arch: starvla_oft_985c2238`) | `query_states`; LayerNorm, Linear 4096->8192, ReLU, two blocks x + ReLU(Linear(LN(x))), LayerNorm, Linear 8192->7 per query (StarVLA 985c2238 `L1RegressionActionHead`, pinned by `tests/test_parity_starvla.py`); proprio Linear(8->8192) and where Linear(36->8192) zero-initialised after the first projection; G3T tokens through a zero-initialised cross-attention | L1 | one forward; the robot executes all 8 open loop |
| flow | each tap (default [16, -1]): LayerNorm, Linear(4096->1024), tap embedding; 8 layers of self-attention over [proprio, 8 action tokens], cross-attention to the taps, a tanh-gated (g = 0 at init) cross-attention to the cond context [null, G3T tokens, where tokens], 4x MLP | `flow`: openpi convention, x_tau = tau eps + (1 - tau) a, target eps - a, tau = 0.001 + 0.999 Beta(1.5, 1); `ddpm`: cosine schedule, target eps (or x0 with `ddpm_prediction=sample`) | 10 Euler steps from tau = 1, or DDIM eta 0 |
| tokens | `query_states[:, j]` = tap -1 at position p - 1 + j, the state that predicts symbol j + 1 (teacher forcing; p = prefix length); no cond, where, proprio or tap_states in HeadInputs (they reach the LM as prefix tokens) | cross-entropy in fp32 over the full vocabulary against the bound ids, averaged over `symbol_mask` | greedy, restricted to the bound ids, until the end symbol, the fixed length (bins) or `max_tokens`; a row that does not decode to [8, 7] returns zeros with `head.last_ok[row]` False; the evaluator re-queries once, then executes one chunk of zero deltas with the previous gripper command |

Taps (schema 2). l in 1..31 is the output of decoder layer l (residual stream before the final RMSNorm),
captured by a differentiable forward hook on `model.model.language_model.layers[l - 1]`; -1 is
`last_hidden_state` (layer 32 after the final norm). 0 and 32 raise, in `VLAConfig` (via `lm_layers`) and
in the adapter; nothing remaps 32. Defaults: regression and tokens [-1], flow [16, -1]. `tap_norm` also
applies the final norm to lower taps. This capture is separate from the tree's detached grounding capture.

Gradient paths. `detach_backbone: true` (flow) passes `HeadInputs.detached()` to the head: the flow loss
sends exactly zero gradient into the LM, while `lm_token_loss: fast` (the F1 arm) adds the FAST token loss
on the same chunk, which does train the LM (T-9). How much spatial skill the LM keeps is unmeasured.

Step-0 parity (T-9). Every cond branch is zero-initialised (regression) or tanh-gated at 0 (flow) and built
under a forked RNG, so with `cond_inject: head` and identical LM tokens a cond arm's first prediction equals
the no-cond arm's bit for bit and every shared parameter starts equal. A prompt that adds text (U1's where
line) changes the input, so U1 need not equal B1 at step 0; `cond_inject: lm` (flow only) changes
predictions too (tested).

## The policy

```
LM input: [left-padded prompt with its 8 query tokens] [flow/tokens only: cond and where tokens if cond_inject=lm,
           proprio token if proprio_inject=lm] [tokens head, or flow with lm_token_loss: the chunk's codec ids (training)]
```

- The regression head appends nothing and learns no query embeddings: `VLAPolicy(cfg, adapter, query_token_id=...)`
  (or `tokenizer=`, through `query_token_id(tokenizer)`, which requires `QUERY_TOKEN * 8` (🔍) to tokenize to 8 copies
  of one id) gathers tap -1 at the last 8 positions holding that id (StarVLA's `_gather_action_token_embeddings`).
  A row with fewer than 8 raises. LM injection is refused for regression, since injected tokens would follow the queries.
- The tokens head always reads cond and proprio through the LM. The flow head reads only prefix positions, which causal
  attention keeps independent of appended codec ids.
- `cfg.lm_layers` must equal the backbone's layer count (32 for Qwen3.5-9B).

### Batch keys

| Key | Shape | Needed when |
|---|---|---|
| `input_ids`, `attention_mask` | [B, T] | always (the prompt of schema 4, from the shared builder; any contiguous padding) |
| `pixel_values`, `image_grid_thw` / video keys, `mm_token_type_ids` | processor output | StudentAdapter with images; `mm_token_type_ids` is derived when absent |
| `proprio` | [B, 8] normalised | `proprio_dim > 0` |
| `cond` | dict (below) | `cond != none` |
| `actions`, `action_mask` | [B, 8, 7], [B, 8] | `loss` |

### Trainer

```python
from vla_heads import VLAConfig, VLAPolicy, StudentAdapter, Normalizer, gripper_to_unit, make_chunks, \
    EpochSampler, save_checkpoint, load_checkpoint, warmup_cosine, query_token_id
cfg, rest = VLAConfig.from_spec(yaml.safe_load(open(arm_yaml)))      # the schema-10 tree; rest = other sections
adapter = StudentAdapter.from_pretrained(base_dir, cfg)               # B0: Qwen3.5-9B@c2022362, bf16
adapter = StudentAdapter.from_export(base_dir, milestone_dir, cfg)    # B1/U1: the export's full_weights
policy = VLAPolicy(cfg, adapter, tokenizer=tok).cuda()                # query id from the tokenizer; sets requires_grad
actions[:, 6] = gripper_to_unit(actions[:, 6], 'ipec')               # IPEC a6 (1 = open) -> g = 1 - 2 a6
norm = Normalizer.fit(train_actions, dims=6, subset_sha=sha); norm.save(run_dir / 'action_norm.json')
prop_norm = Normalizer.fit(train_proprio, subset_sha=sha); prop_norm.save(run_dir / 'proprio_norm.json')
chunks, mask = make_chunks(norm.normalize(episode_actions), cfg.chunk)    # mask 0 past the episode end
batch['cond'] = {'where': where, 'episode': episode_ids, 't': ts}     # U1: training draws the sha256 dropout
g = policy.module_groups()
opt = torch.optim.AdamW([{'params': [p for p in g['lm'] + g['codec_rows'] if p.requires_grad], 'lr': 3e-5},
                         {'params': g['head'] + g['cond'] + g['lm_inject'], 'lr': 3e-4}], betas=(0.9, 0.95))
sched = torch.optim.lr_scheduler.LambdaLR(opt, warmup_cosine(steps, floor=min_lr / lr))   # warm-up 3 %
out = policy.loss(batch); out['loss'].backward(); opt.step(); sched.step()
save_checkpoint(path, policy, opt, sched, step=step, extra={'sampler': sampler.state_dict()})
```

`policy.module_groups()` splits parameters into vision / lm / codec_rows / head / cond / lm_inject for
separate learning rates; `policy.gate_norms()` reports the zero-initialised maps and the flow gates. The
checkpoint stores trainable tensors plus every non-backbone tensor, optimizer moments, scheduler, all RNG
streams, the config hash and the step; a policy with another config refuses it. For FAST, fit the codec
on the training subset (`FastCodec(...).fit(chunks)`), `save(path)` it and set `tok_codec_path`.

### Closed-loop evaluator

```python
policy.eval(); norm = Normalizer.load(run_dir / 'action_norm.json'); prop_norm = Normalizer.load(...)
batch = prompt_rows(obs) | {'proprio': prop_norm.normalize(raw_proprio, clip=True)[None], 'cond': cond}
chunk = policy.predict(batch)[0]                 # fp32 [8, 7], normalised
action = norm.denormalize(chunk)                 # clips y to [-1, 1] first; dim 6 passes through
action[:, 6] = gripper_command(action[:, 6])     # +1 close if g >= 0, else -1 open
# execute all 8 actions open loop, then query again (schema 7: no temporal ensembling)
```

`cond['withheld'] = torch.ones(B, dtype=bool)` gives the `withheld` evaluation condition.
`policy.predict(batch, noise=..., steps=...)` fixes the flow noise and step count. `TemporalEnsembler`
and `ChunkExecutor(replan=n)` remain available for other evaluators.

### Actions, proprio, normalisation, gripper (schema 7)

- `Normalizer` (`minmax_subset_v1`, JSON {kind, min, max, count, subset_sha}) maps the training subset's
  per-dimension min-max to [-1, 1] on its first len(min) dims and passes later dims through. Actions use
  dims 0-5; the gripper g (dim 6) is not normalised. `normalize` does not clip by default (training values
  lie inside), `denormalize` clips y to [-1, 1] by default; proprio uses all 8 dims and `normalize(x, clip=True)`
  at evaluation. Constant dims map to 0 and decode to min.
- Gripper: canonical g = -1 open, +1 close. `gripper_to_unit(a6, 'ipec') = 1 - 2 a6`,
  `gripper_from_unit(g, 'ipec') = (1 - g) / 2`, `'unit_open_neg'` is the identity, and
  `gripper_command(g)` = +1 (close) if g >= 0 else -1, equal to StarVLA's client for every g, the tie g = 0 included.

## Conditioning contracts (`cond`)

`none` is the pure backbone swap. The others read `batch['cond']` (full contract in `cond.py`):

| Key | Shape | Meaning / source |
|---|---|---|
| `where`, `where_mask` | [B, 2, 18], [B, 2] | `spatial_readouts` (U1), `both`: vla_where's records (schema 5.2; 0 target, 1 place): presence, valid, uv_agent, uv_wrist (uv01), X_wrist (m, wrist camera), reach_base (m, base axes), size (m), scale_source one-hot [proprio_handeye, vc_ratio, metric_test]; valid = 0 rows are zero; valid uv-only rows (scale unknown) have cols 6-17 zero |
| `withheld` | [B] bool | optional: withhold these chunks in any mode (evaluation `withheld`) |
| `episode`, `t` | B strings, [B] | training with `where_dropout > 0`: chunk withheld iff int(sha256(f"{seed}:{episode}:{t}")[:8], 16) / 16^8 < 0.2 (seed `where_seed` = 17) |
| `g3t_cam`, `g3t_mask` | [B, V, 2058], [B, V] | `g3t_tokens`, `both`: `g3t_online` feature `cam_l23_2048_pose9_disagreement1_v1` (layer-23 frame and global camera tokens, pose9 relative to frame 0, absolute local yaw) |
| `g3t_patch` | [B, V, H, W, 2048] | optional, read when `g3t_patch_grid > 0` |
| `pose9`, `depth_grid` or `point_depth` + `point_uv`, `gravity_up`, `step_scale` | see `cond.py` | optional readout tokens under `both` |

`where_vector: false` (schema `vla.where.vector`) drops the vectors, leaving U1's text line only. The policy
does not compute these tensors: the harness supplies them from the provider.

## Backbone adapters

`StudentAdapter(model, taps=(-1,), tap_norm=False)` wraps `student_pilot.students.model_class('qwen35')`
(`Qwen3_5ForConditionalGeneration`) or a `CarrierC1` around it. Appended positions (flow and tokens heads
only) enter as the pad id, and a forward hook on the input embedding substitutes their embeddings, so
M-RoPE, image placement and the hybrid DeltaNet / full attention run natively. `padded_ids(batch)` returns
the ids in the adapter's left-padded layout.

Loading. B0: `from_pretrained(<Qwen3.5-9B snapshot>, cfg)`. B1: `from_export(<base>, <export>, cfg)` loads
the base in bf16 and replaces every base tensor through `student_pilot.full_ft.load_export` (manifest
`full_weights.json`, each file verified); a milestone directory is first verified by
`full_ft.read_milestone`. The VLA reads the LM and vision tower only: `auxiliary_heads.pt`, `geometry/`,
MDG artifacts and the routed decoder are not used.

Codec ids (`tok_ids`): `append` adds n new embedding and output rows after the vocabulary; a path loads a
reserved-id JSON such as `out/qwen35_9b_c2022362_rare_ids_1025.json` (1,024 FAST symbols + end; sha256
87a74b67..., `tok_ids_sha256`). `train_mode`: `full` | `lora` | `frozen`; `train_vision` also trains the vision tower.

## Codecs (`tok_codec`, also `lm_token_loss`)

| Codec | Symbols | Round trip |
|---|---|---|
| `fast` | the reference FAST tokenizer: DCT-II ortho over time, np.around(scale x), frequency-major, minus the fitted min_token, BPE (ByteLevel, `tok_vocab` 1024) fitted on the training subset; variable length + end symbol | <= sqrt(K) 0.5 / scale inside the fitted range |
| `bins` | K A values, time-major, b = min(floor((y + 1) / 2 bins), bins - 1) in float64 | <= 1 / bins |
| `dct` | FAST's integers with a symmetric clip, fixed length, no BPE | <= sqrt(K) 0.5 / scale (keep = K, no clip) |
| `digits` | VLA-0: q = round_half_even((y + 1) / 2 1000) as decimal integers joined by single spaces, through the LM's tokenizer; parsing needs exactly 56 integers in 0..1000 | <= 1 / 1000 |
| `nav_text`, `nav_click` | ordinary LM text under `nav_grammar_v1` (`codecs/nav_text.py`); no head parameters | exact |

FAST calls the reference directly: `codecs/fast_reference.py` is physical-intelligence/fast
`processing_action_tokenizer.py`@ec4d7aa71691cac0b8bed6942be45684db2110f4 byte for byte (sha256
6f021ca1..., checked at import; provenance in `tests/fixtures/fast_reference/`). On one fit the token
stream, the tokenizer JSON and the decoded chunks equal an independently imported copy's (tested).
The schema fixture `out/fast_fixture_v2.json` (= `tests/fixtures/fast_fixture_v2/`) is the fit on
`schema_examples.fast_fixture_chunks()`: sha256 cab2442cc376ab1ee68f13097bce41462b2db0d1655152a086a04df3e00352b5,
tokenizers 0.22.2, min_token -28, max_token 28, 736 BPE symbols; a refit reproduces it byte for byte.

Id bindings (schema 1.1, `tok_ids` = the reserved-id file, `tok_ids_sha256` = its pin 87a74b67..., the sha256
of json.dumps(ids), not of the file bytes): FAST symbol s -> LM id 247019 + s and the end symbol -> 248043;
bin b -> 247019 + b; digits use the tokenizer's own ids plus eos.

Navigation (`codecs/nav_text.py`, `nav_grammar_v1`, schema 8.1): `parse(text, 'nav' | 'click', history_frames)`
reads the text after the last `</think>` and returns the nav actions, a `Click`, a big turn or `stop`, or
None; `primitives(...)` expands nav actions and big turns (turn_left 90 = 6 turns, turn_around = 12 left);
clicks go to vla_where's controller. `FALLBACK = ('turn_left',)` after a failed re-query.
`allowed_strings(arm)` enumerates the finite language (910 nav strings, 10,205 click strings) and
`constraint(tokenizer, arm, history_frames)` builds the token trie for constrained decoding
(`prefix_allowed_tokens_fn` for transformers' `generate`). vla_nav vendors this file by sha256.

## Config keys and defaults

`VLAConfig.from_spec(spec)` loads the schema-10 tree exactly (unknown keys raise; a bare `tokens.codec`
outside `vla.head` raises; `vla.schema` must be `vla_schema_v2`) and returns the other sections for the
trainer, with `rest['control_only']` (launchers refuse a control-only arm without the user's recorded yes),
`rest['train_effective']` (optim + train, overlaid key by key by `nav.train` for navigation arms) and
`rest['eval_effective']` (`eval`, or `nav.eval` alone for navigation arms). A navigation config whose
`vla.cond` is not `none` raises. Schema path -> flat key: `head.type` -> `head`; `head.taps` -> `taps`; `head.regression.{arch,hidden,blocks}`
-> `reg_*`; `head.flow.{layers,width,heads,objective,time_dist,steps,cond_gate}` -> `flow_*`;
`head.tokens.{codec,vocab,bins,scale,max_tokens,reserved_ids,reserved_sha256}` -> `tok_codec`, `tok_vocab`, `tok_bins`,
`tok_dct_scale`, `tok_max_tokens`, `tok_ids`, `tok_ids_sha256` (`fast_reference` and `fast_reference_sha256` must
name the vendored reference); `where.{dropout,vector}` -> `where_*`; `train.seed` -> `where_seed`;
`backbone.{train,vision}` -> `train_mode`, `train_vision`; `input.proprio: false` -> `proprio_dim: 0`.

| Key | Default | Meaning |
|---|---|---|
| `head` | `regression` | `regression` \| `flow` \| `tokens` (aliases `generative`, `diffusion`, `discrete`) |
| `action_dim`, `chunk` | 7, 8 | A, K |
| `hidden_size`, `lm_layers` | 4096, 32 | D and the LM's decoder layers; both must match the backbone |
| `proprio_dim`, `proprio_inject` | 8, `head` | P (0 disables); `head` \| `lm` (flow, tokens) |
| `taps`, `tap_norm` | `[]`, false | 1..lm_layers-1 or -1; `[]` = `[16, -1]` for flow, `[-1]` otherwise |
| `detach_backbone` | false | flow only: the head sends no gradient into the LM |
| `lm_token_loss`, `lm_token_weight` | `none`, 1.0 | flow only: a chunk codec the LM also writes (F1: `fast`) |
| `cond`, `cond_dim`, `cond_inject` | `none`, 1024, `head` | `none` \| `spatial_readouts` \| `g3t_tokens` \| `both`; cond token width; `head` \| `lm` (flow) |
| `where_vector`, `where_entities`, `where_features` | true, 2, 18 | feed where vectors; target and place; fixed 18 |
| `where_dropout`, `where_seed` | 0.2, 17 | sha256 dropout share and seed |
| `max_views`, `g3t_cam_dim`, `g3t_patch_dim`, `g3t_patch_grid` | 32, 2058, 2048, 0 | G3T inputs (0 = camera tokens only) |
| `readout_depth_grid`, `readout_hidden` | 4, 256 | readout projector |
| `reg_arch` | `starvla_oft_985c2238` | fixes `reg_block oft`, `reg_act relu`, `reg_input_act true`, `reg_final_norm true`; `custom` frees them |
| `reg_hidden`, `reg_blocks`, `reg_cond_heads` | 8192, 2, 8 | regression width (1024 = the small variant), blocks, cond cross-attention heads |
| `flow_layers`, `flow_width`, `flow_heads`, `flow_mlp_ratio`, `flow_dropout` | 8, 1024, 16, 4.0, 0.0 | expert size |
| `flow_objective`, `flow_time_dist`, `flow_steps`, `flow_cond_gate`, `flow_time_cond` | `flow`, `beta_1.5_1`, 10, `zero_init`, `concat` | `flow` \| `ddpm`; `beta_1.5_1` \| `uniform` \| `logit_normal`; sampler steps; tanh gate; `concat` \| `adaln` |
| `ddpm_train_steps`, `ddpm_clip_sample`, `ddpm_prediction` | 100, true, `epsilon` | cosine schedule length (>= `flow_steps`); clip x0; `epsilon` \| `sample` |
| `tok_codec`, `tok_vocab`, `tok_bins`, `tok_dct_scale` | `fast`, 1024, 256, 10.0 | codec; FAST vocabulary; bins; FAST and dct scale |
| `tok_dct_keep`, `tok_dct_clip` | 0, 127 | `dct` only |
| `tok_max_tokens`, `tok_ids`, `tok_ids_sha256`, `tok_ce`, `tok_codec_path` | 64, `append`, `''`, `full`, `''` | decode cap; id source and pin; CE scope; fitted codec file |
| `tok_fast_reference` | `physical-intelligence/fast processing_action_tokenizer.py@ec4d7aa7...` | the vendored FAST reference |
| `train_mode`, `train_vision` | `full`, false | `full` \| `lora` \| `frozen` |
| `lora_rank`, `lora_alpha`, `lora_dropout`, `lora_targets` | 32, 64, 0.05, q/k/v/o, gate/up/down, in_proj_qkv, in_proj_z, out_proj | LoRA |

## Parameter counts at Qwen3.5-9B width (hidden 4096; meta device, no weights)

New parameters only; the 9B backbone is unchanged. Every row includes the 8-D proprio map. "new LM rows"
are appended codec embedding and output rows (`tok_ids=append`; 0 with the reserved-id file). The default
head is 167,985,159 parameters (StarVLA's 167.9M plus the proprio map); U1 adds 303,104 (the where map).

| Head | cond | head | cond projector | LM injection | new LM rows | total new |
|---|---|---:|---:|---:|---:|---:|
| (a) regression, StarVLA OFT H 8192 (default) | none | 167,985,159 | 0 | 0 | 0 | 167,985,159 |
| (a) regression, StarVLA OFT H 8192 (default) | spatial_readouts | 168,288,263 | 0 | 0 | 0 | 168,288,263 |
| (a) regression, StarVLA OFT H 8192 (default) | g3t_tokens | 444,874,759 | 2,145,300 | 0 | 0 | 447,020,059 |
| (a) regression, StarVLA OFT H 8192 (default) | both | 445,177,863 | 3,244,368 | 0 | 0 | 448,422,231 |
| (a) regression, OFT H 1024 | none | 6,325,255 | 0 | 0 | 0 | 6,325,255 |
| (a) regression, OFT H 1024 | spatial_readouts | 6,363,143 | 0 | 0 | 0 | 6,363,143 |
| (a) regression, OFT H 1024 | g3t_tokens | 11,576,327 | 2,145,300 | 0 | 0 | 13,721,627 |
| (a) regression, OFT H 1024 | both | 11,614,215 | 3,244,368 | 0 | 0 | 14,858,583 |
| (b) flow, 8 x 1024, taps 16+32 | none | 145,974,279 | 0 | 0 | 0 | 145,974,279 |
| (b) flow, 8 x 1024, taps 16+32 | spatial_readouts | 180,666,383 | 0 | 0 | 0 | 180,666,383 |
| (b) flow, 8 x 1024, taps 16+32 | g3t_tokens | 180,646,927 | 2,145,300 | 0 | 0 | 182,792,227 |
| (b) flow, 8 x 1024, taps 16+32 | both | 181,715,983 | 3,244,368 | 0 | 0 | 184,960,351 |
| (b) flow, 8 x 1024, + FAST LM loss | none | 145,974,279 | 0 | 0 | 8,396,800 | 154,371,079 |
| (b) flow, 8 x 1024, + FAST LM loss | spatial_readouts | 180,666,383 | 0 | 0 | 8,396,800 | 189,063,183 |
| (b) flow, 8 x 1024, + FAST LM loss | g3t_tokens | 180,646,927 | 2,145,300 | 0 | 8,396,800 | 191,189,027 |
| (b) flow, 8 x 1024, + FAST LM loss | both | 181,715,983 | 3,244,368 | 0 | 8,396,800 | 193,357,151 |
| (b) flow, 16 x 1024 (large) | none | 280,364,039 | 0 | 0 | 0 | 280,364,039 |
| (b) flow, 16 x 1024 (large) | spatial_readouts | 348,676,119 | 0 | 0 | 0 | 348,676,119 |
| (b) flow, 16 x 1024 (large) | g3t_tokens | 348,656,663 | 2,145,300 | 0 | 0 | 350,801,963 |
| (b) flow, 16 x 1024 (large) | both | 349,725,719 | 3,244,368 | 0 | 0 | 352,970,087 |
| (c) tokens, FAST 1024 | none | 0 | 0 | 1,054,976 | 8,396,800 | 9,451,776 |
| (c) tokens, FAST 1024 | spatial_readouts | 0 | 0 | 1,132,800 | 8,396,800 | 9,529,600 |
| (c) tokens, FAST 1024 | g3t_tokens | 0 | 2,145,300 | 5,253,376 | 8,396,800 | 15,795,476 |
| (c) tokens, FAST 1024 | both | 0 | 3,244,368 | 5,331,200 | 8,396,800 | 16,972,368 |
| (c) tokens, 256 bins | none | 0 | 0 | 1,054,976 | 2,097,152 | 3,152,128 |
| (c) tokens, 256 bins | spatial_readouts | 0 | 0 | 1,132,800 | 2,097,152 | 3,229,952 |
| (c) tokens, 256 bins | g3t_tokens | 0 | 2,145,300 | 5,253,376 | 2,097,152 | 9,495,828 |
| (c) tokens, 256 bins | both | 0 | 3,244,368 | 5,331,200 | 2,097,152 | 10,672,720 |

## Toy evidence (CPU)

Overfit of 64 synthetic (state, chunk) pairs on the stub backbone (width 64; K = 4, A = 7; each state ends
with the 4 query tokens), full-batch AdamW, on a loaded node (`tests/test_training.py`, 2026-11-11, `notes/pytest_v3_toy.txt`):

| Head | Steps | Final loss | mean / max abs error | Bound (mean / max) | Time |
|---|---:|---:|---:|---|---:|
| regression (StarVLA OFT layout, H 64) | 400 | 0.024 | 0.025 / 0.103 | 0.03 / 0.15 | 10 s |
| flow (10 Euler steps) | 1500 | 0.044 | 0.050 / 0.362 | 0.08 / 0.40 | 61 s |
| ddpm, epsilon (10 DDIM steps) | 1500 | 0.030 | 0.066 / 1.21 (q99 0.444) | 0.08 / q99 0.50 | 69 s |
| ddpm, x0 (`ddpm_prediction=sample`) | 1500 | 0.000 | 0.003 / 0.013 | 0.02 / 0.10 | 72 s |
| tokens, bins (32) | 400 | 0.001 | 0.016 / 0.031 | 0.03 / 1/32 | 23 s |
| tokens, dct (scale 20) | 400 | 0.001 | 0.012 / 0.042 | 0.03 / 0.08 | 23 s |
| tokens, fast (reference BPE, scale 20) | 500 | 0.001 | 0.012 / 0.042 | 0.03 / 0.08 | 35 s |

Epsilon prediction recovers x0 as (x - sqrt(1 - ab) eps) / sqrt(ab), which multiplies the eps error by up to 1 / sqrt(ab) (about 2000 at the last cosine step); a few of 1,792 elements stay wrong, so that case bounds the 99th percentile. x0 prediction on the same setup has max error 0.013.

Bimodal toy (each state's chunk is +m or -m with equal odds, 32 samples per state): the flow expert puts 0.92 of its samples within 0.15 of a mode and draws the minority mode 0.36 of the time (mean distance to the nearest mode 0.08); the L1 regression head puts none near a mode (distance 0.85: it predicts between the modes).

First batch through the tiny native Qwen3.5 student (2 hybrid layers, width 32, real vocabulary; `examples/train_step.py --cond both`, one AdamW step, `notes/example_train_step.txt`): regression loss 0.542 (grad norm LM 11.5, head 4.34, cond 0: the zero-initialised maps pass no gradient at step 0); flow 1.872 (LM 3.00, head 4.55, cond 0: closed tanh gates); tokens 12.43 CE over the full vocabulary (LM 0.16, codec rows 1.43, LM injection 9.60); flow with `detach_backbone` + bins LM loss 14.30 (flow 1.872 + CE 12.43; LM gradient 0.18, from the token loss only). Every head and cond value passes forward, loss, backward, step and predict in `tests/test_student.py`.
