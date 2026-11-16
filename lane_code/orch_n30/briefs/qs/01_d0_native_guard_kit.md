# Build brief 01 (TOP PRIORITY): native routed read kit for D0 exports, the init rule's guard read

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. ORCH wants the kit submit-ready when D0's m200 export lands (about 17:50Z).

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU on Trinity, no Orchard submission without an ORCH GO that names the job. Never search /home or /data* recursively; read named files. Every stream above 20 MB goes through the IO governor. Lane folder `/scratch/jjyeung/orch_n30/guard_kit` on the node ORCH assigns; events `B/events/guard_kit/`.

## Why
`/data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_INIT_RULE_20261116.md` (registered 11:16Z) makes the next leg's init depend on a guard read: the native routed read of a D0 candidate export (m200, m400, m600, m800, m1000) on the dev-S1 fixed list, calls served, paired against step 544's native arm of Orchard job 170056 "served by the same backend build". No kit can read a D0 export natively today, so no candidate can pass.

## Standing of this read
The registered rule binds the guard read to the backend build of job 170056, which is a Python runtime with fitted parts (selector, scale rule, guard, mask cache). The user ruled on 2026-11-16 that such a runtime is harness. The guard read is therefore an internal instrument for choosing the init; its numbers are never a claimed result, and every report says so in its first line. The claimed reads use the reader of brief 04 after it passes the acceptance test of brief 03.

## Scope
One Orchard job per candidate export (general, 1 H100, native arm only, about 1.3 h plus staging), and the paired report the rule's items 3 and 5 name. Nothing else: no direct arm, no new backend, no selector refit, no official item.

## Inputs (read these first)
- The rule: `NEXT_LEG_INIT_RULE_20261116.md` items 3, 5, 6; `D0_STOP_RULE_20261116.md`; `REFREEZE_AMENDMENT_3_D1_D2_ROUTE_DECISIONS_20261116.md` item 6 (room calls are served).
- The accepted native read: `distill_design/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`; `B/events/native_r2/STATUS.md`, `NATIVE_READ_DETAIL.md`.
- Kit C8r, the backend build of job 170056: `B/events/native_r2/c8r_kit/` (code_c8r.tar sha256 f4535bc015da4a6e7f0d99e6db17a39fd49aa8d78dcf0a47d0aa5241b507f134, FAMILY.json 0bfae7e4..., PIN_TABLE_C8R.md with its 46 checks, PACKET.json, ORDER.md, C8_READY.md, review `B/events/review_c8/REVIEW_VERDICT_C8R.md`). GCS copy `q8/8865619b/evalx_native/code_f4535bc015da4a6e.tar`.
- Step 544's arm: return of job 170056, sha256 5c150bafb333117b2e026def36564b26cecf25bcdf9d536e5350c84fdef972a1, at Orchard `/project/community/jjyeung/okh7/n2r/b07a20b364`, `gs://cmu-gpucloud-jjyeung/q8/n2r/b07a20b364/`, trinity-1-13 `/scratch/jjyeung/orch_n30/native_r2/work/full_c8r/` (do not stage anything on trinity-1-13: 71 GB free).
- The VSTI kit V1c built on C8r's factored preparation (shows how scale and gravity preparation runs in the job, and the Orchard packet fixes): `B/events/native_r4/STATUS.md`, `B/events/review_vsti/CONFIRMED_dc40cf60.md`. Port from it the fixes that are independent of the benchmark: `sbatch` resources given on the command line (the packet's own `gpu:h100:1` is rejected), no hard links in input tars.
- How D0 exports are published and staged: `B/events/cont_ops/STATUS.md` (section "Orchard read job for m100/m200"), `READS_PLAN_D0.md`, `D0_JOB_B_PACKET.md`; the `.done` record is plain text `<object without bucket> <bytes> <sha256>` at `x_f5c353f7/o/gcs_359fcc3c_m<step>.done`. The reviewed D0 direct read kit (lane cont_ops, `work/d0/readk/` on trinity-1-3, confirmation `B/events/review_d0r/CONFIRMED_read_kit.md`) already stages a D0 export: reuse its export stager unchanged.
- The frozen distance list comes from brief 02 (`DISTANCE_LIST_DEVS1.jsonl` and its sha256); until it exists, build against the 150-item fixed list of job 170056 (TASKS a2f3fdbd).

