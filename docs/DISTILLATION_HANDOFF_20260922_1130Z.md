# Distillation lane handoff (REQ-20260917-232), written 2026-09-22 11:30Z

## Command

P denotes `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918` throughout. This
checkpoint supersedes `docs/DISTILLATION_HANDOFF_20260922_0940Z.md` (commit `749306f` on main) for
everything that changed since 09:40Z; that document still holds the full-set-gate narrative and the
results tables in the checkpoints behind it. A successor reads section 8 (rulings), section 10 (next
steps) and section 9 (watchers) first.

The headline since 09:40Z: both outstanding gate reviews from that checkpoint landed PASS — the
partial-checkpoint scoring change and the Orchard 27B evaluation port. The Orchard admission fix's
*second* defect (`check_host_lease()`) is built and locally verified but its independent review is
stuck, because `/home/jjyeung` is completely full and the review dispatcher writes its receipt there;
a waiter process resumes it automatically once space frees. Home filled to 251G/251G at 10:02Z and
killed two live processes (the gtmeasure v1 generator, the Qwen 27B interim run) before every log,
marker and receipt in this lane moved to `/data2`. The corrected v2.5 compact-target build finished
and passed its own internal verify, but has not yet gone to the independent semantic-derivability
review the 08:50Z ruling requires before anything trains on it. A decode-speed misdiagnosis on Orchard
is resolved: OneThinker's real throughput is 47.9 tok/s, not 1.8, once `use_cache` is forced as the
production harness already forces it.

## 1. Runs in flight

**Four arm C matched-subset replicates**, launched 09:29-09:33Z, seed 17 (fixed by the trainer,
un-overridable), effective batch 32 (fixed), 3 epochs over 3,052 train rows = 286 steps. s/step below
is the most recent measurement recorded (pending-memory note, ~10:55Z); projected finishes are that
note's own arithmetic, not independently recomputed here.

| run | node / cards | mode | pids | WATCH log | s/step | projected finish |
|---|---|---|---:|---|---:|---|
| Qwen 9B arm C rep2 | trinity-0-18, cards 0-5 | FSDP world 6 | launcher 100045, torchrun master 100688 | `P/claude_student_launch_20260922T0515Z/qwen_armc_rep2/out/WATCH_qwen.log` | 128 s | ~2026-09-22 20:00Z |
| OneThinker arm C rep2 | trinity-0-18, cards 6,7 | DDP world 2 | 101665 | `.../onethinker_armc_rep2/out/WATCH_onethinker.log` | 74 s | ~2026-09-22 15:40Z |
| OneThinker arm C rep3 | trinity-1-3, cards 0,6 | DDP world 2 | 1775355 | `.../onethinker_armc_rep3/out/WATCH_onethinker.log` | 46.9 s (Ada cards) | ~2026-09-22 13:30Z |
| OneThinker arm C answer-only | trinity-1-13, cards 2,3 | DDP world 2 | 1278711 | `.../onethinker_armc_answeronly/out/WATCH_answeronly.log` | 57 s | ~2026-09-22 14:15Z |

Qwen's `max_microbatch_size` fix (cap raised from 1 to 8) is confirmed working: steps 1-3 measured
128.0s/127.4s/125.9s, a 2.3x improvement over the earlier 293 s/step at cap 1.

**Qwen3.6-27B, relaunched.** The prior interim-set run died at step 33/216 at 10:43Z when its
vnice-wrapper stdout log, hosted under `/home/jjyeung`, failed on the quota and killed the process
group (checkpoint `step_25` preserved on `/scratch`, diagnostic only). Relaunched as a fresh one-epoch
run on the **arm C set** (not the interim set), lane `P/claude_q27b_armc_relaunch_20260922T1110Z`,
host trinity-0-13, cards 0, 2, 3, wrapper pid **768915**, start `2026-09-22T11:06:30Z`, all logs on
`/data2`. `prepare-protocol` PASSED at 11:06:30Z: `train_rows: 3052`, `heldout_rows: 379` — the arm C
split reproduced exactly. `prepare-training` started at 11:07:44Z; **no completion line or training
step had appeared in `out/PREPARE_full.log` as of this checkpoint's last read** — whether the run has
begun optimizing is unconfirmed (see section 11).

