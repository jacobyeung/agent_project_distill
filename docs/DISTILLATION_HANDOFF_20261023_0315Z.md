# Distillation handoff, 2026-10-23 03:15Z (10-22 20:15 PT)

This handoff replaces `DISTILLATION_HANDOFF_20261023_0020Z.md`. The writer is orchestrator agent-project-distill-f1 (session 0efa5c6c-c93d-4790-b78d-55e6fa0d3e49, trinity-0-23). By user instruction ("please passoff to the next distill orchestator"), f1 stands down, and agent-project-distill-0e owns every distillation lane from now on. Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; S = `/data3/jjyeung/distill_scenes`; R = `agent/scratch/codex_runs` in this repository. Times are PT unless marked Z.

**Read first:** `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_DISTILL_ORCH_20261023T021445Z.md`. It holds the user's answers relayed by orchestrator agent-project-1d (AWS 128 GPUs tonight, proposed 64 for distillation until 06:30 PT 10-23, and Gemini). f1 never read it, so the AWS line below may be out of date.

## 1. User rulings in force (verbatim, newest first)

- **20:15:** "please passoff to the next distill orchestator".
- **Early afternoon (queue, relayed by agent-project-8c):** "btw don't use devin until november! prefer claude". Claude subagents run lanes. The user told f1 directly: "Codex for coding, etc" and "Claude for babysitting after code developed".
- **Late morning to early afternoon (queue):** "Try not to hammer data2", "just don't launch thousadns of processes at once", "We are over 91% on /data2! Remember max 90% on each data drive. Also remember 10TB total", "you can also consider transferring ~4TB to /data3 since it has 24TB free." New run roots and large outputs go to /data3 (`/data3/jjyeung/distill_builds/` holds build outputs); keep under about 200 processes per node, and start at most 8 workers per node per minute.
- **~12:00 (queue):** "trinity-0-8 can you not spawn? killing cluster". Nothing goes on trinity-0-8.
- **10:27:** "0 nodes on AWS please". `L/aws_reserve/DISTILL_GPU_CAP` is 0. The INBOX above may lift this for tonight; read it before launching AWS work, name every job `a15_cot_jjy_distill_*`, and never put the Gemini key on AWS.
- **~10:40:** "Use Claude code and codex please if Devin stays down", "Also use the Gemini key to help rewrite! In the meantime use Claude subagents to run experiments".
- **Standing:** questions never block (plain text, push, a row in `/data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS.md`, act on the default after about 5 minutes; only NV inference and OpenRouter wait); launch first, and reviews gate only banking and reporting; labeling never uses Fast tiers; numeric tolerance 25%, multiple choice exact; no training target ever derives from a VSI-590K released answer (its questions are allowed); traces only for counting, relative count and relative distance; no deletion; no sweeping searches; a buggy harness is never the agent's fault, so fix the harness.

## 2. Results

- **T3B_B seed 17 ties its control, the first T3B trace arm that does not lose.** VSI-500 55.87 vs 55.56, +0.31 [-3.39, 3.99]; VSTI-450 59.79 vs 59.15, +0.64 [-2.96, 4.17]. Per type on VSI: counting -12.6 [-22.4, -3.2], easy relative direction +14.0 [6, 24], relative distance +8.0, route -8.0. With thinking off the arm scores 59.47. Both arms sit about 4 points below r1835 (59.51). The pair shares 38 rows whose targets derive from VSI-590K released answers, disclosed in `L/rwtrain_20261020/out/CHAIN_20261022.json`. Readout: `L/rwtrain_20261020/out/T3_RESULTS_T3B_B.json`.
- **Earlier seed-17 results:** T3A -7.26; T3A_COUNT +0.98 [-2.54, 4.51]; T3B-A -3.20 [-6.65, 0.33]; T3B_SELF_T3A -9.88 [-13.53, -6.32].
- **Held-out authority:** `L/benchscenes_20261021/out/BENCH_SCENES_DISTILL_v2.json` (sha256 33627c61…; 2,245 scenes, 497 hard exclusions).
- **T3B-D spec, frozen** (`L/t3awhy_20261022/out/T3B_D_SPEC.md`, sha256 21bed7e5…): the C cohort trained for 2 epochs against matched control T3B-DC, seeds 17 and 18. Predicted +0.4 [-3.3, +4.1]; P(two-seed win) 0.14, or 0.26 with SC8.
- **Audit rubric rulings R1-R3:** `L/auditswarm_20261021/RUBRIC_RULING_20261022.md`.

## 3. Released-answer rows and the cohort lineage

