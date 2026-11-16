# Review verdict: VSTI-450 camera-only native read kit V1b (code c.tar 7895f182, docs tar 899a213b)

Reviewer: lane review_vsti (Devin, trinity-1-3), 2026-11-16 08:50-09:50Z. Read-only; tests ran on copies under `/scratch/jjyeung/orch_n30/review_vsti/work/`.

## Verdict: GO AFTER FIXES

The legality design holds. The scorer copies are byte-identical, and the comparator reproduction reruns exactly. Three defects would still produce a wrong number or no number, so each must be fixed before submission. F1 makes the kit's own scorer give 0 to every answer the student writes in its trained `<answer>…</answer>` form. F2 and F3 would probably stop the job at start on Orchard. The should-fix items (S1-S8) are cheap and protect the single slot or the public number.

## Must fix

**F1. The kit scores the fuzzy path, not the authority's primary metric.** Location: `code/scorer.py:16-21` (`score`).
- What it does: `value` comes from `official_fuzzy_matching(answer)`, which is `answer.split(' ')[0].rstrip('.')`. The authority's `primary_score` comes from the strict `parse_answer_v1` path (`s0.py:688-708`, `category_scores` from `by_cat_strict`).
- Effect: the step-544 student ends numeric answers with `<answer>1.31</answer><|im_end|>`. In job 170056's return (`from113/work/full_c8r/result.tar.gz`, `native/paired/results/items.jsonl`), 146/148 abs-distance and 34/36 room answers have this form; camera answers are bare. The kit then scores `0.0` while `parsed_answer` is `1.31`. I reproduced this with `out/fmt.py`: `<answer>1.31</answer>` against GT 1.31 scores 0.0, and `<answer>B</answer>` against GT B scores 0.0.
- Why the tests missed it: `comparator_check` calls `score_our_cell` directly and never calls the kit's `score()`. The comparator texts have strict equal to fuzzy, the rehearsal's synthetic answers are bare, and the canary checks only `parse_status=='ok'`.
- Consequences: any type the student answers in tag form (camera_obj_abs_dist is likely) would score near 0. It would also be paired against f17 and P1 m200 strict scores (`report.py:68`), which use a different metric.
- Fix:
  - `score` = `official_exact_match(parsed_answer, gt)` for MC or `official_mra(official_to_float(parsed_answer), …)` for numeric when `parse_status=='ok'`, else 0.
  - Keep the fuzzy value as `official_fuzzy_score`.
  - Add a test that runs the kit's `score(final_text(...))` over both comparator files and matches their recorded `score` (my run: 0 differences on all 900 rows with the current code, because the comparator texts are untagged), plus the two tagged strings above.
  - Add a canary check that native scores equal the strict recomputation.

**F2. The packet lives in the login node's /tmp, which the job cannot see.** Location: `code/o.py:42-49` (`packet`) and `out/RUN_ORCHARD.md` ("/tmp/d9c35d0a").
- `a.sh` runs `exec /usr/bin/python3 … /tmp/d9c35d0a/<token>/o.py run --config /tmp/…/a.json` and sets `#SBATCH --output=/tmp/…/a.log`. On an Orchard compute node, `/tmp` is a job-private ext4 overlay (`distill_design/ORCHARD_STACKED_TMP_MOUNTS_20261113.md`, job 169107 mountinfo). The packet files and the output directory therefore do not exist inside the job, which then fails at its first line.
- C8r avoided this by embedding its payload in the batch script and writing `--output=/dev/null` (`orchard_launcher.py:53-95`).
- Fix: write the packet to an opaque directory on the shared `/project/community/jjyeung/okh7/…` tree, or embed it the C8r way. Point `--output` at `/dev/null` or a shared opaque path.

**F3. The read namespace uses the host's bwrap.** Location: `code/venue.py:72` (`args=['/usr/bin/bwrap',…]`), used by `o.py:157` for both the prepare and the read phases.
- C8r stages and authenticates its own `bwrap` (`FAMILY parent_config.assets.bwrap`, sha e3189038; `native_stage.py:440-442`; `orchard_job.py:120`). The proof namespace keeps using it, but the new read namespace does not. Whether `/usr/bin/bwrap` exists on Orchard compute nodes is unestablished.
- If it is absent, the first read-namespace phase (prepare) fails, and no VSTI item is read.
- Fix: replace `argv[0]` with `str(root/'bwrap')` for the Orchard read namespace.

## Should fix

**S1. The read namespace forces `CUDA_VISIBLE_DEVICES='0'`.** Location: `venue.py:85` via `o.py:157` `gpu=0`. C8r passes the allocation's value through (`orchard_job.py:142`). Fix: pass `os.environ['CUDA_VISIBLE_DEVICES']`.