**Qwen arm A r6 VSIBench evaluation**, trinity-0-23 (supervisor pids 95829/95830): no source assigned
to this checkpoint updated its status; carried forward unconfirmed from the 09:40Z checkpoint. The
`qwen_r6_eval_watch.sh` watcher covers it (section 9).

## 2. Collector: r1313 recovered and stable; r1317 not reconfirmed this window

**r1313 (trinity-3-8).** Stopped finalizing 07:36Z on a silent lease-renewal failure (last heartbeat
07:03:59Z); watchdog and controller both died; recovered by 08:27:38Z (first finalization) and held
44/44 workers clean for 30+ minutes by 09:06:06Z, finalized **25,008**. Total outage ~36 minutes. Live
pids as of that record: **watchdog 212703, controller 215319, package guard 120283, lease-heartbeat
keeper 213556** (20-hour cap, replacing an earlier 4-hour-cap keeper pid 212370 that was killed and
superseded). `setw.sh` itself had a bug (`$n` vs `$N` under `set -u`) that aborted every worker-count
call silently; fixed in place (scratch orchestration script, not `collector/` source). No finalized
count more recent than 25,008/44 at 09:06:06Z was available to this checkpoint —
`collector_health_watch.sh` (section 9) fires at 26,000.

**r1317 (trinity-1-13).** No source assigned to this checkpoint carried a fresh read; carried forward
unconfirmed from the 09:40Z checkpoint (VSTIBench-style epoch, live on trinity-1-13). `r1317_watch.sh`
(section 9) covers controller death, 429s, terminals flat 30 minutes, terminals reaching 3,300, or
lease age past 1,500s.

## 3. Decode-speed diagnosis resolved: OneThinker was never slow, the probe was broken

Two distinct causes, both closed:

**Bug A (the Orchard sizing probe only).** `gen_probe.py` called `model.generate()` with no
`use_cache` override, so it inherited OneThinker-8B's shipped `generation_config.json`, which carries
`"use_cache": false`. With no cache, the model re-encodes all 32 frames and the whole growing context
on every decode step — measured 1.8 tok/s, reproducing the observed 0.547 s/token exactly. **The
deployed harness was never affected**: `benchmark_eval/generate.py:117-119` has forced
`use_cache = True` since 2026-09-18, so production OneThinker evaluation runs at its real rate. Every
throughput number the probe produced before this fix (jobs 147462, 147475) is discarded.

**Bug B (production Qwen3.5-9B and Qwen3.6-27B on trinity).** These models have Gated DeltaNet
(linear-attention) layers that fall back to a slow torch implementation when
`flash-linear-attention`/`fla-core`/`causal-conv1d` are absent — which they are in trinity's
production venv. This explains the persistent 14-22 items/h for Qwen evaluations on trinity against
243 items/h for OneThinker on the same harness; a corrected trinity evaluation venv is in progress
(section 9).

**Corrected, authoritative throughput** (job 147480, `use_cache` forced exactly as the harness forces
it): OneThinker-8B on one H100, **47.9 tok/s decode, 0.71 s prefill**, 397.6 items/h at 400 generated
tokens — a 25x correction over the discarded 16.1 items/h. VSIBench (500 items) now sizes to **1.26
h**, VSTIBench (450 items) to **1.13 h**, both well inside a single 12-hour Orchard `general` job.
Qwen3.6-27B on one H100 (single-device mode, no sharding needed): **18.5 tok/s decode, peak 54.0
GiB**; at its realistic thinking-off length (~100 tokens) that is about an hour per benchmark.

## 4. Orchard: capacity, deployed code, and the live training blocker

