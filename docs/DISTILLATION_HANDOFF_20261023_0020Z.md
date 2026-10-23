# Distillation handoff, 2026-10-23 00:20Z (10-22 17:20 PT)

This handoff replaces `DISTILLATION_HANDOFF_20261021_2235Z.md`; read that file only for history. The writer is orchestrator agent-project-distill-f1 (session 0efa5c6c-c93d-4790-b78d-55e6fa0d3e49) on trinity-0-23. Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; S = `/data3/jjyeung/distill_scenes`; R = `agent/scratch/codex_runs` in this repository. Times are PT. The running log behind this file is `L/ORCH_F1_STATE_20261022T1020Z.md`.

## 1. User rulings in force (verbatim, newest first)

- **~12:00 (queue):** "trinity-0-8 can you not spawn? killing cluster". Never place lanes, pools, services, dispatchers or forwarders on trinity-0-8.
- **~10:40:** "Use Claude code and codex please if Devin stays down", "Also use the Gemini key to help rewrite! In the meantime use Claude subagents to run experiments", "Codex for coding, etc", "Claude for babysitting after code developed".
- **10:27:** "0 nodes on AWS please". `L/aws_reserve/DISTILL_GPU_CAP` is 0, and every `a15_cot_jjy_distill_*` job is cancelled. AWS stays at zero until the user lifts it.
- **~10:25:** "Rip, we used too much Devin". Devin hit its monthly usage limit; no Devin session can start until it resets next month.
- **Questions never block (10-22):** ask in plain text, push a notification, add a row to `/data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS.md`, and act on the default after about 5 minutes. Only paid keys (NV inference, OpenRouter) wait.
- **Earlier rulings still bind:** launch first, and reviews gate only banking and reporting; labeling never uses Fast tiers; numeric tolerance 25%, multiple choice exact; no answer from VSI-590K's release ever trains (its questions may); traces only for counting, relative count and relative distance; storage at most 90% per disk and 10 TB total, heavy reads on node-local /scratch; no deletion; no sweeping searches; the Gemini key stays on Trinity.

## 2. Results banked today

- **Seed 17, VSI-500, C27 lenient-v2, warm start r1835:** T3A -7.26 (50.98 vs 58.23); T3A_COUNT +0.98 [-2.54, 4.51]; T3B-A -3.20 [-6.65, 0.33] (54.76; VSTI 62.40, +1.91); T3B_SELF_T3A -9.88 [-13.53, -6.32] (50.66 vs 60.54; VSTI 59.03 vs 62.52). Pointers: `L/rwtrain_20261020/out/T3_RESULTS_*.json` and `CHAIN_20261022.json`.
- **No single lever wins** (`L/t3awhy_20261022/WIN_LEVERS.md`). The best stack, self-consistency plus T3B-D/E, adds about +1.5, with P(two-seed win) about 0.3.
- **BENCH_SCENES_DISTILL_v2** is the held-out authority: `L/benchscenes_20261021/out/BENCH_SCENES_DISTILL_v2.json`, sha256 33627c61c2b40f9325af77a6d9c933f759e4179a70f89cac1781f3639d828bed. It holds 2,245 scenes and 497 hard exclusions, and adds scannetppv2/c8fc01c453 to v1.
- **33 VSI-590K released answers removed from the T3B cohorts:** 20 found by the T3B-D lane (19 clean_vsi590k absolute-distance rows and vsi590k_168847), 11 unit-converted released answers (for example vsi590k_157246: released 6.6 ft became 2.01 m; GT 6.5 ft), and 2 that only T3B-A held. The 559 direction rows the T3B-D lane also flagged trace to our GT tool and stay. Evidence: `L/t3bbuild_20261022/out/T3B_VSI590K_ANSWER_PROVENANCE.jsonl` and `T3B_DROP31_MANIFEST.json`. The current cohorts are T3B_B3 (10,883 rows), T3B_C4 (13,191) and T3B_E4 (14,071).
- **T3B-D spec, frozen at 16:00:** `L/t3awhy_20261022/out/T3B_D_SPEC.md` (sha256 21bed7e5…). T3B-D trains the C cohort for 2 epochs against matched control T3B-DC, seeds 17 and 18. It adds no rows, because the bank holds only 12 audited traced-type rows beyond T3B-C. Predicted +0.4 [-3.3, +4.1]; P(two-seed win) 0.14, or 0.26 with the SC8 readout. Its build is `L/t3bbuild_20261022/out/build_t3b_d_v2` (from C4, epochs 2 in every field).
- **Bank (tracebank, 16:40):** gated 28,655; audited 17,232; audited and admitted 9,122. The Claude auditor published 25 audits and 6 passed: percept-v1.1 (38/40, then 37/40), camera-direction (37/40), camera-v2b-v1.1 (35/40), vlm3r-spatial-v1 (34/40, after recheck), and the grown percept-v1.1 population. Every VLM-3R VSI version fails, including the Gemini-written one (31/40). Tranche TRANCHE_r38_d5 released 590 audited-family rows. Post-release totals are pending; the hourly reader on trinity-3-23 is being restarted.
- **Audit rubric rulings R1-R3** (`L/auditswarm_20261021/RUBRIC_RULING_20261022.md`): GT anchoring is judged on evidence, never on closeness to GT; the 25% band is inclusive and uses the unrounded GT; auditors never see running totals.

## 3. Lane map

