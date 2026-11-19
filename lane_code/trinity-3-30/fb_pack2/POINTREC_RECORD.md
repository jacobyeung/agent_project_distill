# fbp_pointrec: how pointing rows are trained and served, and the options for their think block

**Summary.** Training supervises the closing half of the empty think block, three tokens (`\n` `</think>` `\n\n`) after a `<think>\n` prompt. They carry 12.0% (visible) or 17.6% (null) of a pointing row's weight and 3.5% of a final-mode step's language-loss weight.
The scored eval and production serving never ask the model to generate those tokens: they pre-fill `<think>\n\n</think>\n\n` with `enable_thinking=False`, so a train-serve mismatch already exists today, down to the token split of the prefix.
Option (c) needs no admission change and no scoring change; (a) needs both; (b) also needs a non-native chat format in every pointing caller.
**Recommended: (c)**, best done as (c′): the trainer encodes pointing rows with the eval's own thinking-off prefix, so the loss starts at the JSON. Keep (a) as a later designed change, gated on the K1 test in §4.

Sources: tree_r1 (seal 57a1f14d, read-only copy); source store c09bb5ca (25,020 rows: 16,262 visible, 8,758 null); Locate store d5362229. Status: analysis complete; nothing built in the tree.

## 1. Which target tokens carry loss weight today
- `build_stream` writes `READOUT_TARGET + mask JSON` for every pointing row (`carrier_c1_data.py:649-654`), where `READOUT_TARGET = '<think>\n\n</think>\n\n'` (`decoupled_v_run.py:57`). Admission always runs this rebuild (`s1_admission.py:186-192`, `:245`).
- The final configs use the duplicate layout, so rows encode through `encode_layout_row` → `encode_frames` → `training_text` (`carrier_c1_data.py:208`, `pose_samples.py:200`). `training_text` builds the prompt with the default template, which leaves thinking open and ends in `<think>\n` (`batches.py:111`). The supervised suffix is therefore `\n</think>\n\n{json}<|im_end|><|endoftext|>` (`batches.py:124-129`, stop token `:97-99`), and the labels cover the whole suffix (`pose_samples.py:229`).
- The tree asserts this boundary itself. `pose_samples.py:203-205` allows a merged tokenization only for a `…<think>\n` prompt followed by a `\n</think>\n\n` suffix, and `vqa_direct.py:181-182` requires the trainer's prefix to end in `<think>\n`.
- Weights come from `pointing_token_weights` (`carrier_c1_data.py:20-40`) with E2E-1C/1G `pointing_weights` {decision 5, row_mean 2} (`carrier_c1_run.py:1167-1171`). The row's language loss is mean(CE·w) (`carrier_c1.py:544-546`).
- **Tokenizer: MISSING.** The Qwen3.5 snapshot is on `/data2` (`students.py:18`). The staged processors named by the tests (`tests/test_pose_samples.py:17`, `tests/test_carrier_c1_routing.py:15`) are absent, and the only local `tokenizer.json` (under pointD/work/test_runs) is a 935-byte WordLevel stub. The tree's own pinned counter (`generator/derivgen_v7/derivgen/plan_contract.py:90-104`) is absent too. The counts below therefore run the tree's own `training_text`, `pointing_token_weights` and `segment_tags` on a proxy tokenizer that emits one token per Qwen2-family pre-token and keeps special tokens atomic. Real BPE can only split a word further.

| row | supervised tokens (weight) | think share |
|---|---|---|
| 3, visible, "book", frame 8, [778, 480]; N=21 | **`\n` `</think>` `\n\n`** `{"` `point` `_` `2` `d` `":` ` [` `7` `7` `8` `,` ` ` `4` `8` `0` `]}` `<\|im_end\|>` `<\|endoftext\|>`; each 1.68, ` [` 8.40 | 5.04 / 42.0 = 12.0% |
| 0, null, "lamp", frame 18; N=13 | **`\n` `</think>` `\n\n`** `{"` `point` `_` `2` `d` `":` ` null` `}` `<\|im_end\|>` `<\|endoftext\|>`; each 1.53, ` null` 7.65 | 4.59 / 26.0 = 17.6% |