Independent reviews keep finding training targets derived from VSI-590K released answers: 20 by direct copy, 11 by unit conversion, and 10 more whose frozen direct rows carry `target_provenance.source = ground_truth` but pin released offline-label files (`L/rev_drop31_t3b_20261022/out/PROVENANCE_BLOCKERS.md`). B3, C4 and E4 therefore failed review.
- **Running now:** Codex t3b_dropall (receipt `R/20261023T025249Z_t3b_dropall`). It traces every row's answer to its source file, builds T3B_B4, T3B_C5 and T3B_E5 without any released-answer row, rebuilds T3B-D v3 from C5, and writes `L/t3bbuild_20261022/out/T3B_DROPALL_MANIFEST.json` and `REVIEW_REQUEST_T3B_DROPALL.md`. If this session's end kills it, rerun it from `R/t3b_dropall_20261022.md`.
- **Next:** an independent review of the dropall build. The reviewer writes the verdict JSONs that the submit scripts assert into `L/rev_drop_t3b_20261022/out/`; the trainer never writes them.
- **Never train** T3B_C2, C3, C4, E2, E3, E4, B2 (beyond the job already running), B3, or T3B-D v1/v2.

## 4. Lane map (no Claude subagent of f1 is alive; the user stopped them)

| Lane | Where | State at 20:15 | Check | Next action |
|---|---|---|---|---|
| Orchard training | Orchard advanced partition, one 4-GPU node, serial | 160498 T3B_B2_S18 running since 18:38; 160499 T3B_BC2_S18 queued (about 20:35). Both carry 18 shared released-answer rows (disclose). | `L/rwtrain_20261020/out/CHAIN_20261022.json` | Start a new Claude trainer subagent. Two armed scripts in `L/rwtrain_20261020/out/` act on their own: `dropall_auto_a13.sh` preps, reviews and queues C5, and `c_fallback_v2_a13.sh` queues the C3 seed-17 pair at about 22:30 if C5 is not cleared. Decide whether C3 (14 released-answer rows) may run, or hold it. |
| T3B-D | builds in `L/t3bbuild_20261022/out/` | v2 review FAIL: the old wrappers assert epochs == 1. The new wrapper `L/rwtrain_20261020/work/rung1_orchard_job_v3se.sh` (sha256 37696691…) passes its tests. | `L/rwtrain_20261020/work/REVIEW_REQUEST_T3B_D_WRAPPER.md` | Independent review of v3se.sh and of T3B-D v3 (from C5). Queue the four T3B-D runs (6 h limit) after the C5 and E5 pairs. |
| SC8 eval driver A12 | detached | running | `L/rwtrain_20261020/out/SC8_DRIVER_STATE_A12.json` | none |
| Bank | hourly reader on trinity-3-23 (python PID 1703520 under `timeout 24h`) | **Unverified drop:** after the counter fix, audited fell from 17,232 to 7,873 and audited-and-admitted from 9,122 to 3,649. The likely cause is the fix withdrawing credit from versions whose pooled audit failed, but confirm it before quoting any bank number. | `L/tracebank_20261021/out/hourly_runtime_g9c_r38.log` and `out/bank_r38/` | Reconcile per-version credit before and after the fix. |
| Blind exposure | `S/BLIND_EXPOSURE_AUDIT_20261022.jsonl` | 90 items, 824 released blind rows: no READ_GT and no NO_LOGS, but Devin's logs omit tool calls, so 767 Devin-written rows (qgen-absdist-v1.2, vlm3r-spatial-v1.1, percept-v1-ad-v1.2) cannot be shown clean. The 57 Gemini rows are clean. | receipt `R/*_blind_leak_fix` | Default: withhold the 767 Devin rows. `render_brief.py` (allowlist) and the fail-closed `publish_tranche.py` are live; the publisher needs an independent re-review (round-1 FAIL: `L/auditswarm_20261021/REVIEW_BLIND_GT_FILTER.md`). |
| Gemini swarm | dispatchers detached on trinity-0-3, 3-23 and 2-18; no babysitter | 338 checker-passed rows; the governor has backed off to 2 concurrent; nearly idle | `L/scenedispatch_20261021/out/GEMINI_SWARM_STATUS.md` (last updated 17:30), `S/GEMINI_GOVERNOR.json` | Pause w5b_vsi (all VLM-3R VSI versions fail audit). Run percept-v1.1 queues, the only passing traced-type recipe. |
| gemrw | Gemini API workers on trinity-2-3, 2-18 and 3-23 | not checked since 11:00 | `L/gemrw_20261021/out/` | none |
| Devin lanes | none | all paused (STOP files in every `S/<queue>/`, auditswarm maxrun 0, watchdogs stopped) | — | Stay paused until November per the user. |

## 5. Open user decisions

Distillation rows in the saved-questions file: count at most 2 audited rows per question toward 250,000 (default yes); an ARKitScenes camera-alignment gate (default not before 11-01); single-image sources (default video first). Also open: whether to reframe the goal (every arm has P(two-seed win) of 0.3 or less; default keep going), and allow rules to cut permission prompts (offered, not added).

## 6. Footguns

- The auto-mode classifier blocks a lane from writing its own review or approval record, and blocks Claude subagents from editing shared release manifests. An independent Codex reviewer writes verdicts, and Codex makes manifest edits.
- Codex's sandbox cannot open ssh sockets, so remote launches go to a Claude helper.
- Provenance tags lie: `target_provenance.source = ground_truth` can pin a released label file. Trace every answer to the file it was read from.
- A spec that pins live bank files fails its own pin check; pin build inputs only.
- Subagents that report through `lanemsg` create messages between sessions. Have them report in their final message or with SendMessage to main.