**S2. Any proof exception kills the VSTI read.** Location: `o.py:163-167`. A nonzero exit from `p.py` (call error, replay mismatch, OOM, a staging-path error in the new proof staging) raises before the read phase. `a.py:44` also needs `/r/p/PROOF.json`.
- Continuing on token divergence is right: the proof is a reproducibility receipt, and the canary independently gates the read.
- Exceptions should behave the same way. Record `PROOF.json` with `failed`, continue the read, and print "proof failed/diverged" on the report's Primary line. Today the outcome appears only on a separate line.

**S3. The GPU parity gate runs on a VSTI item under camera_only.** Location: `engine.py:207-208`, which executes `nomdg.py:419-477`.
- The gate fails if the probe decode has any `call_errors`, and a refused call counts as an error. One `depth_at` or `ground` in the first VSTI camera item would therefore stop the read before item 1.
- Fix: run the parity probe on a dev-S1 camera item that 170056 already proved, or count refusals separately from call errors.

**S4. Items on geometry-refused captures score 0 without decoding, for every type.** Location: `engine.py:246-248` with `geometry_refusals.item_refusals`. Non-camera VSTI items need no geometry under camera_only, yet they would be zeroed while f17 and P1 answered them.
- Fix: decode these items with every call refused, `move`, `turn` and `pose` included.
- Otherwise: state the count of auto-zero items per subtask on the headline.

**S5. Partial types are reported as scores.** Location: `report.py:41-47` and `report.py:98-101`.
- The first job is expected to end partial (SIZING: 3,440-34,400 s of "other" items).
- Per-type and per-subtask rows then show means over the completed id-ordered prefix, labelled only by an item count.
- Fix: label rows with fewer than 50 items "partial n/50" and withhold their score, or print the label in the score cell.

**S6. The headline does not name the subtasks with refused calls.** Location: `report.py:95`. The text "includes subtasks with refused calls whenever present" is generic. Fix: name the subtasks and their refused-call counts on that line.

**S7. The deadline margins can cut the report.** Location: `o.py:162`, `budget.py:27`, `a.py:41-47`.
- The read subprocess is killed at exactly deadline−300 s, which is the same instant at which the item rule stops starting items. An item that overruns its projection then kills merge and report; only journals return.
- The 300 s return reserve covers pool publish (120 s timeout) plus GCS cp, describe and cat (up to 180+60+180 s) only if they are fast.
- Fix: stop starting items at deadline−420 s, or kill the subprocess later than the item stop.

**S8. The frame checks have two gaps.** Location: `pixels.py:28-43`. The check records `decoded_frames` but never asserts that it equals `selection.total_num_frames`. Fix: assert the equality. In `adapter.prepare`, also compare every scene's `frame_indices` with `agent/selected_frames_vstibench.json` and record the differences (see item 4).

## Findings by brief item

### 1. Legality
- **Served calls.** On a VSTI item, only `move`, `turn` and `pose` are served. `policy.py:16-27` patches `carrier_c1_decode.respond_state`, which is the only dispatch path (`carrier_c1_batch_decode.py:139` looks up `D.respond_state` at call time). Every other name returns the fixed string before the original dispatcher runs.
- **Source of the served values.** They come from the tower run in the job on this read's 32 frames, through `engine.tower` and `prepare_geometry`, then `perception.camera_geometry`. The pose is scaled by `tower_scale_rule.estimate`. That rule takes the median of the student-depth/G3T ratio over points above the median confidence within 0.1-10 m. It has no fitted constants, and its rule file says `frozen_before_gt`. Gravity comes from the student's head.
- **Grounding backend.** `ground_backend` is None in `NativeBoundary.generate`, and `perception.backend` (the `native_selector` profile) is never called.
- **Benchmark-derived assets in the read namespace.**
  - Not bound: `root/d` (proof inputs), `root/sj` (C8r masks `mask_recall_run`, raw G3T `raw_g3t_20261114`, `legs1_routed/CAMERA_GT*`) and `root/project`. The exceptions are the trainer tree and `producer_bridge`, which are code. Bindings are at `o.py:147-156`.
  - Bound but off the call path: the code archive `/x` still ships `MASK_CACHE_C8/P6_BOUND.json` and `mask_kit/kit_combo3.tar.gz`, which contains `selector_geom.py`, vocabularies and an ITEMS list. They are reachable as files but not reached by any call. Hardening (optional): after the canary, assert that `kitlib`, `variantlib`, `native_selection` and `hrp.selector` are absent from `sys.modules`, and record the result.