## What to build
1. `guard_kit/`: C8r with exactly these changes, each listed in a DIFF.md line by line.
   - The export is a parameter: the candidate's `.done` record names object, bytes and sha256; the job stages that export and refuses any other. Every pin of PIN_TABLE_C8R.md is classified as export-dependent (re-derived in the job and written to the return: prepared geometry, own-head scale and gravity receipts, artifact sha) or export-independent (must equal job 170056's value; the job refuses on a difference).
   - One arm, native. All calls served, room calls included. A refusal or a non-answer scores 0 and stays in the denominator.
   - Item set: 450 camera items, the distance list, 36 room items, in the order of job 170056 for shared items.
   - Backend identity proof inside the job, before the candidate arm: re-read ten camera items and ten distance items of job 170056 with the step-544 export and require identical tokens, calls, responses and answers. A mismatch ends the job with a receipt; it is the evidence for "same backend build".
   - Orchard naming: review finding F6 of the native read says CONFIG and FAMILY keys and paths carry project, model and dataset words. Remove them from every job-visible name and path; show that only names changed (same code bytes elsewhere).
2. `guard_read.py`: candidate minus step 544, paired, per the rule: the three camera types (150 items each), metre distance on the frozen list, call rates (camera 450 of 450; metre distance at least 95%), room and non-metre distance printed only; percentile 95% intervals from a bootstrap over physical rooms, 10,000 draws, seed 20261115. It prints PASS or FAIL per guard and every interval. Unit from question text only, with the parser of brief 02.
3. `RUN.md`: exact prepare, packet and sbatch commands for STEP in {200, 400, 600, 800, 1000}, the fetch command (governed stream), and the ledger line for `work/ORCHARD_LEDGER.jsonl`.

## Tests (all must pass; logs in `out/`)
- Unit tests of `guard_read.py` (at least: paired bootstrap on a fixture with a known answer, refusal scoring, call-rate guard with one uncalled item, unit parser counts 43 / 28 / 46 / 33 on the fixed list) and a mutant run (every guard threshold flipped must fail a test).
- Whole-worker CPU rehearsal with the production CONFIG, changed only in transport (lesson of K1 job 170193), on a tiny model: stage, prepare, identity proof, native arm on 20 items, merge, admit, publish, fetch, report.
- CPU first batch of the real export is not possible locally; instead the in-job identity proof and a ten-item canary run before the full arm, and the job writes a canary receipt before spending the hour.
- `guard_read.py` run on job 170056's own return as both arms must give zero differences on every type.

## Do not touch
D0 job 170111 and its Orchard directories (read only the `.done` records and the GCS export objects); the VSTI job and pool `okh7/d9c35d0a`; the K1 pool `okh7/b7e31d84a90c62f5` and anything under `/scratch/jjyeung/k1` on trinity-1-18; the sealed C8r tar (work on a copy); the Orchard general queue order of `B/events/cont_ops/20261116T1102Z_ORCH_RULING_general_order.md`.

## Deliver
`out/GUARD_KIT_READY.md` (hashes, DIFF.md, tests, the pin classification table, time and disk estimate), a mirror of the kit on a second node over InfiniBand, STATUS.md in the events folder, and one RESULT event asking for the independent review. The review is a refute review by another model family of DIFF.md, the pin classification and `guard_read.py`; one review suffices. The guard read of a candidate is submitted only after that review, the list's sha256 in the init-rule record, and an ORCH GO.

## What might go wrong
- A pin that looks export-independent may hash a prepared output of step 544. The identity proof catches a real backend change; the pin table catches a relabelled one.
- D0 reset the routing-opener rows; if a candidate emits no call on camera items the guard fails by rule. Report the count, do not rerun.
- General holds one job per user. Estimate the job's time from job 170056 (2 h 35 min for two arms on 636 items) and set the limit to need plus margin.