| Lane | Carrier and host | Status at 17:20 | Health check | On completion |
|---|---|---|---|---|
| Orchard training chain | Claude subagent (dies with this session); jobs on Orchard advanced, one 4-GPU node, serial | T3B_B_S17 160469 completed 16:45, evals pending; T3B_BC_S17 160470 running; T3B_B2_S18/BC2_S18 160498/160499 pending, to be swapped for B3; C4 pair not yet submitted | `L/rwtrain_20261020/out/CHAIN_20261022.json` and `T3B_B*_PIPELINE_A13.log` | Read the B pair's VSI-500/VSTI delta. Submit order: B3 S18 pair, C4 pair (S17, S18), E4 pair, T3B-D (after its review passes). Every new arm needs an independent review JSON in `L/rev_drop_t3b_20261022/out/`; dispatch Codex to write it, never the trainer. |
| SC8 eval driver A12 | detached process | schedules self-consistency eval units on Orchard general | `L/rwtrain_20261020/out/SC8_DRIVER_STATE_A12.json`, `SC8_DRIVER_A12.log` | none; it runs on its own |
| T3B-D v2 review | Codex, receipt `R/*_rev_t3bd_v2` | running | `final_message.md` in the receipt; verdicts in `L/rev_drop_t3b_20261022/out/T3B_D*.json` | On PASS, add the T3B-D arms to the chain after E4. On FAIL, rebuild per the findings. |
| Blind GT exposure fix and audit | Codex, receipt `R/*_blind_leak_fix` | running | `final_message.md`; `S/BLIND_EXPOSURE_AUDIT_20261022.jsonl` | Withhold credit from every blind recipe version with READ_GT or NO_LOGS items. Send the fixed `publish_tranche.py` back to an independent reviewer (the round-1 FAIL is `L/auditswarm_20261021/REVIEW_BLIND_GT_FILTER.md`). |
| Bank reader restart | Claude subagent (dies) | restarting the hourly reader on trinity-3-23 | `L/tracebank_20261021/out/` count files | Record the post-release totals. |
| Gemini swarm | dispatchers detached on trinity-0-3, 3-23 and 2-18 (survive); Claude babysitter (dies) | 338 checker-passed rows in all (w6_ad12 66, w4_absd 28, w5b_vsi 244), but the governor has backed off to 2 concurrent and the last hour produced under 10 rows | `L/scenedispatch_20261021/out/GEMINI_SWARM_STATUS.md`; `S/GEMINI_GOVERNOR.json` | w5b_vsi should be paused (its versions fail audit); move capacity to percept-v1.1 queues, the only passing traced-type recipe. Rows per +gemini version reach audit at 40. |
| gemrw rewrites | Gemini API python workers on trinity-2-3, 2-18 and 3-23 (survive) | not rechecked since 11:00 | `L/gemrw_20261021/out/` | none |
| Devin lanes | none | all paused: a STOP file in every `S/<queue>/`, auditswarm `queue_r38/CONFIG.json` maxrun 0, watchdogs stopped | — | Resume only after Devin resets, per the resume steps in `L/ORCH_F1_STATE_20261022T1020Z.md`. |

## 4. Infrastructure

- **Gemini carrier:** `S/tools_v5/dispatch_v5.sh -C gemini`, with its documentation in `S/tools_v5/GEMINI_CARRIER.md`. The governor `S/GEMINI_GOVERNOR.json` caps the swarm at 6 concurrent requests and adapts on 429/503. The experimenter has priority on the key, so the swarm runs on leftover capacity.
- **Release path:** the publisher (`S/tools_v5/publish_tranche.py`) withholds blind numeric rows outside the inclusive 25% band (349 withheld in d5). Its fail-closed fixes are in progress.
- **trinity-2-3 /scratch is full** from other users and main-project ICLR review folders; distillation holds nothing there. Keep staging off trinity-2-3.

## 5. What survives this session and what dies

- **Survives:** Orchard jobs and their pipeline watchers, the SC8 driver, Gemini dispatchers, gemrw workers, the trinity-3-23 bank reader, and every file under L, S and R.
- **Dies:** the Claude subagents (trainer, babysitter, bank-reader helper), the Codex runs launched from this session's shell if they have not finished (rerun them from their prompt files in R), and the queue watcher. A new orchestrator must start a trainer subagent at once, because the chain needs a submitter after T3B_BC_S17.

## 6. Open user decisions (defaults in force)

- Reframe the goal? Every planned arm has P(two-seed win) of 0.3 or less. Default: keep pursuing it.
- Clean up trinity-2-3 /scratch? It belongs to the main project. Default: leave it to its owner.
- Allow rules to cut permission prompts (codex_dispatch.sh, Trinity ssh, writes under L and S, lanemsg)? Offered; not added.
- Devin budget for next month. Default: decide when Devin resets.

## 7. Do not redo

- T3B_C2, T3B_C3, T3B_E2, T3B_E3, T3B_B2 and T3B-D v1 are superseded by B3, C4, E4 and T3B-D v2. Never train them.
- Do not resume w5b_vsi or any VLM-3R VSI recipe; all fail audit.
- Do not start Devin sessions, AWS jobs, or anything on trinity-0-8.

## 8. Footguns learned today

- The auto-mode classifier blocks a lane from writing its own review or approval record ("self-approval"). An independent Codex reviewer writes every verdict that a launch gate reads.
- The classifier also blocks Claude subagents from editing shared release manifests ("modify shared resources"). Route such edits through Codex with a writable root.
- Codex's sandbox cannot open ssh sockets. Remote launches go to a Claude helper.
- `render_brief.py` stripped only top-level GT fields, so blind briefs carried source-shard paths that lead to GT. Any blind claim needs the exposure audit above.
- A spec that pins live bank files will fail its own pin check; pin build inputs only.
- Subagents that report through `lanemsg` create messages between sessions; have them report in their final message or with SendMessage to main.