**Capacity, from real Slurm limits (`sacctmgr show assoc user=jjyeung`):** `general_qos` allows
exactly one 1-GPU job at a time; `adv_4gpu_qos` allows 4 GPUs on one node, no preemption, 24-hour
jobs; `preempt_qos` allows up to 32 GPUs across 4 nodes but its projected start is about 2026-10-02, so
it is a lottery ticket only. Working concurrent capacity is **4 H100s (advanced) + 1 H100 (general) =
5**. Measured H100-over-RTX-6000-Ada speedup: **1.77x** (3.369 s/microbatch H100 vs. 5.959 s Ada, both
32.2 GiB peak).

**Deployed code.** Trainer `51d1372` (`orchard-admission-local-gpu-index-20260922`, includes the
reviewed `issue()`/`admission_probe()` fix) at `code/orchard_trainer_51d1372`; deployment `a0551b5` at
`code/deployment_a0551b5`; Orchard 27B eval port `bd628a8` (reviewed PASS this window, section 5) at
`code/orchard_eval_bd628a8`; 27B harness `d65bd2b` at `code/harness_qwen27b_d65bd2b`. Node-local
dataset staging (`stage_dataset_local.sh`) is built but not yet exercised past admission — it needs no
trainer change (the reviewed code already permits redirecting reads to `/tmp/jjyeung`) and should cut
arm C's prepare time from an extrapolated 17 minutes to under two.

**The live blocker.** Jobs **147468** (Qwen 9B arm C) and **147470** (Qwen3.6-27B) both FAILED at
`bind-lease-ddp` ("Physical device differs from Slurm-bound device") after clearing admission's
`issue()` cleanly on `51d1372` — proving the round-1 fix works and that the *next* gate,
`check_host_lease()`, carries the identical physical-vs-cgroup-local-index defect. A fix
(`7b691ad` + `386702e`, on the same branch) is committed and locally verified — 12/12 `test_orchard`,
the two real DDP callers (`bind_leases`, `require_rank_lease`) directly exercised and passing — but
**not yet independently reviewed and not yet deployed**: its round-3 review is held on the
`/home/jjyeung` disk-quota incident (section 5). Advanced partition sits idle until it lands; the arm
C chain submitter (`$ORCH/submit_armc_chain.sh`) is staged and fires in one command once it does. The
general-partition evaluation slot is idle for the identical reason (the same `issue()`/
`check_host_lease()` path gates evaluation leases too).

**Evaluation venv.** `venv_eval` = `flash-linear-attention` 0.5.2 + `fla-core` 0.5.2 + `einops` 0.8.2,
**without `causal-conv1d`** — the PyPI 1.7.0 build was ABI-broken against this torch (undefined
symbol) and was removed; `fla` falls back to a torch short convolution without it. If the conv kernel
turns out to matter, it needs building against this exact torch rather than pulled from PyPI. A
`--thinking off` launcher patch for Qwen base-control evaluations is written but **blocked**: editing
`eval_job.py` under `/data2` was refused twice by the permission system ("Instruction Poisoning", then
"Modify Shared Resources"); it needs either an operator to apply the patch by hand or a permission
rule for that path.

## 5. Gate reviews concluded this window

- **Partial-checkpoint scoring, round 3: PASS.** Commit `c7c7c789` (unchanged across all three
  rounds). Round 1 and round 2 both FAILed on review-setup defects, not code defects; round 3 applied
  the repository's actual test-gate rule (tests touching the change plus its new tests must pass; other
  failures are recorded, not blocking) and passed on direct evidence — 42/42 parent tests still pass at
  the child commit plus 2 new tests, both worktrees left clean. Ready to wire into the arm C replicates
  and the Qwen 27B run so a preemption still yields a scoreable number.
- **Orchard Qwen3.6-27B evaluation port (`bd628a8`): PASS.** All five asked-for guarantees confirmed
  with independent evidence (byte-identical scoring/prompting vs. parent, device-gate parity, a
  reviewer-constructed lease-mismatch probe correctly refused, adapter-loading round-trip checked
  tensor-by-tensor, the full 79-test suite green). One non-blocking correction: this session's own
  review brief mis-stated a baseline test count (51 vs. the true 9+42); not a code or lane defect.
