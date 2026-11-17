# Codex build brief B1: selector rule without the null slot, plus per-call stage-1 diagnostics, for the own-arm reader (reader only)

Written by lane notseen_diag on 2026-11-17 and not dispatched; the orchestrator dispatches it. Suggested call: `codex_dispatch.sh implement <workdir> <this file> --model gpt-6-astra --effort high --label b1_nonull`. Workdir is a fresh folder on /scratch, for example `/scratch/jjyeung/orch_n30/notseen_diag/work/b1`. Do not ssh, kill processes or use Git, do not submit any job, and do not touch any file outside the workdir.

## Why
In H1-0's distance read (job 170706, step 544, own arm), 74 of 298 grounded (item, name) pairs print `<name>: not seen`. On 67 of them SAM 3 proposes the name with score >= 0.3 and pixels that survive the geometry-free eligibility cuts, in a median of 6 of the 32 frames. Job 170056's tower arm boxes 66 of those 67. Scaling the scene flips 19 of the 67 and 27 seen pairs. Every stage except the selector head is scale-invariant, so the selector head's learned null slot decides these reads (`DD/H1_0_NOT_SEEN_DIAGNOSIS_20261117.md`, Answer 1). All 33 capped reads follow such a response. The fix keeps the selector head and its weights and changes only the decoding rule: when candidates exist, pick the best candidate slot instead of letting the null slot refuse. The per-call records hold no candidate logits today, so the same build adds the diagnostics that settle the remaining 48 pairs (selector null or the own-depth spread cut).

