<!-- recovered by seal_plan: transcript=71f94277 line=23510 utc=2026-11-13T18:25:32.072Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_MILESTONE_ROUTED_REVIEW.md  -->
# Independent review, routed scope: the reader that executes a model's tool programs with real tools

You are an independent reviewer from a different model family than the author. The code under review measures whether a trained model's tool programs work when real perception answers them. A silent fallback, an unpaired comparison or a wrong configuration would make that measurement meaningless.

## Context

A 9B vision-language model (run 469ddece) is trained to write short programs for five question types (camera displacement, camera movement direction, camera rotation, absolute object distance, room size): the program calls tools (`move`, `turn`, `depth_at`, `ground`, `gap`), a runtime answers them from the model's own pose, scale and depth heads plus a segmenter's masks, and the model reads the printed result. The "routed" read runs that loop on 636 held-out questions (150 absolute distance, 36 room size, 450 camera) and compares, on the same items and the same perception, the model's routed answer with a scripted program (rule R1: routed types within 5 points of the scripted program, tool-call rate at least 95%). It runs natively: the trainer's own model code, loaded from a weight export, on one GPU.

The author (lane "evalx") forked an earlier reviewed reader and added: a metadata-only configuration loader (the reader authenticates the run's derived configuration from the export's `artifact.json` and small mirrored JSON files, and must not open the training databases), a tensor-only device-transfer helper that keeps frame and video provenance on the batch, a bootstrap, and the command chain. Scope "routed" of the review packet:

- Packet: `/scratch/jjyeung/orch_cd/evalx/work/milestone/SCOPED_REVIEW_REQUEST.json` (entry `routed`: thirteen code pins and `code_pins_sha256` 548cbefe...).
- Files: under `/scratch/jjyeung/orch_cd/evalx/work/milestone/` (`camera_leg.py`, `chain.py`, `chain_save.py`, `execute_chain.py`, `native_bootstrap.py`, `report_camera_leg.py`) and `native/out2/` (`common.py`, `geometry.py`, `nomdg.py`, `perception.py`, `r1.py`, `read_runtime.py`, `routed.py`), with their tests.
- Background you may read: the earlier verdict on the reader this fork derives from, `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ROUTED_NOMDG.md`; its run card `/scratch/jjyeung/orch_cd/legs1_routed/out2/RUNCARD_ROUTED_NOMDG.md`; the frozen proposal setting `/scratch/jjyeung/orch_cd/official_reads/FUSION_PROPOSAL_SETTING_FROZEN_VSI_20261113.md`; the camera cohort `/scratch/jjyeung/orch_cd/legs1_routed/out2/CAMERA_COHORT.json`; the lane's notes at the top of `/scratch/jjyeung/orch_cd/evalx/STATUS.md` (top block only). The sealed trainer tree the reader imports from is named in the lane's files; read only the functions the reader calls.

## Check, with file and line for every finding

1. **Pins.** Hash the thirteen files; do they equal the packet, and does the canonical digest equal `code_pins_sha256`? State how you computed it. Say which differences from the earlier reviewed reader (`/scratch/jjyeung/orch_cd/legs1_routed/out2/`) exist beyond the three stated additions.
2. **Configuration loader.** The model is built from the derived configuration bound to this export: architecture, heads, frame layout, templates and token setup must come from authenticated metadata; a configuration that does not match the export's identities refuses; no default fills a missing field; no training database is opened; every tensor of the export is loaded strictly, with no silent fallback to parent or base weights.
3. **Transfer helper.** Only tensors move; frame indices and video identity stay attached and are the ones used for tool calls and for binding outputs to items.
4. **The loop.** Tool calls are parsed from the model's own output and answered only by the runtime; a malformed, missing or failed call is counted (call rate, error classes) and never replaced by a direct answer or a scripted call without being counted; the tool-response text is byte-identical in form to training; thinking and length budgets are the registered ones; no ground truth reaches the prompt or the tools.
5. **Perception and geometry.** The frozen proposal setting applies to absolute distance and room size only; pose, scale and depth come from the checkpoint under read (geometry is conditioned on that checkpoint, not on an earlier parent-conditioned export); the scripted-program arm uses exactly the same perception per item.
6. **R1 and pairing.** Exactly the 636 pinned items; routed and scripted arms paired per item; denominators keep every item including failures; the 5-point rule and the 95% call rate are computed as registered; step-1 rehearsal outputs are labelled diagnostic.
7. **Failure preservation and saves.** As in the direct scope: evidence kept, no silent retry, bounded alternating saves with a free-space floor, behaviour when a write fails for lack of space.
8. **Tests.** Run the scope's CPU tests from a private copy and report the count. Add a test only if it demonstrates a finding.
9. **What CPU cannot show** (GPU memory fit of the model plus tower on one 49 GB card, runtime compatibility, timing).

## Output

Write `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_MILESTONE_ROUTED.md`, at most 50 lines: first line **ACCEPT**, **ACCEPT AFTER FIXES** or **REJECT**; one line per item with evidence; findings by severity with the smallest fix; what you ran; what you did not check. If and only if the verdict is ACCEPT, also write `/scratch/jjyeung/orch_cd/leg_s1_review/MILESTONE_ROUTED_RECEIPT.json` with `{"verdict": "ACCEPT", "reviewer": "<your model family and role>", "scope": "routed", "code_pins_sha256": "<the digest you verified>"}`. Return a summary of at most 10 lines.

## Bounds

Read-only everywhere except `/scratch/jjyeung/orch_cd/leg_s1_review/work_milestone_routed/` (private copies and tiny fixtures, at most 500 MB). No Git commands, no ssh, no network, no GPU, no agents, no deletion commands. Stay on `/scratch`; never read, search or list `/home` or `/data*`; no recursive search outside the folders named here. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`.