- **Orchard admission `check_host_lease()`, round 2 (`a54fd46`): FAIL**, recorded for context — it
  required the full physical-index/UUID/local-index list, but the real DDP callers
  (`bind_leases`/`require_rank_lease`) narrow `CUDA_VISIBLE_DEVICES` to one index at a time, so it
  broke both. The round-1 regression test missed this because it called `provisional.bind_lease()`
  directly, bypassing the DDP narrowing.
- **Orchard admission `check_host_lease()`, round 3 (`7b691ad` + `386702e`): not yet reviewed.** Held,
  not overridden: `codex_dispatch.sh` derives its receipt path unconditionally from the repository root
  under `/home/jjyeung`, which has 0 KiB available. A waiter (pid 3744262, log
  `P/claude_orchard_admission_fix_20260922T0925Z/review3/wait_and_dispatch.log`) polls
  `df --output=avail /home/jjyeung` and dispatches automatically once it exceeds 5,000,000 KiB.

## 6. Datasets

**Arm C matched subset (3,431 rows) — the set actually training now.**
`candidate_index.jsonl`:
`/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl`,
sha256 `530663315143fa6202983cdad82c8bc4375c1c6f9b111f230ceebe09410ea80c`. Split:
`/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6_republish_20260920T045138Z/split.json`,
sha256 `4dd7467fd3b63b6a124bebf7c9a7be1749e3ac7696f6c7acaaaa49755efe4083`, train 3,052 / held-out 379.

**v1 full set — FAILED its independent gate; nothing trains on it.**
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_compact_interim_full_20260922`,
render commit `d9e3d57`, 17,058 candidates + 1,600 deferred = 18,658 index rows, train 14,123 / held-out
2,935, MANIFEST sha256 `12aa5cf40016baffd9162b69bb45fa3fac172687475ba75f51734020e495eb3b`. Independent
review FAILed 2026-09-22 08:22Z
(`agent/scratch/codex_runs/20260922T082638Z_fullset_review_20260922T0822Z`) on semantic derivability
(8 of 12 sampled targets: numbers with no stated operands, radial-distance-only observations where a
direction question needs coordinates, "unspecified units" beside a metres question) and on training
having begun before approval. Dataset-mix correction from the same review: 64.55% scannetppv2 admitted
(11,011/17,058) against arm C's matched membership at 7.29% (250/3,431) — the claim that every
published student used a uniform 21% mix is unsupported by this set.

**v2.5 corrected full build — rendered and internally verified, but not yet independently reviewed.**
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/diagnostic_set_compact_v25_full_20260922`,
generation commit `5411443032a449fe6d3181b0aab2ca07c88fa55d` (branch `compact-v2-5-20260920`,
previously reviewed PASS on its own 1,378-row build), config_sha256
`d6ca6ef4beb4d4b8bd4ead9cac6b0f62622d6f77558a6476f1475e1b05bd7e86`. Input 18,692 round-3 strict
sources; admitted **2,856** (2,130 train / 726 held-out); deferred 15,836. `verify`: VERIFIED, all
replay flags true, zero calls/GPU. Split gate: PASS, train 2,130 / held-out 726 across 196 train / 30
held-out scenes. `training_eligible: false`, `independent_review_required: **pending**` — this build
has not yet been sent to a fresh gate review, so the 08:50Z ruling's condition ("make sure it passes")
is not yet met (see section 10, next step 3). The frozen 3,431-row slice inside this build reproduces
v2.4.3's reviewed admission set byte-for-byte (659/659 rows) and matches arm C's train/held-out
assignment and rendered student input exactly (570 rows). Four numeric/measurement question types
(`object_abs_distance`, `object_rel_distance`, `object_size_estimation`, `room_size_estimation`) admit
**zero** rows by explicit, named refusal rather than a defective render; per the coordinator's ruling
these families are intentionally deferred to the gtmeasure sets below, not recovered in this build.

