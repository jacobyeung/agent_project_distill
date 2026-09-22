# Distillation lane handoff (REQ-20260917-232), written 2026-09-22 09:40Z

## Command

P denotes `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918` throughout. This
checkpoint supersedes `DISTILLATION_HANDOFF_20260922_0600Z.md` for everything that changed since
06:00Z; that document still holds the full results tables and their derivation. A successor reads
section 6 (rulings), section 7 (next steps) and section 8 (watchers) first.

The headline since 06:00Z: the full 17,058-row compact training set failed its independent gate
on semantic derivability, so nothing trained on it. The user ruled to train the arm C 3,431-row
matched subset as seed replicates meanwhile and to fix the full set so a re-review passes. The
r1313 collector also stopped and recovered. Orchard training is still blocked on one admission bug.

## 1. The full-set gate failed; the user's fix is in flight

The interim full build (`diagnostic_set_compact_interim_full_20260922`, 17,058 candidates, render
commit `d9e3d57`, `BUILD_RECORD_FULL.md` at `P/claude_source_generation_recovery_20260922T0600Z/`)
went to an independent Astra gate review at 08:22Z
(`agent/scratch/codex_runs/20260922T082638Z_fullset_review_20260922T0822Z/final_message.md`).
The verdict is FAIL. Replay, the zero-call check and split inheritance all passed: the manifest
hash matches, both pinned modules carry none of the seven provider-call tokens, and the split
gate reproduces 14,123 train / 2,935 held-out rows exactly. But of 12 sampled targets, 8 fail on
derivability — numbers with no stated operands, radial XY-and-Z distances where a direction
question needs coordinates, tool scalars with no derivation shown, and "unspecified units" beside
a metres question. The build's own manifest already marked `training_eligible: false` and
`independent_review_required: true`; the reviewer's concern (a) is that training began anyway,
before that review landed.

The build record's own caveats (`BUILD_RECORD_FULL.md` sections 1, 8, 10) explain why: the stage-1
tool that turns raw teacher traces into row/target/checks sources
(`student/compact_targets/compact_v25_ingest.py`, v2.5 Devin clone, HEAD `5411443`) had only ever
run inside that clone, so 10,211 of the pool's traces were never converted before this recovery
lane's round 3 (see `docs/DISTILLATION_HANDOFF_20260922_0600Z.md` section on the compact pipeline
for the recovery). Round 3's output then went through the **v1 renderer** (`compact_counted_v1.py`
at `d9e3d57`) rather than the reviewed v2.5 renderer — a composition the v2.5 review never covered.
The build is also 64.55 percent scannetppv2 against 21 percent in every published student, so any
comparison against arm C or v1c-XL needs the matched 3,431-row subset as control, and room-size
still contributes zero training rows (all 67 candidates over the token budget).

User ruling, 08:50Z, verbatim intent as recorded: do not train on the failed set; train the arm C
3,431-row matched subset meanwhile (its own published training rows, so these runs are seed
replicates that give variance for the headline numbers); re-render the remaining rows with the
reviewed v2.5 renderer so the gate passes — **"Make sure that it passes."**

The fix lane (`P/claude_v25_fullset_build_20260922T0905Z/`) reruns the reviewed
`compact_counted_v2_5.py` (branch `compact-v2-5-20260920`, HEAD `5411443`, previously reviewed
PASS on its own 1,378-row build) over all 18,692 round-3 strict sources, inheriting every config
value unchanged from the prior v2.5 build's frozen anchor except `--expected-count` (18692, a
mechanical consequence of the input row count, not a discretionary change). Its STEP_1.md records
the plan: a 40-row extension pilot plus the 3,431 mandatory frozen rows first, hand-checked against
the eight defect classes the FAIL verdict named, then the full render on trinity-0-23, then
`verify` and the same inheritance-aware split gate, then a fresh `BUILD_RECORD_V25_FULL.md`. No
later STEP file existed under that lane as of this writing — the render had not started.

The four full-set training lanes prepared before the FAIL verdict
(`qwen_full1ep`, `onethinker_full1ep`, `onethinker_full3ep`, `onethinker_answeronly_full1ep`, all
under `P/claude_student_launch_20260922T0515Z/`) are left untouched on disk, not deleted, not
modified, for when a corrected set passes review.

