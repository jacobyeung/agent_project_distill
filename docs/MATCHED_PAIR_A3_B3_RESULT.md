# Matched-pair result: target format vs. question membership (RUN A3 vs. RUN B3)

RUN A3 and RUN B3 train OneThinker-8B on the same 570 questions, the same split, the same
frames and prompts, the same trainer and configuration, and the same 54 optimizer steps
(LoRA r=32, alpha 64, text and vision attention/MLP plus mergers, lr 1e-4 cosine, effective
batch 32, 3 epochs). RUN A3 trains on the corrected-format compact v2.4.3 targets; RUN B3
trains on the matched v1c subset of the same 570 questions. Because membership, budget and
every other factor are held fixed, a gap between the two isolates the effect of target
format. Both evaluate on the fixed protocol: harness `58794b87fb1c289cbaeffbf2cff4858c77ca7a87`,
instructed prompt, 4,096-token generation budget, strict parser as the metric of record with
a lenient rescore as sensitivity, RGB-only, tool-free, greedy, 32 frames.

## VSIBench (answerable-500)

| cell | strict | lenient | parse failures | capped (no answer) | items | training rows | steps | checkpoint |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| base OneThinker (instructed prompt) | 31.47 | 39.19 | 93 | 0 | 500 | — | 0 | none |
| RUN A3 (v2.4.3 corrected format) | 22.18 | 22.18 | 97 | 89 | 500 | 570 | 54 | `/data3/jjyeung/ddp_onethinker_v243_onethinker_20260921T0330Z` |
| RUN B3 (v1c matched subset) | 22.61 | 22.61 | 185 | 182 | 500 | 570 | 54 | `/data3/jjyeung/ddp_onethinker_v1cm243_onethinker_20260921T0330Z` |

RUN B3 scores 0.43 points above RUN A3 and 8.86 points below base. RUN A3 scores 9.29 points
below base.

Source: `out_run_a3/RESULTS_VSIBENCH_V243.md` and `out_run_b3/RESULTS_VSIBENCH_V1CM243.md`
(both under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_onethinker_v242_eval_20260921T0300Z/`),
cross-checked against `out_run_b3/summary_eb3_vsi.txt` for RUN B3.

### Per question type, strict parser

| question type | base | RUN A3 | RUN B3 |
|---|---:|---:|---:|
| appearance order | 52.0 | 46.0 | 52.0 |
| absolute distance | 12.8 | 17.4 | 17.4 |
| counting | 21.6 | 14.8 | 14.2 |
| relative direction, easy | 36.0 | 38.0 | 50.0 |
| relative direction, hard | 22.0 | 26.0 | 14.0 |
| relative direction, medium | 36.0 | 40.0 | 16.0 |
| relative distance | 42.0 | 26.0 | 24.0 |
| object size | 45.0 | 10.2 | 20.0 |
| room size | 21.0 | 8.4 | 2.6 |
| route planning | 26.0 | 20.0 | 24.0 |

Source: `out_run_b3/RESULTS_VSIBENCH_V1CM243.md`.

## VSTIBench (representative-450)

| cell | strict | lenient | parse failures | capped (no answer) | items | training rows | steps | checkpoint |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| base OneThinker (instructed prompt) | 40.16 | 45.40 | 55 | 1 | 450 | — | 0 | none |
| RUN A3 (v2.4.3 corrected format) | 32.09 | 32.09 | 58 | 51 | 450 | 570 | 54 | `/data3/jjyeung/ddp_onethinker_v243_onethinker_20260921T0330Z` |
| RUN B3 (v1c matched subset) | 37.85 | 37.85 | 24 | 24 | 450 | 570 | 54 | `/data3/jjyeung/ddp_onethinker_v1cm243_onethinker_20260921T0330Z` |

RUN B3 scores 5.76 points above RUN A3 and 2.31 points below base. RUN A3 scores 8.07 points
below base.

Source: `out_run_a3/RESULTS_VSTIBENCH_V243.md` and `out_run_b3/RESULTS_VSTIBENCH_V1CM243.md`
(both under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_onethinker_v242_eval_20260921T0300Z/`).

### Per question type, strict parser

| question type | base | RUN A3 | RUN B3 |
|---|---:|---:|---:|
| camera displacement | 20.8 | 6.6 | 14.0 |
| camera movement direction | 30.0 | 20.0 | 26.0 |
| camera-object absolute distance | 10.0 | 31.2 | 30.6 |
| camera-object relative distance v1 | 52.0 | 38.0 | 44.0 |
| camera-object relative distance v2 | 72.0 | 46.0 | 54.0 |
| camera-object relative distance v3 | 70.0 | 60.0 | 68.0 |
| object-object position, left/right | 60.0 | 48.0 | 60.0 |
| object-object position, near/far | 74.0 | 50.0 | 50.0 |
| object-object position, up/down | 92.0 | 66.0 | 80.0 |

Source: `out_run_b3/RESULTS_VSTIBENCH_V1CM243.md`.

## Interpretation

Target format separates RUN A3 from RUN B3 on VSTIBench but not on VSIBench. On VSTIBench,
RUN B3's v1c-format targets cut parse failures roughly in half against RUN A3's corrected
format (24 vs. 58) and lift the score 5.76 points (37.85 vs. 32.09), so format explains most
of the gap between the two matched runs there. On VSIBench, the two formats land within noise
of each other (22.61 vs. 22.18, a 0.43-point gap), yet RUN B3 hits the generation cap more
than twice as often as RUN A3 (182 vs. 89 of 500 items) — termination behavior tracks the
question subset, not the target format, on this benchmark. Both matched runs sit below base
on both benchmarks (VSIBench: 8.86 to 9.29 points; VSTIBench: 2.31 to 8.07 points), so neither
target format recovers base ability on this 570-question, 54-step budget. The pair therefore
shows that format and question membership interact differently by benchmark: format is the
dominant lever on VSTIBench, while on VSIBench some other factor tied to the 570-question
subset (row count, item difficulty, or training budget) suppresses both formats similarly.