**GT-measurement v1** — died mid-run at the home-quota incident (169/306 scenes complete;
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/gtmeasure_v1_20260922`), resumed
for the remaining 137 scenes into a sibling directory,
`.../gtmeasure_v1_20260922_resume` (generator pid 3757857, watcher pid 3758261, marker
`FULL_GENERATION_V1_DONE` under `P/claude_gtmeasure_v1_resume_20260922T1040Z/`), rate roughly 1
scene/minute or a little below, projected finish **~13:00Z**. The two directories are not yet merged.

**GT-measurement v2** — full-set generation in progress,
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/gtmeasure_v2_20260922`, structure
v2 (intermediate GT observations — extents, centres, camera positions — before the answer;
byte-identical final answers to v1), repo commit `53cd73ef4a5a9444c7ba43690d89ec80caae6039` (reviewed
PASS), generator pid 3602895, watcher pid 3603440, marker `FULL_GENERATION_V2_DONE` under
`P/claude_gtmeasure_v2_verify_20260922T0758Z/`. Rate ~1.66 scenes/min at its first direct measurement;
the most recent note (10:55Z) puts completion at **~11:35Z**, superseding the earlier ~11:09Z estimate.

**Pending mixes — commands derived and verified against the mixer's contract, not yet run** (waiting
on the v2 completion marker). `tools/gtmeasure/mix.py`'s `--ratio` sets the gtmeasure share of the
mixed **training** side only; held-out rows from both sources are always kept in full. Both planned
calls use the arm C `split.json` (sha256 `4dd7467f...`) and the default seed 17.
- Set A (pilot): `--compact-dir` = arm C's `diagnostic_set_compact_v1c_dropclause`, `--gtmeasure-dir`
  = `gtmeasure_v2_20260922`, `--ratio 0.25`, `--output .../mix_armc_gtm2_r025_20260922`.
- Set B (corrected): `--compact-dir` = `diagnostic_set_compact_v25_full_20260922`, `--gtmeasure-dir`
  = `gtmeasure_v2_20260922`, `--ratio 0.5`, `--output .../mix_v25_gtm2_r050_20260922`.

## 7. Home-quota incident

`/home/jjyeung` (`nebby.ib:/exports/home4/jjyeung/brick`) sat at **251G/251G, 0 bytes free**, both at
the census's start (10:18Z) and finish (~10:4xZ). `quota -s` refused every check ("Connection
refused" — the quota daemon itself is unreachable), so the finding rests on `df -h` and directory
sizes only. `/data2` had 172G free of 209G (18% used) at the time. No `du`, `find`, `ls -R`, or
`grep -r` swept the whole of any of `/home/jjyeung`, `/data2`, or `/data3`; every size below came from
a directory named in a task brief or a plain single-level `ls`.

**What the full quota killed or degraded:** the Devin CLI (writes `$HOME/.local/share/devin`, so
every Devin-lane launch fails while home is full); Codex receipt writes (blocking the Orchard
admission round-3 review, section 5); memory appends; the **gtmeasure v1 generator**, which died at
scene 169/306 when its home-hosted log write raised an unhandled disk-quota error; the **Qwen 27B
interim run**, which died at step 33/216 when its vnice wrapper's home-hosted stdout log failed the
same way and killed the process group; and Orchard ssh, which needed a `CLOUDSDK_CONFIG` wrapper
redirecting `gcloud`'s config to `/data2` because the IAP tunnel's `ProxyCommand` runs `gcloud`, which
could not write its own config under a full home.

**What was relocated:** every lane log, marker and receipt going forward writes to `/data2`, never to
`/home`; the gtmeasure v1 resume and the Qwen 27B relaunch both write every log and wrapper stdout to
`/data2`; the stale interim-run 27B watch log was repointed to
`claude_home_full_20260922T1020Z/WATCH_q27b.log` (that run is now dead; the fresh relaunch's own log
paths live under its own new lane, section 1).