## 2. Arm C replicates training now (trainer facts learned this hour)

Four seed replicates of arm C's own published recipe are running as the interim evidence while the
full-set fix is in flight. `student_pilot/ddp_config.py` fixes `effective_batch_size` at 32 and
`seed` at 17 — neither field can change without a reviewed trainer edit — so these replicates
differ from arm C's original published run only by GPU nondeterminism, not by seed or batch size.
`max_microbatch_size` is the free, adjustable lever (default 8); arm C's original config had
lowered it to 1, which is why the earlier Qwen full1ep attempt measured 293 s/step on six A6000s
at only 30 percent memory use — six accumulation passes each paying a full FSDP all-gather. The
replicate configs restore the cap to 8.

Provenance, hand-verified against `protocol.json`: dataset
`/data2/jjyeung/agent_project_data/devin_lane_out/converter_compact_v1_20260919_out/diagnostic_set_compact_v1c_dropclause/candidate_index.jsonl`
(sha256 `530663...`, 3,431 rows), split
`/data3/jjyeung/ddp_onethinker_c_onethinker_20260919T2100Z_active6_republish_20260920T045138Z/split.json`
(sha256 `4dd7467f...`, train 3,052 / held-out 379). Three epochs at effective batch 32 is 286 steps.

Four lanes, all launched 09:29-09:33Z after two scripting bugs (below) were caught and fixed:

| lane | host, cards | mode | pids | RUN_TAG |
|---|---|---|---:|---|
| Qwen arm C replicate 2 | trinity-0-18, cards 0-5 | FSDP world 6 | launcher 100045, torchrun 100688 | `_armc_rep2` |
| OneThinker arm C replicate 2 | trinity-0-18, cards 6-7 | DDP world 2 | 101665 | `_armc_rep2` |
| OneThinker arm C replicate 3 | trinity-1-3, cards 0,6 | DDP world 2 | 1775355 | `_armc_rep3` |
| OneThinker arm C answer-only | trinity-1-13, cards 2,3 | DDP world 2 | 1278711 | `_armc_answeronly` |

Two real bugs surfaced while preparing these lanes, both silent at `bash -n` and only visible at
runtime. First, a `${VAR:?message}` guard across all four full-set CPU-gate scripts carried an
apostrophe inside its own message string ("file's sha256"), which breaks bash's quote parsing
inside the guard even though the whole thing sits inside double quotes; several subsequent
variable assignments were silently swallowed into one long no-op argument. Fixed by rewording the
message in each script. Second, every OneThinker DDP-attempt-loop script derived by `sed` from an
earlier lane used a rename pattern requiring a trailing slash (`s#/onethinker_full1ep/#.../g`),
which never matches the bare `LANE=.../onethinker_full1ep` assignment line (no trailing slash,
last path segment) — so three of the four arm C launch scripts silently pointed at the wrong
lane's frozen inputs on first launch and exited rc=1 within seconds with no heartbeat file
written. Fixed with a one-line `sed -i` per script; Qwen's scripts were never at risk (its
rename patterns always include `/out` or `/work` suffixes). Lesson for any future script: never
put an apostrophe inside a `${VAR:?message}` guard, and never rely on an un-anchored rename
pattern for the last segment of a path assignment.

Measured step time for all four replicates: **pending** — WATCH logs
(`P/claude_student_launch_20260922T0515Z/{qwen_armc_rep2,onethinker_armc_rep2,onethinker_armc_rep3,onethinker_armc_answeronly}/out/WATCH_*.log`)
had not logged a step yet as of the last read (STEP_16.md, 09:33Z); `training_watch.sh` (section 8)
carries the live numbers.