## Inputs (the orchestrator stages these into `<workdir>/in/` before dispatch)
1. The full H1-0 package payload (`p`), which is the payload of package b01ec87a6f29b, 0.tgz sha256 446a4323. Two copies exist: Orchard `/project/community/jjyeung/okh7/e6fc152498/p446` and the CPU rehearsal tree on trinity-1-18 at `/scratch/jjyeung/b01ec87a6f29b/p`. A partial read-only copy (h1eval, tree/trace_format, tree/student_pilot/*.py, b/e2e_reader, b/heads/selector, orchard_h10, items, rows) sits at `trinity-1-3:/scratch/jjyeung/orch_n30/notseen_diag/work/f3/p446`.
2. The b04 reader tests and fixtures: `trinity-1-3:/scratch/jjyeung/n30_mirror/b04_e2ehook/b04_deliver_v7.tar` (`tests/`, `e2e_reader/`, `heads/selector/`).
3. The evidence bundle `EV/notseen_diag/notseen_evidence_20261117.tgz` (sha256 7a5b17d9), with `calls.json` and `pairs_cache.json` for expected-count checks. `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events`.

## Code the job runs (sha256 prefixes in the payload)
- `b/e2e_reader/stage1.py` dc9c9189. `StageOne.select` (lines 143-147) returns `-1` when the null slot wins. `sam3_detect` (line 99) applies joint >= 0.05 with cap 30.
- `b/e2e_reader/grounding.py` d9b7e6f3. `StageOneSocket.__call__` (lines 144-154) returns `[]` when there are no candidates or `choice < 0`, and records `self.queries`. `E2EGroundSession._instances` (lines 170-176) lifts with `lift_bestspread`.
- `tree/trace_format/box_v313.py` 395a4603. `ground()` (lines 513-524) prints `name: not seen` when `_instances` is empty, and `BoxRegistry.gap` (lines 226-228) prints the gap's `not seen`.
- `tree/student_pilot/routed_candidates.py` 9a200410: `lift_grid` eligibility (lines 69-84), `lift` (score floor 0.3 at line 99, 3x3 erosion and `no_eligible_pixels` at lines 106-109) and `link`.
- `tree/student_pilot/routed_features.py` 736c5a64: `accept_features` (lines 168-219) never drops a candidate.
- `b/heads/selector/selector_head.py`, `with_null`, and `b/heads/selector/sl118/selector_inputs.py`, which holds the 58 inputs.
- `b/e2e_reader/callhook.py`. `report()` (line 146) drops each record's `audit` key, so new fields need their own key.
- The import order is fixed by `orchard_h10/entry.py`, which puts `p/b` first, and `h1eval/h10/launch.py reader_factory`, which binds `--reader-root p/b`. `h1eval/reader_core/e2e_reader` is an older copy that the job does not import. Patch `b/e2e_reader` and leave `reader_core` alone.

## Changes
1. **Selection rule.** Add `rule` to `StageOne` and `stage1_factory` with two values:
   - `null_argmax` (default): today's behaviour, byte for byte.
   - `candidates_argmax`: when N >= 1 candidates exist, return the argmax over the first N slots of `with_null`, breaking ties at the lowest index. Return `-1` only when N = 0.

   Read the rule from the read settings (`settings['stage1_select_rule']`, default `null_argmax`). Include it in the read's identity and binding (`environment.json` binding, `IDENTITY`), so reads under different rules can never merge or resume into each other. Add no numeric constant and no threshold.
2. **Per-call diagnostics.** On every `<ground>` call, attach `stage1` to the call record, under its own key and not `audit`. Its fields:
   - `rule`, `name_key`;
   - SAM 3 proposals kept per frame: 32 counts, plus `max_score`, `max_presence`, `max_joint`;
   - proposals entering `lift` with score >= 0.3, proposals lifted, and rejections by reason (`no_eligible_pixels`, `invalid_pose`) taken from `lift`'s `rejected` list;
   - the number of linked candidates;
   - per candidate: id, frames, `peak`, the selector logit and the 58-input vector as float32 lists, cut to the first 30 candidates;
   - the null logit, the chosen index, and whether the null would have won.

   `gap` calls carry the operand states. These records must reach `items.jsonl` through `callhook.report()`. The printed response text must stay byte-identical under `null_argmax`.
3. **Own depth for offline replays (flag, default on).** Once per read, write the own-depth grid that `h1eval/perception.py own_profile` builds (32 x 51 x 51) as float16, with the own `pose9` and `gravity`, into a per-read `.npz` under the run output, plus its sha256 in the read record. That is about 170 KB per read. These arrays let any later selector or eligibility change be replayed on CPU without another GPU read.
4. **Read kit (build and rehearse; do not submit).** Build two package variants of H1-0 from the patched payload with `orchard_h10/build.py`, each under a new opaque token (never reuse b01ec87a6f29b): rule `null_argmax` and rule `candidates_argmax`. Each covers types [object_abs_distance], arm own, mode none only, and the 150 dev-S1 baseline items.
   - Orchard job names follow `a15_cot_ap` plus hex, and no project, benchmark, dataset, model or method word may appear on Orchard.
   - Estimated cost: 150 reads x about 25 s x 2 rules plus load, about 2.5 H100-h on Orchard general with one GPU each.
   - Rehearse on CPU from an empty root, exactly as the H1-0 rehearsal did (the package creates every bind source itself).
5. **Analysis script** `b1_report.py`, run on the two returned `items.jsonl`. It prints:
   - the per-call stage table (SAM 3 none; lift empty by reason; selector null with non-empty candidates; selected);
   - capped reads and not-seen reads per rule;
   - task MRA per rule and paired by room (bootstrap over rooms, 10,000 draws, seed 20261115), on all units and on the 43 metre items;
   - per-call gap |error| against GT in metres;
   - the per-name and per-dataset not-seen tables.
   Pre-registered predictions to print beside the results: under `null_argmax`, at least 60 of the 67 stage-D pairs of `pairs_cache.json` show non-empty candidates with the null winning; under `candidates_argmax`, at most 8 not-seen reads, at most 2 capped reads, and an MRA change of +2 to +6 points on all units and at least +8 on metres.

## Tests (CPU; all must pass, with the log in `<workdir>/out/TESTS.txt`)
- With stub propose and select (no SAM 3), `null_argmax` returns exactly what the current code returns on every b04 fixture and on the package's existing headcall, ground and box tests. Run the existing suites that touch `e2e_reader`, `trace_format` and `h1eval` (tests that already fail are reported with their cause and do not block).
- `candidates_argmax` returns a candidate whenever N >= 1 and `-1` only when N = 0. Planted variants must fail the tests: an off-by-one into the null slot, a rule that ignores settings, and a rule that changes the printed format.
- The `stage1` diagnostics are JSON-serialisable, bounded in size (assert under 64 KB per call), and survive `callhook.report()`.
- The rule is part of the read identity: a resume from a `null_argmax` journal into `candidates_argmax` is refused.
- EAT-1 static scan of the changed files: no new literal threshold, no alias table, and no file read outside the artifact's code roots in the decision path.
- The CPU first batch (`h1eval/h10/cpu_first_batch.py`, or the host wrapper's CPU mode) runs under both rules, if the staged inputs allow; otherwise state what is missing.

## Deliverables (in `<workdir>/out/`)
`PATCH.diff`, `TESTS.txt`, `REPORT.md` (what changed, file hashes before and after, both package tokens with manifest hashes, the rehearsal log, the exact submit command for the orchestrator, the price), `b1_report.py` with a fixture test, and `REMOVAL_CANDIDATES.md` if anything temporary remains. Review: a change in admission or legality? No, but the read decides a route rule, so ask the orchestrator for one cross-family review before submission.