**Census, top consumers** (nothing deleted or moved; `du -sh` on the two full repos timed out at
90s/180s/300s, so their true totals are higher than shown):

| path | size | note |
|---|---:|---|
| `/home/jjyeung/agent_project` (whole repo) | at least 74.5G measured | `devin_lanes/` alone 69.4G across 275 entries, `.git` 5.1G; du itself never finished |
| `/home/jjyeung/agent_project_distill` (whole working tree; live collector's source) | 14G | `.git` 29M, `devin_lanes/` ~13.5G across 59 lanes |
| `/home/jjyeung/.codex` | 6.9G | Codex CLI session/cache |
| `/home/jjyeung/cot-filler` | 5.7G | |
| `/home/jjyeung/agent_project_astra_self_improve` | 5.6G | |
| `/home/jjyeung/.claude` | 3.7G | holds session memory; excluded from cleanup outright regardless of size |
| `/home/jjyeung/.cursor-server` | 3.3G | regenerable |
| `/home/jjyeung/.local` | 3.3G | `.local/share/devin` is 1017M of it |
| `/home/jjyeung/.vscode-server` | 739M | regenerable |
| `/home/jjyeung/.devin-server` | 966M | regenerable, caution: live Devin lanes may be attached |

The single largest lane is `agent_project/agent/scratch/devin_lanes/r1326_v17_fixpass2_abort_handoff_20260921`
at 4.9G. **None of the 274 measured lanes in `agent_project/agent/scratch/devin_lanes/` carry a
`DEVIN_LANE_DONE` marker** (checked individually, including one level deeper into `out/` for the
largest), so under the stated safety rule none of that ~69.4G qualifies as a cleanup candidate without
either a different completion criterion or an explicit user list of which lanes are actually
abandoned — this is the single biggest blocker to freeing real space.

**Deletion queue for the user — nothing here has been touched; this is a request for the user's
decision, not a plan to act unilaterally:**

Confirmed safe (duplicate or fully-merged work, ~12.7M combined):
- `agent_project_distill/agent/scratch/devin_lanes/answer_line_unit_fix_20260921T2355Z` (12M) —
  `DEVIN_LANE_DONE` present, worktree clean, 0 commits ahead of `main` / 3 behind; its content already
  landed as commit `d9e3d57`.
- `agent_project_distill/agent/scratch/devin_lanes/qwen27b_student_20260922T0545Z/out/devin_test_tmp`
  (678K) — a smoke-test scratch subtree only; the lane's live orchestration files (`run_q27b.sh`,
  `watch_qwen27b.sh`, `RESUME_RECIPE_q27b.md`) must stay, since the 27B job still reads them.
- `agent_project_distill/agent/scratch/devin_lanes/claude_compact_v25_typecap_20260922T1015Z/out/devin_xdg/data/devin/credentials.toml`
  (331 bytes, confirmed present by direct check) — a duplicate Devin credentials file inside a lane's
  XDG staging directory, named in this checkpoint's own task brief.
- `/project/community/jjyeung/probe_256m.bin` and `probe2_256m.bin` on Orchard — carried forward from
  the 07:00Z ruling, still queued, unchanged.
- Four items carried forward from the 06:00Z checkpoint, described there but without paths this
  checkpoint's sources restate: a stale index-lock-class file renamed aside 2026-09-21 05:26Z, a
  link-latency probe directory, one stray `.nfs_probe` file, and one stray placeholder file. A
  successor should re-locate these before queuing them for deletion (see section 11).

Regenerable caches (safe in principle, ~12.1G combined, but each deserves a live-process check first):
`/home/jjyeung/.codex` (6.9G), `.cursor-server` (3.3G), `.vscode-server` (739M), `.devin-server` (966M,
caution: live Devin lanes may be attached), `.npm` (161M), `.cache/flashinfer` (23M), `.cache/devin`
(14M).