The two interim runs that were training before this (Qwen and OneThinker on trinity-0-18,
3,052/3,431-row v1c set) were stopped cleanly at 08:16Z: Qwen's launcher exited on the first
SIGTERM (final step 13, loss 0.7394, no checkpoint yet). OneThinker's launcher has an internal
six-attempt retry loop that caught the SIGTERM as a training failure and auto-restarted; the
wrapper and the restarted attempt were both killed by hand (final step 51, loss 0.4560, checkpoints
at step_25 and step_50 preserved on `/scratch`). All 8 rank coordination leases were explicitly
released (`coord.py fail ... --error preempted_for_full_set`), not just left to stop renewing.

## 3. Collector lease incident: silent renewal stop, full recovery

The r1313 collector on trinity-3-8 stopped finalizing at 07:36Z with no provider, pool or node
cause. Its own coordination-lease heartbeat last renewed at 07:03:59Z and then simply stopped —
the controller (pid 23553) kept finalizing normally for another 32 minutes on an aging lease before
the guard's 1,800 s staleness limit caught up with it. The cascade from there: five workers hit
"stale or foreign collection lease" at 07:36Z (1,921 s after the last heartbeat, 121 s past the
limit), the watchdog stepped the worker count down 44→36→28 chasing the errors, a `set-workers`
resize was itself refused by the same stale-lease check, the watchdog's `if rc: raise` on that
refusal was uncaught, and it wrote a durable `BLOCKED.json` and exited. The collector's own pool
harness wrote a second, separate `BLOCKED.json` for the same reason. Both the watchdog (pid 3693)
and the controller (pid 23553) were confirmed dead; nothing on the node was retrying either — the
outage would not have self-healed.

Recovery, all times UTC: a lease-heartbeat keeper (pid 212370, later replaced by pid 213556 on a
20-hour cap, past both the projected 12:24Z 20,000-strict mark and the ~18:45Z pool-exhaustion
ETA) renewed the lease at 07:58:29Z; both `BLOCKED.json` markers were archived, never deleted, to
`out/BLOCKED_archive_20260922T0759Z/`; the watchdog relaunched at 07:59:57Z (pid 212703) and
completed its terminals rescan in 18 minutes (warm NFS cache, unlike the 75-minute cold-cache
rescan after the 01:43Z reboot); the controller (pid 215319) came up at 08:17:50Z; the first
finalization after the outage landed at 08:27:38Z. `setw.sh 44 6` was reissued at 08:30Z but first
needed its own fix — line 21 referenced bash `$n` instead of the outer shell's `$N`, so every call
aborted under `set -u` before writing the control file. Fixed, then confirmed: "ADOPTED target=44
after 1 checks." By 09:06:06Z the collector held 44/44 workers clean for 30+ minutes, finalized had
reached 25,008, and the post-recovery rate (372-444 per 10-minute window, roughly 372-444/h) was at
or above the pre-incident 240/h baseline. Total outage, watchdog death to first finalization:
about 36 minutes.

Lesson recorded for a successor: the collector's own renewal can stop silently with no warning
elsewhere, and the stale-lease guard turns that into a full stop nothing retries on its own. Run an
external lease keeper for the whole expected run life, not a short cap, and watch lease age
directly rather than inferring health from finalization counts.

## 4. Orchard: capacity confirmed, one admission bug blocks all training and evaluation

Real per-user Slurm limits, queried directly (`sacctmgr show assoc user=jjyeung`): `general_qos`
allows exactly one 1-GPU job at a time (`MaxJobsPU=1`); `adv_4gpu_qos` allows 4 GPUs on one node,
no preemption, 24-hour jobs; `preempt_qos` allows up to 32 GPUs across 4 nodes but sits behind a
projected start of about 2026-10-02, so preempt jobs are queued only as lottery tickets. Working
concurrent capacity is therefore 4 H100s (advanced) plus 1 H100 (general) — 5 total, not the 32 the
earlier plan assumed.

Measured H100 speedup over an RTX 6000 Ada, same LoRA probe on both clusters: 1.77x per card
(3.369 s/microbatch on H100 vs. 5.959 s on Ada, both at 32.2 GiB peak). At the real arm C anchor
(293 s/step at effective batch 32, cap-1 microbatch, six A6000 accumulation passes = 48.8 s per
pass on Ada), an H100 pass is about 27.6 s; raising the microbatch cap to the trainer's own default
of 8 removes seven of every eight FSDP all-gathers and is the largest lever available, on Orchard
exactly as on trinity.