Every prompt token has weight 0, including `<think>` and the `\n` after it.
- Across all 25,020 rows, the think share averages 12.10% on visible rows and 17.65% on null rows (11.99–13.64% on visible rows, depending on coordinate digits). The supervised think text is `\n</think>\n\n` on all 25,020 rows, and the prompt/suffix boundary merges on all 25,020 (`bash work/run.sh probe` → `work/probe.json`).
- Step share (`bash work/run.sh step_share` → `work/step_share.json`). Each language-loss row enters with its stream weight; vqa, pointing and routing all weigh 1.0. Each microstep's loss is divided by len(plan) (`carrier_c1_run.py:1587`). Pose and MDG rows carry no language tokens (`carrier_c1_data.py:458-459`; `carrier_c1.py:464-466`). A pointing row's mean token weight is 2.0, against 1.0 for a VQA or routing row.

| mix | rows/step | pointing rows (of all / of LM rows) | pointing share of LM weight | empty-think share of LM weight |
|---|---|---|---|---|
| E2E-1C, E2E-1G `stream_rows_per_step` | 160 | 16 (10.0% / 14.3%) | 25.0% | 3.51% |
| R1 quotas (`r1_training.py:7`, `r1_mix.py:10`) | 288 | 32 (11.1% / 14.3%) | 25.0% | 3.51% |
| either mix, no `pointing_weights` | – | – | 14.3% | 2.49% |

The R1 production config is not in this tree, so whether it sets `pointing_weights` is UNVERIFIED. These shares are of loss weight, not of loss value. Cross-entropy on three deterministic tokens should fall near zero within early steps, but I could not measure it here (no checkpoint).

## 2. How pointing is called at eval and serving
- **Scored video pointing** (`evalpath/pointing_markers.py`). The request pins `enable_thinking=False`, greedy decoding and `max_new_tokens=64` (`:28`, `:39-45`). The Qwen chat template writes the prefix: `video_prompt` calls `apply_chat_template(..., enable_thinking=False)` and asserts that the prompt ends with `EMPTY_THINK = '<think>\n\n</think>\n\n'`, directly after `<|im_start|>assistant\n` (`:17`, `:164-166`).
- `encode_prompt` wraps the processor in `ThinkingOff` (`:170-184`), runs the trainer's encoder and cuts at the first label (`:186-199`). Its "trainer" parity check (`:264-269`) therefore compares against a thinking-off encode, not the encode that training uses. Trained candidates take the same path (`pointing_candidates.py:168`). Scoring runs Trinity's `score_pointing_video.score_rows` (`:322`), which is not in this tree; its parse rule is UNVERIFIED.
- **Serving.** The production decode loop's ground backend `hrp_reread` (`carrier_c1_decode.py:435-437`) reads single images with `enable_thinking=False` (`hrp_reread.py:100`), caps output at 48 tokens (`:28`), and parses the whole raw text as JSON (`:120`). The vendored single-image contract does the same (`vendor/evalx_pointing.py:28-30`).
- **The only caller where the model closes the think block itself** is the live-parity diagnostic `video_address`. It uses the trainer prefix ending in `<think>\n` (`carrier_c1_canary.py:21-29`), caps output at 48 tokens, and parses after the last `</think>` (`live_parity_adapter.py:169-180`, run from `run_live_parity.py:261-268`).
- So in scored eval and serving the model never generates the think block, yet training supervises it. The token contexts differ as well: the eval encodes `<think>` `\n\n` `</think>` `\n\n`, while training joins `<think>` `\n` with `\n` `</think>` `\n\n` (`probe.json` `eval_vs_train_context`). The merge exception at `pose_samples.py:203-205` exists only because the tokenizer merges at that boundary.

## 3. Options
All three trip all four launch gates, because any change to code or config changes `identity(cfg)`. That changes the preparation's `config_sha256` (`carrier_c1_run.py:625`, `:694`), then the population's evidence pins and the row plan (`r1_population.py:140-151`, `:209-210`; `launch_r1/entry.py:85-88`), then the host receipt's `config_identity` and `loader_audit` (`entry.py:89-94`, rebuilt at `:189-199`), and finally the review bound to `identity(cfg)` (`entry.py:103-104`). The options differ in what else changes.