Explicitly **not** safe to remove: `agent_project/agent/scratch/devin_lanes/` in full (274 lanes,
~69.4G, zero `DEVIN_LANE_DONE`); `agent_project_distill`'s `gt_measurement_supervision_20260922T0620Z`
/ `gt_measurement_v2_20260922T0735Z` / `vstigen_membership_v4_20260922T0000Z` (DONE-marked but 2, 3
and 7 commits respectively ahead of `main` — real unmerged work); `orchard_eval_qwen27b_20260922T0905Z`
and `partial_checkpoint_scoring_20260922T0810Z` (DONE-marked orchestration files tied to the live 27B
job); `qwen27b_student_20260922T0545Z` outside `devin_test_tmp`; both repositories' `.git` directories;
`/home/jjyeung/.claude` outright; and the two working trees themselves.

## 8. Rulings (user, 2026-09-22, verbatim where quoted — unchanged from the 09:40Z checkpoint)

1. Collector key budget: **"You can go up to six million"** — the shared Gemini key's cap, in tokens
   per minute, across every collector drawing on it.
2. Lenient scoring is primary. Never penalize a correct answer given in the wrong format; strict
   parsing stays secondary.
3. Every GPU on the cluster is usable. Never ask for allocation — find idle cards over ssh and claim
   them. Leave every other experimenter's running process untouched.
4. vnice is required only above 16 large GPUs held in total on trinity; below that threshold it is
   optional. Orchard has no vnice at all — Slurm allocation, QoS and preemption govern there instead.
5. Maximize Orchard's use. Preemption is acceptable — partial results plus resume are preferred over
   holding out for an uninterrupted run.
6. 08:50Z, on the failed full-set gate: train on the 3,431 clean arm C rows meanwhile, and reword the
   remaining rows so the review passes — **"Make sure that it passes."** Interpretation carried forward
   into this window's work: the arm C replicates in section 1 satisfy the first half; the v2.5 build in
   section 6 satisfies the re-render but **not yet** the "make sure it passes" half — it has not been
   sent to a fresh independent gate review (next step 3, section 10).

Other-experimenter GPU handover channel and Gemini key sharing, both unchanged from the 09:40Z
checkpoint: no new release or 429 event was reported to this checkpoint.

## 9. Watchers a successor must re-arm

Six scripted watchers live under `P/claude_orchestrator_watchers_20260921T2330Z/`, read-only, none
kills or restarts anything; each writes its own `.log` and fires (prints one line, exits 0) when its
condition trips. Re-arm any whose process is not found running, using the same script and log path.

- `collector_health_watch.sh` — polls `WATCHDOG_HEALTH.json` for r1313 every 120s; tracks pids 212703
  (watchdog), 215319 (controller), 120283 (guard); fires on a 26,000-finalized crossing or a
  health-file problem. (The lease keeper is now pid 213556, 20-hour cap; this watcher's own header does
  not track it separately.)
- `r1317_watch.sh` — ssh's trinity-1-13 every 300s for the r1317 controller's health line; fires on
  controller death, any 429, terminals flat 30 minutes, terminals reaching 3,300, or lease age past
  1,500s.
- `training_watch.sh` — polls WATCH logs every 120s via its own array (`qwen9b_rep2`, `ot_rep2`,
  `ot_rep3`, `ot_answeronly`) pointed at the four arm C replicates' logs under
  `P/claude_student_launch_20260922T0515Z/`; fires on any log stale past 600s, any run's step flat
  1,500s, or any run reaching its final step. **This array does not include the Qwen 27B relaunch** — a
  successor should add a fifth entry once the 27B run's own WATCH log exists (section 1 notes none was
  found as of this checkpoint).
- `qwen_r6_eval_watch.sh` — polls the Qwen arm A r6 evaluation's rate logs every 300s against
  supervisor pids 95829/95830; fires on staleness past 1,200s.
- `census_exit_watch.sh` — polls the r1313 light census (pids 1595879/1600988) every 120s; fires when
  it exits.
- `trinity38_thaw_watch.sh` — watches for trinity-3-8 to answer again after its 2026-09-21
  freeze/reboot; its condition has very likely already fired, since the node has been running the
  collector for hours; confirm from its own log rather than assume it is still armed.