The Orchard trainer (`9645d34`) and deployment (`a0551b5`) passed independent Astra review (157
scoped trainer tests, 25 admission tests, 5 deployment tests, pip check, all green) and are live on
Orchard. Two smoke attempts failed on fixable setup errors — a split-record schema Orchard's
trainer does not accept (fixed: use the real published arm C `split.json`, not the lane's own
audit-artifact `PUBLISHED_SPLIT_*.json`) and an effective-batch-size of 36 that the trainer's
`FIXED` tuple refuses outright (fixed: keep effective batch 32, raise `max_microbatch_size` to 8
instead — mechanically equivalent to the ruling's intent, no `ddp_config` change needed). A third
smoke (job 147450) cleared every gate through `prepare-training` (6,897 train rows, matching the
interim build exactly) and then failed at `orchard_admission.issue()`:

```
SLURM_JOB_GPUS=0,2,3,4          <- physical node indices, non-contiguous
CUDA_VISIBLE_DEVICES=0,1,2,3    <- the job cgroup renumbers them
```

`issue()` queries `nvidia-smi -i 4` for a physical index the cgroup does not expose (exit code 6).
Orchard renumbers GPUs inside the job cgroup; the admission code assumed physical indices survive
into `CUDA_VISIBLE_DEVICES`, which is true on trinity but not here. The proposed fix — query UUIDs
by local index while keeping the physical index in the lease record, and accept a local-index form
of `CUDA_VISIBLE_DEVICES` as a third valid pattern — is a one-place change but touches admission
code, so it needs independent review before use (lane `P/claude_orchard_admission_fix_20260922T0925Z/`
had a worktree staged and review scaffolding created but no STEP file or verdict yet as of this
writing). Every Orchard general-partition evaluation slot is blocked by the identical bug (same
`issue()` path), so the OneThinker VSIBench reference run and the 27B three-row smoke wait on the
same fix, not a separate one.

Node-local staging needs no trainer change: the reviewed code already permits redirecting reads to
anything under `/tmp/jjyeung` via `STUDENT_FRAME_ROOT_MAP`, so a launcher-side staging script
(`stage_dataset_local.sh`, built, not yet exercised past admission) should cut arm C's prepare time
on Orchard from an extrapolated 17 minutes to under two, once training itself is unblocked. The
27B base-control harness port (`orchard-eval-qwen27b-20260922` at `bd628a8`, +834/-27 across 6
files) is in independent Astra review now (`P/claude_orchard_eval_review_20260922T0935Z/`,
dispatched 09:31:35Z, no verdict as of this writing).

Deletion queue for the user, unchanged from the 07:00Z ruling: `/project/community/jjyeung/probe_256m.bin`
and `probe2_256m.bin` on Orchard.

## 5. Qwen3.6-27B, gtmeasure, and the partial-checkpoint scoring review

The Qwen3.6-27B arm C student is live on trinity-0-13 (cards 0, 2, 3; card 1 belongs to another
user), FSDP, one epoch, interim 7,622-row set, 216 steps, finish projected about 2026-09-23 04:15Z.
The harness's 27B support (branch `harness-qwen27b-20260922` at `d65bd2b`) passed independent
review, 104/104 tests, scoring byte-identical to the existing path. A base control on both
benchmarks is still required before any improvement claim and is the item the Orchard eval port
above is building toward — no 27B base control exists yet.

`tools/gtmeasure/` (branch `gt-measurement-supervision-20260922`) generates exact measurement
targets straight from GT scene assets — count, size, object distance, camera-object distance, room
size — following conventions harvested from the pool's own wording. v2 (intermediate GT
observations: extents, centres, camera positions before the answer, byte-identical answers to v1)
passed independent review at commit `53cd73e`. The v1 full set (about 9,180 rows) and the v2 full
set are both generating; the v2 pilot is OneThinker, arm C recipe, three epochs, the full trace set
mixed at a 0.25 ratio of measurement rows, targeting Orchard preempt as job 4 in the Orchard queue
— itself waiting on the same admission fix as everything else on Orchard.