**(a) One Locate line in the target, generated at serving.**
- Tree: `build_stream` must emit the Locate target under a pinned field (pointD's plan; MUST 1 of the review), and the prepared store must assert that form. Store `d5362229` replaces c09bb5ca, so `store_hashes.pointing` and `bind_target` change (`s1_admission.py:222-223`).
- Weights: the visible-or-null decision moves to the `.\n` or `:` token after "frame k", which weighs 1.75, while ` [` or ` null` keeps 8.75–8.79 even though it now just copies the Locate line. The trace takes 33.4% (visible) or 57.6% (null) of the row's weight, which is 10.5% of the step's language-loss weight (`probe.json`, `step_share.json`). The decision weight must move to that token.
- Single-image rows: `encode_image_row` strips only `READOUT_TARGET` (`carrier_c1_data.py:386-388`), so single-image Locate rows must be refused. The store has none today.
- Reader and serving: video pointing must use the `<think>\n` prefix and parse after `</think>`. `hrp_reread` stays thinking-off, because single-image rows keep the empty form; if it ever switches to thinking-on, it must split on `</think>` as `live_parity_adapter.py:177` does. The longest Locate suffix is 32 proxy tokens (row 3315), which fits the 48- and 64-token caps.
- Eval: `pointing_markers` must drop `enable_thinking=False` (`:42`), the EMPTY_THINK assertion (`:164-166`) and `ThinkingOff` (`:186-193`), and its parity target (`:264-269`) changes. Train and serve are consistent only if the eval switches.
- **Scoring change:** a thinking-on pointing protocol, and `score_pointing_video` parsing the JSON after `</think>`, with an unclosed think counted as a parse failure. Admission also changes, which needs the one independent review (AGENTS.md).

**(b) No think block in target or prefix.**
- The native template cannot express this. A think-free target is re-rendered with `\n</think>\n\n` before it (`batches.py:120-125`), so it trains exactly as today.
- Tree: a pointing-only prompt and suffix builder that bypasses `apply_chat_template` (prompt ends `<|im_start|>assistant\n`), plus a `build_stream` change at `:653` or a strip at encode time. Weights: the decision token is unchanged, and N falls by 3.
- Reader and serving: every pointing caller must build the same non-native prompt: `pointing_markers` `:164-166` and `:186-199`, `pointing_candidates`, `hrp_reread.py:100`, `evalx_pointing.py:28-30`, and the aws_vl parity at `:264-269`.
- Consistency holds only if every caller changes. The base model's template always emits a think block, so its pointing prior is at risk.
- **Scoring change:** the prompt protocol changes, while the parser is unchanged (bare JSON). Admission or encoder code changes, which needs a review.

**(c) Leave the target as is, with zero loss weight on the think tokens.**
- Tree: add a pinned key, e.g. `pointing_weights.think: 0`, accepted by the validator (`carrier_c1_run.py:121-124`) and passed at `:1170`. It zeroes the supervised tokens before the JSON's first token (`carrier_c1_data.py:20-40`). `build_stream`, admission and the store stay byte-identical, and `store_hashes.pointing` is unchanged.
- Effect: JSON tokens weigh ×1.138 (visible) or ×1.214 (null), and the decision token rises from 8.40 to 9.55 (visible) or from 7.65 to 9.29 (null) (`probe.json`).
- **(c′)** instead encodes pointing rows through `ThinkingOff` in `Rows.get` (`carrier_c1_run.py:1159`), the encode the eval already assumes (`pointing_markers.py:189-193`). The labels then start at the JSON, the contexts match token for token, and the parity check binds the real training encode. (c) and (c′) give identical effective JSON weights, 2/(N+1) per token with N today's supervised count; they differ only in context.
- Reader, serving and eval: unchanged. Consistency: training trains only what serving generates. (c) leaves the context split mismatch from §2; (c′) removes it.
- **Scoring change: none.** The code touches no admission, legality or scoring path, but the launch review must still be re-bound to the new identity.

## 4. Test on K1 training captures
- **Data.** Use the K1 split `K1SPLIT_R0.json` (sha 27126674, equal to `r1_rooms.AUTHORITY['split']`): 233 training captures in 214 rooms, none of them in the K1-heldout, R0 (372 rooms) or R0-dev (100 rooms) lists (`bash work/run.sh k1_overlap` → `work/k1_overlap.json`). The dev-S1 and benchmark lists are not local, so apply `dev_scene_exclusions` and `benchmark_scene_exclusions` through `Exclusions` (`s1_admission.py:187`) before selection. Never use K1-heldout rooms.
- The source store holds 320 rows on 5 K1 training rooms (201 visible, 119 null, 64 per room). These form the eval set, and both arms remove them from pointing training. Frames are at `/scratch/jjyeung/k1_frames`.
- **Arms.** A0 is today's targets and weights. C′ is the recommended option. A is the Locate form, evaluated thinking-on, with a secondary thinking-off eval. The base model is a floor. A, C′ and A0 start from one milestone checkpoint, with the same seed, row plan and E2E-1C recipe, and train 200 steps (a recipe milestone). Only the pointing target form or weights differ. First, run every arm's first batch on CPU with the real processor (AGENTS.md).
- **Metric.** A visible hit is a point inside the GT mask, using the rule at `live_parity_adapter.py:183-194`. A null is correct when the output is null. Report the combined accuracy over 320 items, plus parse-failure and token-cap rates. For A, also report Locate/JSON agreement. Compare arms as item-paired differences with a bootstrap over items and over rooms.
- **Size** (`bash work/run.sh power`). At a 10% discordant-pair rate, 320 paired items give a 95% half-width of 3.46 points; a 5-point non-inferiority margin needs 247 items and a 3-point margin needs 687. Use 5 points on the 320 items, or build about 370 more rows with the same GT rule on other K1 training rooms for 3 points.
- **Pass bar.** An arm passes when the lower 95% bound of (arm − A0) is at least −5 points on combined accuracy and on each of visible hit and null accuracy, parse failures are at most 1%, and no output hits the cap. A additionally needs at least 99% Locate/JSON agreement.

## 5. What would make us drop the change
- The arm misses the §4 pass bar, or its room-level bootstrap shows a consistent fall in any single room.
- For (a): Locate/JSON disagreement above 1%; null accuracy falling while visible-hit accuracy holds, which would mean the 1.75-weight `.`/`:` token decides the answer; or no measurable gain over (c′) in its motivating metric (for example, an empty-think rate on K1 VQA prompts).
- The scoring change for (a) or (b) fails review, or Trinity's scorer cannot change before the target boundary.
- The CPU first batch with the real processor contradicts the boundary assumed here, for example if the labels do not start after `<think>\n` or the Locate suffix merges across the boundary.

## 6. What might not work, and how we would notice
- The proxy tokenizer can miscount label words or the `\n\n` token. The real-processor first batch would show different suffix ids or weights than `probe.json`.
- The template behaviour comes from the tree's assertions, not from the template file. If it were wrong, `vqa_direct.py:181-182` or `pointing_markers.py:165` would raise at their first run.
- (c) may change nothing measurable, because the think tokens' cross-entropy is near zero. A0 and C would then tie in §4; only (c′) also removes the context mismatch.
- (a) states the inherited ground-truth errors in words: hyponym absences, and "it is" with plural labels (review SHOULD 1–2). Null accuracy on those labels would fall in §4.
- `segment_tags` never emits `pointing_null` under digit-split tokenization, because the `2` in `point_2d` counts as a digit (`carrier_c1_data.py:55-58`; see `probe.json`). Null-loss logs are therefore mislabelled; training logs would show no `pointing_null` segment.
- 320 source rows lie on 5 K1-heldout rooms (`k1_overlap.json`). Admission's room audit must refuse them (`r1_rooms.py:78`, `:188-191`); a nonzero `k1_heldout` count in a host receipt would expose a leak.
- 5 rooms is a small pool, so per-room effects can dominate. A wide room bootstrap would show it; extend the pool in that case.

Commands (all `cd /scratch/jjyeung/orch_n30/fb_pack/pointrec`): `bash work/run.sh probe` (88 s, 1 core); `bash work/run.sh step_share`; `bash work/run.sh k1_overlap`; `bash work/run.sh power` (printed only). `probe.json`, `step_share.json` and `k1_overlap.json` record the sha256 of their inputs.