- **Labels.** Labels are written only to `SCORES.json` (`adapter.py:103-104`) and read only by `score()` and the report. `/d/c.json` and the comparator files sit in the read namespace, so the separation holds by code, not by namespace. This is acceptable.
- **dev-S1 proof.** The proof runs after VSTI preparation, in its own process and namespace. It writes only `/r/p`, and the read takes only `PROOF.json` from it. Its inputs cannot change VSTI decoding.
- **What the heads were trained on.** Step-544's run 469ddece has data receipt `inputs/data_receipt.json`. It applies `BENCH_SCENE_EXCLUSIONS_v2` (sha 3119aa4a), which lists VSTI's 312 ScanNet val scenes (142 rooms), to the vqa, pointing, pose and routing sources (all PASS; pose rows 194,987). So the gravity and pose heads' last training excludes VSTI scenes.
- **Not verified:** the depth head's lineage before step 544, i.e. the parent CP1/m200 runs and the depth assets `97a6a3eb/b19c1200/step_400`.
- **Audit status of the serving rules** (POLICY_AUDIT_20261115): camera route #4 C (disclosed), budget #18 C, gravity guard #21 C so far, scale #20 U, selector #13 not used. The camera-only read is legal under §7 as built. The report should disclose #20 as unaudited.

### 2. Refusal policy
- The string is `error: call_unavailable; answer directly from the video` (`policy.py:7`). It matches the runtime's trace-3.13 error wrapper (`student_pilot/trace_format313.py:29`).
- **Not confirmed: that the student was trained on it.** `distill_design/ROUTED_READ_FIRST_ITEMS_169605_20261114.md` (section C) finds 0 of 165 sampled routing rows with an error, not-seen or unresolved response. The row generator also stops before a gap when a ground fails. Job 170056 has 0 error responses in 634 native decodes. `LEGALITY.md` and `DECISIONS.md` call these "trained refusal bytes". The claim should change to "runtime error format; no trained recovery", which is what the refused-call cost then measures.
- **Decoding continues.** The response is injected and decoding proceeds, bounded by the 2,048+64 thinking budget and 200 calls.
- **Refused items count.** A refused item is scored by its final answer and counted. No final answer scores 0.
- **Unknown tags stay text.** The extra-tail pattern matches only `reader_policy.CALL_NAMES`.

### 3. Scorer
- `s1.py`, `s2.py` and `s3.py` are byte-identical to `/home/jjyeung/agent_project/agent/evaluation/{scoring.py, _score_index_vstibench_mechanical.py, score_record_core.py}` (sha f67703ea, 2e685ee0, 503a16f1).
- `s0.py` (0bb536ca) is `score_and_aggregate.py` from the Orchard official tree. The main repository has no copy, so I could not hash-check it against an authority file.
- The five-subtask collapse (`scorer.collapse`) equals `VSTI_PRIMARY_GROUPS` and the mean of 5.
- I reran the reproduction (`out/check.py`; output `work/sc/SCORER_CHECK_rerun.json`, sha 61c0caeb): f17 66.95 and P1 m200 68.71, 0 per-item mismatches, collapse equal. The kit's own `score()` is wrong for tagged answers (F1).

### 4. Frames
- **Source.** The 32 frames per scene are the comparator reads' sets: selection files pinned by `media.json` from the vstibench_repr450_v2 generation, `floor(k*(N-1)/31)`, decoded with av 15.1 from `/data2/.../vsibench_videos`.
- **Index lists against VSTI's list.** VSTI's own list is `agent/selected_frames_vstibench.json`. Two of the 311 VSTI scenes differ from the formula by one ordinal: scene0609_02 at positions 9, 17 and 18, and scene0690_00 at position 17. Their questions (q1639, q1981) reference frames 13 and 8, which are unaffected. The two sample scenes (scene0025_01, scene0019_00) match exactly.
- **Not checked:** the other 309 scenes' video frame counts, because they need the selection files from `/data2`.
- **What the five-scene pixel check can show:** for those 5 scenes, release-decode against kit pixels at the same ordinals, plus the frame count once S8 is in place.
- **What it cannot show:** the other 306 scenes. It also cannot separate a video difference from a decoder difference (av 17.1 against 15.1).
- **Caveat.** The report states it on its own line (`report.py:58`).