The partial-checkpoint scoring change (branch `partial-checkpoint-scoring-20260922`, commit
`c7c7c789`) let a raw `checkpoints/step_N/adapters.pt` be scored and labelled without a full
publish — needed so the arm C replicates and the Qwen 27B run produce usable numbers even if
preempted mid-run. Three independent review rounds so far, all against the same unchanged commit:
round 1 FAILed on two defects in the review's own setup (a misleading brief on an intentional
optional-field design, and a fully read-only sandbox that could not run the suite at all) — every
per-item code finding was clean. Round 2 fixed both setup defects, and the reviewer went further
than asked, writing its own independent provenance probes and stating explicitly "I found no
scoring-code defect" — but still FAILed, because the full `unittest discover` run at the reviewed
worktree didn't reproduce a retained baseline log's exact pass/fail identities; nearly all of the
121 differing identities traced to environment gaps in modules the change never touches (a missing
env var in unrelated test modules, one hardcoded fixture path, one sandboxed socket-permission
restriction). Round 3, dispatched 09:30:35Z, restates PASS as exactly the repository's test-gate
rule requires — tests exercising the change plus its own new tests must pass with no regression;
unrelated pre-existing or environmental failures are recorded, not blocking — and reruns the
specific comparison against a live parent-commit baseline in the identical sandboxed environment
rather than an old retained log. No verdict yet as of this writing
(`P/claude_partial_scoring_review3_20260922T0929Z/`, receipt
`agent/scratch/codex_runs/20260922T093035Z_partial_checkpoint_scoring_gate_review_round3`).

## 6. Rulings (user, 2026-09-22, verbatim where quoted)

1. Collector key budget: **"You can go up to six million"** — the shared Gemini key's cap, in
   tokens per minute, across every collector drawing on it.
2. Lenient scoring is primary. Never penalize a correct answer given in the wrong format; strict
   parsing stays secondary (carried forward from 05:30Z, still in force).
3. Every GPU on the cluster is usable. Never ask for allocation — find idle cards over ssh and
   claim them. Leave every other experimenter's running process untouched.
4. vnice is required only above 16 large GPUs held in total on trinity; below that threshold it is
   optional. Orchard has no vnice at all — Slurm allocation, QoS and preemption govern there
   instead.
5. Maximize Orchard's use. Preemption is acceptable — partial results plus resume are preferred
   over holding out for an uninterrupted run.
6. 08:50Z, on the failed full-set gate: train on the 3,431 clean arm C rows meanwhile, and reword
   the remaining rows so the review passes — **"Make sure that it passes."**

Other-experimenter GPU handover channel (08:25Z): the other experimenter's orchestrator (session
`agent-project-89`, cross-session address `bridge:session_019FXAvcrnojoNLtm61Mdsja`) releases its
large GPUs to this lane as its own experiments finish, messaging each release with node and card
indices; this session never stops its processes. Released so far: trinity-1-3 GPUs 0 and 6 (used
for OneThinker arm C replicate 3, section 2). Expected next: trinity-1-13 GPUs 2 and 3 (already
used for the answer-only replicate), trinity-0-13 GPU 1 around 13:20Z, several Qwen replica pairs
across trinity-0-23, trinity-1-13, trinity-0-13 and trinity-1-3 between about 00:00 and 02:00Z on
09-23. Scan tables: `/home/jjyeung/agent_project/agent/scratch/gpu_scan_20260922/REPORT.md`.

Gemini key sharing (from the same ruling record): the key moved from this lane's sole control to a
shared arrangement superseded by the main queue's ruling — REQ-234's rungs and counting cells run
beside the teacher collectors with REQ-234 keeping priority, and a 429 response is the signal to
decrease usage, not a hard stop.

## 7. Next steps, in priority order

1. Get a verdict on the round-3 partial-checkpoint scoring review
   (`P/claude_partial_scoring_review3_20260922T0929Z/`) and, on PASS, wire partial-checkpoint
   scoring into the arm C replicates and the Qwen 27B run so a preemption still yields a number.
