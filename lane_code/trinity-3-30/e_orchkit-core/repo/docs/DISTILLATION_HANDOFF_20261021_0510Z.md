# Distillation handoff, 2026-10-21 05:10Z (10-20 22:10 PT)

This handoff replaces `DISTILLATION_HANDOFF_20261020_0350Z.md`; read that file only for history. The writer is orchestrator session agent-project-distill-88 (session 4754b6b0-2bad-4b71-bfe1-52a02bb71305) on trinity-3-30. Notation: L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`; W = `L/devinwatch_20261004`; B = `agent/scratch/devin_lanes`; RW = `L/rewrite_20261014`. Times are PT.

## 1. User rulings in force (verbatim, newest first)

- **10-20 22:00 (relayed by experimenter orchestrator agent-project-fd):** the experimenter campaign has GPU priority over distillation on Trinity, especially for SAM3 servers. qwengen holds no trinity-0-18 card and claims none until the experimenter says otherwise.
- **10-20 ~20:05:** "I approve the signing (Recommended)" for OWNER_CALIBRATION_RECOVERY.v2.json. The permission classifier still blocks every agent from signing, so the user must run it (section 2).
- **10-20 13:35:** "https://arxiv.org/abs/2610.10478 does this help? Have a Devin explore."
- **10-20 ~07:45:** "Pack distillation's own files (Recommended)" on AWS: tar cold dirs under `split/distill/` only, verify, confirm synced to Trinity, then remove the originals.
- **10-20 ~00:45:** "rembmer, you can also use orchard! there you can use as many gpus as you can get your hands on"
- **10-20 ~00:35:** "remember 6:30am drop to 32 gpus". L/CODE_AWS_GPU_CAP is 32: qwengen 2 nodes, otaws 1, sprint 1.
- **10-20 ~00:20:** "call it a15_cot_jjy_distill_... aws is my account but it's much easier to get permission for a15_cot". The user confirmed the work is covered by a15_cot. Their own process cancels non-a15_cot jobs, so every distillation AWS job is named `a15_cot_jjy_distill_<rest>`, and the cap counts only that prefix.
- **10-20 ~01:15, the VSI-590K pipeline:**
  - "answer is from vsi 590k right? if our answer disagrees, ig drop the question"
  - Qwen attempts each question; a strong agent fixes its reasoning from SPLIT, canonical or GT references.
  - "keep it with light restyle if nubers are wrong, i recommend 1-2 decimal digits max!"
  - "full set, but def balnced first tranche!"
  - Scene overlap with benchmarks is allowed; literal benchmark questions are dropped.
- **10-20 ~01:00:** "start finetuning on the rewritten traces now. devin is no logner free starting novemner. we need to get as many traces NOW and reword them NOW"
- **10-20 ~00:55:** "use use as many devin agents as needed, under 1000 concurrently you can use without my permission"; "i recommend opus 5.5 max thinking for error analysis".
- **10-20 ~01:20:** Qwen3.5-9B is the main student. Qwen3.8-27B is a second student, trained after the 9B R1 rung beats its answer-only control.
- **10-20 ~00:10:** gap-type Gemini collection moves to the main experimenter's REQ-232 collector (filed as REQ-20261020-283). MONITOR91 is retired.
- **10-20 00:28:** "use aws for collection too, not just the eval"
- **Earlier rulings still bind:** no deletion outside approved scopes, one Git owner, no sweeping searches, no self-approved launch clearance, banned hosts. Banned hosts are trinity-3-23, 0-28, 2-8, 2-23, 3-13, plus **3-3 (hung 04:55 10-20)** and **1-18 (sshd hung 16:00 10-20)**.

## 2. Open user decisions and actions

1. **Sign the calibration recovery authority.** The user approved it, but agents are blocked. The lane's waiter, PID 3275448 on trinity-2-13, launches the 90-case Devin-judge calibration within 5 s of `RW/work/round5_judge_v2/recovery_attempt17_v1/OWNER_CALIBRATION_RECOVERY.v2.json` appearing, and waits until 22:33 PT. The user runs two commands:
   - `sed` of `sign_owner_authority_attempt18.py`, changing the tag to `owner_sign_v2` and the output to `.v2.json`, into `sign_owner_authority_v2_user.py`;
   - `ssh trinity-2-13 /data2/jjyeung/envs/vllm/bin/python -B <dir>/sign_owner_authority_v2_user.py`. The output must end `CHECK rc 0`.
   
   If the waiter expired first, ask rewrite to re-arm one. The fallback, if the user declines, is the frozen Gemini verifier as judge (~138 rows/h at 8 workers; `RW/out/JUDGE_FALLBACK_SCOPE.md`).
2. **AWS tunnel load.** The tunnel hung three times on 10-20 (13-29 stuck connections each time) and is back since 21:55. Every lane now uses one persistent ControlMaster per host. A shared `ControlMaster auto` / `ControlPersist` entry for `code-aws` in `~/.ssh/config` was proposed and not applied; it is the user's call because it affects other projects.
3. **Ten September Orchard jobs** (149000-149003, 149178, 149195-149199) are pending on the user's account with SPLIT paths. They may compete with our 4 queued preempt jobs. Cancel them, or ask the main experimenter.
4. **Optional premise-MCQ probe** (from the arXiv lane): measure, per claim type, whether base Qwen can pick GT-true claims, and decide where rewrites state numbers versus hedge. See `L/arxiv2610_20261020/out/RELEVANCE.md`.

## 3. Results banked on 10-20

- **Why trace training lost about 12 points to answer-only (seed 17, 9B):**
  - The student asserts precise quantities it cannot see: 165 of 199 flips (tracegap, `L/tracegap_20261020/out/TRACEGAP_REPORT.md`).
  - First faulty premises: distance 120, direction 97, camera motion 48 of 378. The needed fact was visually recoverable in 122 cases and needed precise measurement in 210 (erroran, `L/erroran_20261020/out/ERROR_ANALYSIS.md`).
  - Camera motion (0/48) and room size (0/24) are never visible in the frames.
- **Rewriter bake-off** (same 100 B_sum questions, frozen verifier): Devin Astra 18/100 (C7 15/3), Opus 17/100 (C7 15/2), Devin Qwen-3.8-27B 1/100. Astra is the bulk rewriter and Opus secondary; Qwen is out. Evidence: `RW/out/R4D_RESULT.attempt15.json`, `RW/out/QWEN100_FROZEN_SCORING.v1/AUDIT.json`.
- **VSI-590K manifests PASSED admission review** at v4: 652,363 questions, 65,465 GT-agreed candidates, wording-proof benchmark exclusion, verified visibility. See `L/v590k_20261020/out/PUBLICATION.v4.json` and `REVIEW_VERDICT.v4.json`.
- **Qwen3.5-9B VSI-590K traces:** about 3,950 verified. Trinity shards 1-4 hold 1,954 (qwengen); Orchard shards 7, 11, 15 and 20 hold 2,000 (otorch). About 65% of outputs loop or hit the 8,192 cap, which is expected for the base model; the swarm rewrites them.
- **Open-teacher (Qwen3.6-27B plus GT tools):** camera continuation runs at about 15 strict acceptances per hour per two-card replica (94%). The displacement pilot reached 28/40 strict and 39/40 within 25%.
- **REQ-283 (Gemini Pro on 8,889 gap questions):** delivering, with 56 workers scaling toward 64. The first traces sit in `L/teacher_pilot_20261004/out/ACCEPTED_<type>.jsonl`.
- **The rwtrain smoke run** (24 steps on 4 rows, Orchard) passed as plumbing. Format readout: 3/20 capped and 8/20 unsupported numeric claims, so that readout measures the base model and was not a gate.
- **AWS file-count quota** recovered to about 3.0M free entries, an account-wide cleanup not ours. awspack freed 4,772 entries.

## 4. Lane map (watchdog: W/watch_host.sh on trinity-2-28, lanes file W/lanes_trinity-2-28_20261019.tsv)

| Lane | State and next action | Check |
|---|---|---|
| rewrite_20261014 (Round-5 swarm) | Parked on the calibration owner signature (section 2). Then calibration, then `RW/out/ROUND5_SWARM_REVIEW_REQUEST.v2.md` for rev_round5 (parked on it), then `RW/out/rows/TR_RW_live/R1_READY_2000.json`. Branch lane/rewrite_20261014 tip 76c66a98 in worktree `RW/work/repo_round5`; `RW/work/repo` stays detached at ec1c236 (frozen scorer). Owner renewal loop PID 2313459 on trinity-2-13: max 12 h from 19:28 PT; stop file `RW/work/calibration_capacity_plan_attempt17/owner_renewal/STOP`. | `RW/out/PROGRESS.md`, `RW/out/HEARTBEAT.log` |
| rwtrain_20261020 | Parked on R1_READY_2000.json. Trainer epoch 5530926d (bundle out/TRAINER_5530926.bundle), Qwen3.8 patch cb6a5282, helpers 9e39401e. Orchard advanced partition reserved. | `L/rwtrain_20261020/out/BLOCKED.md` |
| qwengen_aws_20261014 | Trinity v6c is stopped (experimenter priority on 0-18). AWS v6b/v6c may now resume (tunnel back 21:55; quota fine; 2 nodes). Commits in `L/qwengen_aws_20261014/work/.git`: be10eac0 (v6c_h018), 9193ee19 (v6b), e3925792 (parity-fixed runner). | `out/PROGRESS.md` |
| otorch_20261020 (Orchard) | A8 dc6cae08 (PASS v5). Shard 16 on 1 general H100; 4x8 preempt jobs queued. Claims come from `L/v590k_20261020/out/claims/`. | `out/REPORT.md` |
| openteacher_20261008 (Trinity 0-13) | Camera continuation; numeric pilots (36 object, 98 room, Gemma arm) on the local planner (PASS A55); displacement pilot done. Never reuse REQ-283 IDs. | `out/PROGRESS.md` |
| otaws_20261020 | Parked on `L/CODE_AWS_CONTROL_RESTORED_20261020c`, which now exists. aws_v4c 92fb187f; reconcile preflight_d2 (lost reply) before any retry. | `out/BLOCKED.md`, `NEXT.v2.md` |
| aws_sync_20261019 | Push mode from code-aws, 2 streams with ControlMaster. Mirror 267 GB / 344 specs. e5, t16 and coord requeued; awspack's two packed authorities are synced as tar mirrors. | `out/PROGRESS.md` |
| sprint_train_aws_20261014 | v4 admission PASS (da9ecc88); seed-18 cells within its AWS share. Not heard from since resume; check. | `S/out/PROGRESS.md` |
| tracecold_20261012, teacher_pilot_20261004, opsd, qwengen tutor, camopt lanes | Parked or retired. Wake each only with a new brief. | each `out/BLOCKED.md` |
| Review lanes rev_* | Done or parked. rev_round5 waits on ROUND5_SWARM_REVIEW_REQUEST.v2.md. Every reviewer writes verdicts; nobody else does. | lane `out/REPORT.md` |

## 5. What survives this session and what dies

- **Survives:** the trinity-2-28 watchdog and every Devin lane; the owner renewal loop (2313459); the rewrite waiter (3275448, until 22:33); Orchard jobs; AWS-side aws_sync workers; REQ-283 (main experimenter).
- **Dies:** this session's background watchers, the Git-owner subagents, and lane bindings to session 4754b6b0.
  - The watchers: the filtered queue watcher (`scratchpad/queue_watcher_filtered.sh`), the alerts watcher (`scratchpad/alerts_watcher.sh`), and the trinity-3-13 thaw watcher.
- **Successor actions, in order:**
  1. Run `lanemsg --orchestrator adopt` on every lane path in the lanes file, then read each lane's `mail/outbox/new/`.
  2. Re-arm the queue watcher (`agent/scripts/queue_watcher.sh`) and an alerts watcher that also fires on a stale `W/WATCHDOG_ALIVE_trinity-2-28`.
  3. Settle the calibration signature with the user.
  4. Start a new single Git-owner subagent for checkpoint requests.

## 6. Do not redo

- Do not retry the Qwen rewriter, rerun the tutor arm, or reconsider Fable for B_sum.
- Do not revive MONITOR91 or the REAUTH/RATE88 machinery.
- Do not hand-roll AWS admission: reuse sprint v4 (da9ecc88) or qwengen's wrapper (57cf1806).
- Do not re-run tracegap or erroran. Their benchmark diagnostics never enter training rows.
- Do not claim trinity-0-18 cards, or cards in the experimenter's allocation.
- Do not write any verdict, clearance or owner authority from an agent; the classifier blocks it, rightly.

## 7. Footguns learned on 10-20

- **Brief race.** A continuation brief written while a lane is still finishing loses to its DEVIN_LANE_DONE. Re-touch the brief so it is newer than out/REPORT.md.
- **Short receipts.** Receipts with a 5-minute freshness window need one atomic waiter in the executing lane, triggered by the signed file. Hand-offs across sessions missed the window three times.
- **NFS git status.** It takes 78-98 s on loaded trinity-2-28 and 2-7 s on quiet hosts. Run Git-owner work on trinity-0-8.
- **Parity check.** vLLM versus native-HF prompt-token parity caught a renderer-cache bug (0/50 with the cache on). Keep the gate.
- **Unfilled placeholders.** Lanes sometimes announce request files before writing them, or send a tell-all with placeholders unfilled. Verify that the file exists, and its sha256, before acting.
- **Publication versions.** v590k keeps versioning its publication, so admission must read the highest PUBLICATION.vN and its cumulative overlay, never a fixed version.