### 5. Job
- **Phases.** stage, then prepare (tower and own scale/gravity), then proof, then read (canary of 10: 4 camera and 6 other; then 96 camera; then 344 other).
- **Deadline.** Items stop when the next one cannot finish by 16:15Z−300 s, but S7 applies.
- **Return.** The return runs on any failure (`o.py:170-184`). A full project filesystem fails only the pool channel, and the GCS channel is independent (`orchard_results.publish`). The return cap of 300 MB fits by my estimate (311 prepared npz of about 0.35 MB, plus journals).
- **Resume.** Resume skips the proof and reruns parity. I did not verify that the returned archive's layout extracts to `RESULT.json` at the top level.
- **Orchard /home.** Nothing is written under it; the root is the job-private /tmp.
- **Opaque names.**
  - Clean: the job name `a15_cot_ap`+token, the pool and GCS paths, and `/x` and `/r` in argv. The inherited C8r names are unchanged.
  - Leak: `REPORT.md` and `REPORT.json`, generated on Orchard and returned through pool and GCS, contain "VSI-Bench", "VSTI", "ScanNet", "G3T", "f17" and "dev-S1" (`report.py:7`, `report.py:58`). Fix: build the report on Trinity from the returned journals, or neutralize the text.
- **Proof divergence.** Continuing past token divergence is right. Exceptions should not be fatal (S2).
- **Parity.** See S3.
- **Packet location.** See F2.

### 6. geometry.py
- The refactor moves the C8r body into `prepare_capture` with the same operations. The prefill function is the same: `closed_adapters(no_grad(_prepare_decode))` at `geometry.py:145` and `engine.py:49`. Only the order changed: the anchor check now runs before the batch is built.
- `tower()` adds `gravity_up` capture and a CPU device option.
- The builder's `GEOMETRY_CPU.json` reports bit-identical scale, camera_to_world, K, guard decision, prefill digest and diagnostics on a real raw cache with synthetic heads. I read the record and agree with the code reading; I did not rerun the test.

### 7. Report
- Present: per-type and per-subtask call, served and refused counts; scene intervals with room sensitivity; refused-call cost with answer distribution; same-item comparisons labelled "other models"; the proof line.
- Gaps: S4, S5 and S6. The paired differences inherit F1.

### 8. Unexecuted lines (first-start and first-GPU-step risks no rehearsal ran)
- `a.py` (both phases), all of `o.run`, the read namespace as built (bindings, bootstrap entry `/x/a.py`, bwrap, CUDA), the namespace runtime (native_bootstrap with entrypoints `a.py` and `p.py`), model load inside the read namespace (FSW, AP and tree paths only; no `/project/community` logical mount), tower on GPU, and parity on a VSTI item. Also unexecuted: the proof staging copytree, the `p.py` import mix (C8r out2 first on the path, the kit's engine and scorer), resume extraction, and the return of a 311-capture read.
- The operator namespace rehearsal used a different binding set (the whole native_r4 tree) and a fixture tower, so it does not cover these paths.

## What I read and what I did not
- **Read:** the diff in the docs tar and all new kit files (`a.py`, `adapter.py`, `budget.py`, `engine.py`, `entry.py`, `o.py`, `p.py`, `paths.py`, `pixels.py`, `policy.py`, `proof.py`, `proof_stage.py`, `report.py`, `scorer.py`, `u.py`, `venue.py`). Also the relevant parts of `s0.py`, `perception.py`, `gravity_guard.py`, `geometry.py`, `geometry_refusals.py`, `nomdg` parity, `native_stage`, `native_bootstrap`, `orchard_results`, `orchard_launcher` and the trainer's decode dispatch. Also `FAMILY.json`, `LEGALITY.md`, `DECISIONS.md`, `SIZING.md`, `RUN_ORCHARD.md` and the head of `UNEXECUTED.md`; 170056's items; the data receipt and exclusions; POLICY_AUDIT, ROUTED_READ_FIRST_ITEMS_169605 and ORCHARD_STACKED_TMP_MOUNTS; and AGENTS.md sections 3 and 7.
- **Not read:** `boundary.py`, `orchard.py` (the fallback path), the builder's tests, most of `UNEXECUTED.md`, C8r's `S.namespace` environment helper `J.environment`, and the Trinity fallback runbook.
- **Not run:** the kit's test suite, any GPU path, and any Orchard command.

## Claims I could not confirm
- That the student was trained on the refusal string. Evidence points the other way.
- That `/usr/bin/bwrap` exists on Orchard compute nodes.
- That Slurm's `CUDA_VISIBLE_DEVICES` is 0.
- The depth head's training lineage before step 544.
- That `s0.py` equals an authority file.
- That the other 309 scenes' video frame counts equal the release counts.
- That the returned archive layout supports resume.
- The proof and parity outcomes on H100.