2. Get a verdict on the Orchard admission local-GPU-index fix
   (`P/claude_orchard_admission_fix_20260922T0925Z/`) and the Orchard 27B evaluation port
   (`P/claude_orchard_eval_review_20260922T0935Z/`); on PASS, unblock every Orchard training and
   evaluation job behind the same `issue()` bug — the Qwen 9B and OneThinker full-set chains, the
   27B full-set run, the gtmeasure pilot, and the general-partition evaluation slot.
3. Render the full 18,692-row set with the reviewed v2.5 renderer
   (`P/claude_v25_fullset_build_20260922T0905Z/`), hand-check the 40-row pilot against the eight
   FAIL-verdict defect classes before committing to the full render, then send the corrected build
   to a fresh independent gate review before anything trains on it.
4. Babysit the four arm C replicates to their first measured step time and report it; watch for
   the same scripting-bug class (apostrophes in `${VAR:?}` guards, un-anchored sed renames) in any
   further lane cloned from these scripts.
5. Watch the r1313 collector's approach to its finalized-count trigger and the r1317 controller's
   ramp on trinity-1-13; watch the Qwen arm A r6 evaluation and the Qwen 27B run toward their
   projected finish times.
6. Bring the pending deletions (the four from the 06:00Z checkpoint plus the two Orchard probe
   files in section 4) and any newly-provisional rulings to the user for confirmation.

## 8. Armed watchers

All six live under `P/claude_orchestrator_watchers_20260921T2330Z/`, read-only, none kills or
restarts anything; each writes its own `.log` and fires (prints one line, exits 0) when its
condition trips.

- `collector_health_watch.sh` — polls `WATCHDOG_HEALTH.json` for the r1313 collector every 120 s;
  tracks pids 212703 (watchdog), 215319 (controller), 120283 (package guard); fires on a
  26,000-finalized crossing or a health-file problem.
- `r1317_watch.sh` — ssh's trinity-1-13 every 300 s for the r1317 controller's health line; fires
  on controller death, any 429, terminals flat 30 minutes, terminals reaching 3,300, or a lease age
  past 1,500 s (the stale-lease guard trips at 1,800 s — this is the 07:04Z incident's lesson
  applied as an alarm).
- `training_watch.sh` — polls five WATCH logs every 120 s: the four arm C replicates
  (`qwen9b_rep2`, `ot_rep2`, `ot_rep3`, `ot_answeronly`) plus the Qwen 27B run; fires on any log
  going stale past 600 s, any run's step count flat for 1,500 s, or any run reaching its final
  step.
- `qwen_r6_eval_watch.sh` — polls the Qwen arm A r6 evaluation's rate logs every 300 s against
  supervisor pids 95829/95830; fires on staleness past 1,200 s.
- `census_exit_watch.sh` — polls the r1313 light census (trinity-3-8, pids 1595879/1600988) every
  120 s; fires when the census process exits.
- `trinity38_thaw_watch.sh` — ssh's trinity-3-8 every 120 s watching for it to answer again after
  the 2026-09-21 freeze/reboot; gives up after 6 hours. The node has since answered and the
  collector has been running on it for hours (sections 3 and 6 of the 06:00Z checkpoint), so this
  watcher's condition has likely already fired; a successor should confirm from its log rather than
  assume it is still armed.

A successor re-arms any watcher whose process is not found running, using the same script and log
path so the history is continuous.

## 9. Not verified when this was written

Whether the round-3 partial-checkpoint scoring review reached a verdict is unknown. Whether the
Orchard admission fix or the Orchard 27B evaluation port passed independent review is unknown —
neither lane had a STEP file recording a result as of this writing. The four arm C replicates'
first measured step times are unrecorded; none had logged a step in the WATCH logs as of the last
read. The v2.5 full-set render's pilot and full-render results are unrecorded — no STEP file beyond
the plan existed under that lane. Whether the Qwen arm A r6 VSIBench leg and the Qwen 27B run have
progressed past their last recorded checkpoints is unconfirmed.

None of this blocks further work. The four full-set training lanes held on disk since section 1
need no action until a corrected build passes review. The rulings in section 6 are already in
force as stated; none is provisional.
