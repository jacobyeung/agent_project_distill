# Head-call arms on the full fine-tuning trainer (HC, HX, HA): design

Branch `headcall-fullft` (base: `fullft-gxs` 8ba75d5). The `headcall/` package comes from `phase2-headcall-opus` 83c2d47
(agent_project_distill); its converters, first-hit packs and probe builder stay there, and their outputs enter this tree as
pinned sidecars and rows. Choices: `L/fullft_review/HEADCALL_ARM_CHOICES.md` (defaults applied 2026-10-31 03:02 PT;
`L` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`). Full fine-tuning itself, the CPD head
recipe and the checkpoint formats are in `DESIGN_FULLFT_GXS.md`.

## 1. Arms

| Arm | Rows (396,649 RG2P2 questions, one epoch, 1,550 steps) | Targets | Scheduled sampling |
|---|---|---|---|
| HC | RG2P2_X's questions | head-call traces on 85,214 rows, plain G traces on 50,989, answer-only elsewhere | p 0 -> 0.5 over steps 0-1,000, then 0.5 |
| HX | RG2P2_X | answer-only on every row | off |
| HA | RG2P2_A | RG2P2_A's free-text GT traces | off |

Shared by all three: CPD's final full weights and camera + point-depth heads (Cambrian-P width 2,048) as init; full FT at
Cambrian-P's rates (LLM and merger 1e-5, vision 2e-6, heads 1e-4), AdamW, weight decay 0, 3% warmup, cosine, per-family
clip 1.0; the PD row routing (every labelled question row trains the heads, with carriers); RG2P2_A's segment loss, which is
bitwise the default on answer-only rows; seeds 17 and 18; global batch 256 on 32 GPUs. The configs differ only in their
`headcall` block (arm, sidecar pin, sampling). All three admit the same qids, admission sorts rows by qid and the seed
shuffles them, so `question_order_sha256` is equal across HC, HX, HA and FT_A at one seed.

## 2. The headcall training block (`headcall/rows.py`)

- Admission keeps only a fixed set of row fields (`provisional._load_candidate_rows`), so head calls cannot ride in the
  candidate index (phase 2's runtime patch read `row["head_calls"]`, which admission drops). They come from a pinned gzip
  JSONL sidecar joined at startup like the label bank: an entry binds to one admitted row by the SHA-256 of its target text
  and its input identity (`auxiliary_targets.input_identity`), and an HC entry's template must re-render the admitted target
  from its GT responses. Every sidecar qid must be an admitted row; the join audit goes to `headcall_rows.json`.
- Every sidecar row (HC's head-call rows and their twins in HX and HA): its depth calls go first into the point-depth
  targets, the bank's 64 points fill the remaining slots, and the 16 carriers are inserted even when the bank has no label
  for its scene (`camera_targets.insert_tokens` `force_carriers`). The arms therefore share carriers and depth targets row
  for row; the twins' queries come from HC's calls through one function (`depth_queries`).
- HC rows: tool responses (`<tool_response>` through `</tool_response>`) are masked from the LM loss; the student writes
  its calls and everything after each response.
- Scheduled sampling (HC): before backward, each chosen call (a pure function of seed, qid, step) gets the student's own
  head answer from a session (one no-grad forward of the row's carrier-bearing prompt); answers outside the tolerance gate
  (depth max(10%, 0.20 m); position 0.25 m; heading, pitch, roll, view 10 deg) keep GT, every derived value is re-rendered,
  and a row whose re-derived decision misses the GT answer keeps its GT target. The new target is spliced after the unchanged
  prompt. Under FSDP every forward is a collective: ranks all-reduce their count of sampled rows and the less busy ranks run
  discarded forwards to match; padding slots never sample. Per-step counters (session and discarded forwards, rows and
  responses swapped) go to `metrics.jsonl` under `headcall`.
- The block requires full fine-tuning, the camera head with its point-depth head, and not the Cambrian-P routing.
  `ddp_config.runtime_bindings` binds the headcall training files into every protocol.

## 3. Rows (`tools/headcall_rows.py`; build `/scratch/jjyeung/headcall_fullft/rows/v3`)

`build` reads phase 2's G and motion exports (`/scratch/jjyeung/phase2_opus/out_fix/{rung1_g,rg2vs_motion}`), RG2P2's
drop list (`drop_qids.txt`, 720e9711), the rung-2 parts and the published G rows, and writes the three sidecars,
`HC_REPLACE` (136,203 targets that differ from RG2P2_X's) and the table below. Every HC and HX entry passes the
trainer's join check on the source rows; HX's and HA's queries equal HC's (228,395 depth points; at most 5 per group).

| Source | Type | Rows | Head-call | Fallback | Answer-only | Plain |
|---|---|---:|---:|---:|---:|---:|
| rung-1 G | absolute direction | 40,256 | 22,941 | 17,315 | 0 | 0 |
| rung-1 G | relative direction (hard) | 23,929 | 16,288 | 7,641 | 0 | 0 |
| rung-1 G | absolute distance | 30,126 | 13,364 | 16,762 | 0 | 0 |
| rung-1 G | relative distance | 30,525 | 16,796 | 13,729 | 0 | 0 |
| rung-1 G | appearance order / size / relative size | 40,203 / 10,017 / 30,412 | 0 | 0 | 80,632 | 0 |
| rung-1 G | counting / relative count | 5,814 / 45,175 | 0 | 0 | 0 | 50,989 |
| RG2VS | camera movement direction | 12,000 | 9,238 | 2,762 | 0 | 0 |
| RG2VS | camera displacement | 12,000 | 6,587 | 5,413 | 0 | 0 |
| RG2VS | camera-object abs / rel distance, object-object lr / nf / ud | 60,000 | 0 | 0 | 60,000 | 0 |
| RG2DS (ADT) | 7 types | 51,900 | 0 | 0 | 51,900 | 0 |
| RG2RSP / RG2RT2 | room size / route | 392 / 3,900 | 0 | 0 | 4,292 | 0 |
| **Total** | | **396,649** | **85,214** | **63,622** | **196,824** | **50,989** |

Fallback and answer-only rows carry their RG2P2_X answer-only targets in HC. `index` (code-aws) rewrites RG2P2_X's frozen
candidate index into HC's: each replaced entry becomes an inline row (the X twin's own row and frame paths, target
replaced, checked against the build's input identity and twin target) with its target in a shared shard file; admission's
own loader accepts it (test). `subset` writes the smoke's files for the 20 smoke-bank scenes (1,407 head-call rows).

## 4. Init: `full_ft` init kind `full_export`

`init: {kind: full_export, path, sha256}` pins a full-weights manifest (`full_weights/full_weights.json`, which pins every
shard); `full_ft.load_init_export` loads it exactly into the BF16 base before the FP32 master cast and checks that it names
the run's base snapshot. The heads load through `init_modules.heads` (exact names, shapes, dtypes, values).
`full_ft.read_milestone` verifies a milestone export (`milestone_<step>/`, written by `save_milestone_export`) file by file
and returns both pins; the test writes one with the trainer's own writer.

## 5. Evaluation and gate

- `orchard_eval --carriers insert --headcall decode` (`EVAL_HEADCALL=decode`): the published heads load exactly (camera
  tokens must equal the carrier pin), every item decodes through `headcall.eval_hook` (greedy, the 4,096 cap counts inserted
  responses, max 80 calls, 128 call tokens, lenient calls executed and counted apart), and each item's call record goes to
  `headcalls/<qid>.json`. The heads, decode settings and headcall code hashes enter the adapter pin and protocol identity;
  without the option every identity is unchanged. HC, HX and HA use the same decoder.
- Cells: VSI-500 and VSTI-450 v3, thinking on (primary) and off. `tools/headcall_eval_summary.py` reports the strict parse,
  a lenient rescore apart, and call metrics (valid, strict, lenient, refused, value used downstream) per type.
- Gate: `headcall.gate_eval` on the 1,368 held-out probe rows with `--milestone` or `--full-weights`, on CPD's final
  checkpoint (go/no-go) and on each arm's final heads, with the shuffled control.

## 6. Deviations

| Choice | Source value | Ours | Reason |
|---|---|---|---|
| Head use | Cambrian-P: training loss only | tool calls mid-trace, responses inserted and masked | the user's phase-2 plan |
| Row routing | Cambrian-P (and CPD): question rows NTP only | every labelled row trains the heads with carriers | head-call rows need carriers and the heads; the arms keep one routing |
| Carriers outside the bank | Cambrian-P: camera tokens only on supervised samples | forced on every sidecar row | the heads answer that row's calls |
| Depth targets | random dense samples (DepthVLM) | the row's queried points first, then the bank's | supervise where the traces query |
| Head warmup | CPD: 51-step isolation, 51-step ramp | none | CPD trained the heads |
| Init precision | CPD's FP32 masters | the BF16 export, cast back to FP32 masters | the export is the only world-size-independent format; a full-state resume needs CPD's world and shard layout |
| Pose-only rows | Cambrian-P beta 1; CPD 34,888 | none | CPD trained the heads |
| Answer-only share | traces on every row (USER 10-21 recipe) | 66% of HC's rows answer-only | the heads cannot derive those answers; HC is the experiment against HX |
| Sampling cost under FSDP | phase 2's patch: a session forward for every row on every rank | only sampled rows, matched to the busiest rank by discarded forwards | same collectives, fewer forwards |
| HX/HA decoding | plain generate | the head-call decoder | one evaluator for the three arms |
| Smoke sampling schedule | 0 -> 0.5 over 1,000 steps | 0 -> 0.5 over 20 steps | the 30-step smoke must measure the sampling forwards |

## 7. Tests

`tests/test_headcall_fullft.py` (config, sidecar join and refusals, encoder on the tiny Qwen3.5 processor, splice, sampling
swaps, decision-rule rejection, FSDP forward matching, the `full_export` warm start from a real milestone layout, the HC
index rewrite through admission's loader, and a 2-rank CPU/gloo FSDP full-FT step with heads, carriers, masking and
sampling); `tests/test_headcall_eval.py` and `tests/headcall/test_gate_fullft.py` (evaluator and gate); `tests/headcall/`
(phase 2's protocol, derive, sampler, prefill, decode and gate tests on this tree).