Not standalone scripts, but processes a successor must track directly (from the pending memory this
checkpoint distilled):
- **Home-space recovery**: no scripted watcher exists; check `df --output=avail /home/jjyeung`
  directly. The Orchard admission round-3 review waiter (pid 3744262, log
  `P/claude_orchard_admission_fix_20260922T0925Z/review3/wait_and_dispatch.log`) is itself polling this
  value and auto-dispatches once it exceeds 5,000,000 KiB.
- **gtmeasure v2 generator**: pid 3602895, watcher pid 3603440, marker `FULL_GENERATION_V2_DONE` under
  `P/claude_gtmeasure_v2_verify_20260922T0758Z/`.
- **gtmeasure v1 resume generator**: pid 3757857, watcher pid 3758261, marker
  `FULL_GENERATION_V1_DONE` under `P/claude_gtmeasure_v1_resume_20260922T1040Z/`.

## 10. Next steps, in dependency order

1. Free `/home/jjyeung` — this needs the user (deletions are not this session's to make); once free
   space passes 5,000,000 KiB the Orchard admission round-3 review dispatches automatically (waiter pid
   3744262). On PASS, redeploy the trainer and resubmit the arm C + 27B chain under fresh run IDs (both
   currently sit failed at `bind-lease-ddp`); this also unblocks the Orchard general-partition
   evaluation slot.
2. Wire the now-PASSED partial-checkpoint scoring change (`c7c7c789`) into the four running arm C
   replicates and the Qwen 27B run, so a preemption still yields a scoreable number.
3. Send the corrected v2.5 full-set build (section 6) to a fresh independent semantic-derivability gate
   review — it is rendered and internally verified but has not yet been reviewed, so the 08:50Z ruling's
   "make sure it passes" condition remains open.
4. Confirm the Qwen 27B relaunch has reached actual training steps (not just `prepare-training`); watch
   the four arm C replicates toward their projected finishes; watch r1313 toward the 26,000-finalized
   watcher trip and re-check r1317's status directly, since no fresh read was available this window.
5. Merge the two gtmeasure v1 directories once the resume run completes; watch gtmeasure v2 to its own
   completion marker; then run the two prepared mixer commands (Set A ratio 0.25, Set B ratio 0.5).
6. Apply the `--thinking off` launcher patch to Orchard's `eval_job.py` once an operator or a permission
   rule allows editing under `/data2` — needed before any Qwen base-control evaluation there.
7. Bring the full deletion queue (section 7) and any newly-provisional rulings to the user for
   confirmation.

## 11. Not verified when this was written

Whether the Qwen 27B relaunch (wrapper pid 768915, trinity-0-13) has progressed past
`prepare-training` into actual optimizer steps is unknown; no WATCH log or step count for it was found
in this checkpoint's sources. The r1313 collector's finalized and worker counts beyond the last
recorded 25,008/44 at 09:06:06Z are unconfirmed. The r1317 controller's current state on trinity-1-13
was not reconfirmed by any source assigned to this checkpoint. The Qwen arm A r6 VSIBench evaluation's
progress past its last recorded checkpoint is unconfirmed. gtmeasure v1's exact scene count at the
resume run and gtmeasure v2's exact completion time are both estimates, not confirmed completions —
both generators were last observed alive and progressing, not finished. Whether either of the two
prepared mixer commands (Set A / Set B) has run is unknown; both wait on the gtmeasure v2 completion
marker, which had not appeared as of the last read. Whether `trinity38_thaw_watch.sh`'s condition has
actually fired was not reconfirmed from its own log this window. The exact current paths of the four
small deletion candidates carried forward from the 06:00Z checkpoint (the stale lock, the link-latency
probe directory, the `.nfs_probe` file, the placeholder file) were not restated in any source available
to this checkpoint and would need to be re-located before queuing them for deletion.

None of this blocks further work. The rulings in section 8 are already in force as stated; none is
provisional.
