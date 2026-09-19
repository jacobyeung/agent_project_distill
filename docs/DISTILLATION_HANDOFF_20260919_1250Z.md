# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 12:50Z

Read this, then `CLAUDE.md` (operating rules including production source tree, branch, and
test-gate rules), then the memory index for this project. The orchestrator verified
everything below at write time; re-verify before acting.

## 1. State of the goal

The user restated the lane's goal at about 11:50Z, verbatim:

> "Own the distillation lane: obtain at least 20,000 accepted traces on vsibench training
> using the GT perception data. Fine-tune OneThinker-8B and Qwen3.5-9B with vision and
> language LoRA on a scene-disjoint split of those targets and show better RGB-only,
> tool-free accuracy than the base checkpoints on VSIBench and VSTIBench reporting
> per-question-type results. use Devin Astra max for development, Codex or Luna for ssh
> work and Sonnet for easy tasks, and never touch the other experimenter's state or the
> collector code on main while the collector runs. Maximize the google API key at 8m
> tok/min to collect the reasoning traces. Evidence first: publish per-type results on the
> partial training set for both students before any full-scale run, and report them
> whether or not they beat the base. Paper ready numbers by 2026-9-24Z; when lanes compete
> for GPUs or the key, the collector and the two student fine-tunes win over ablations."

Lane root (D below): `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`.
Devin lane root: `agent/scratch/devin_lanes/`, with `out/` symlinked to
`/data2/jjyeung/agent_project_data/devin_lane_out/<lane>_out/`.

### Collector (r1315 teacher traces, target 20,000; 6,570 finalized at 12:46Z)

The collector is recovered. trinity-3-23 stayed unreachable by direct ssh (its home NFS
still hangs after the public-key offer); the poller `D/codex_luna_t323_reach_poll` keeps
polling every 5 minutes and still returns rc=124. Devin lane
`collector_remote_drain_attestation_20260919` built the truthful remote-evidence
attestation instead: `attest_host_drained.py remote --host trinity-3-23 --evidence
<the 07:24:51Z ssh ps snapshot PREFLIGHT_T323.json> ...`, with the verifier host recorded as
itself rather than as trinity-3-23. It landed on branch
`collector-remote-attestation-20260919`, commit `998516b0e4a298ac5f82cddd8557c16418435df4`.
Astra review (`D/codex_review_remote_attestation/out/REVIEW.md`) passed: all 313
receipt-less workers are covered, and a simulated publication clears admission.

Relaunch lane `D/codex_relaunch_r1315_drain_attest` reached attempt 4 (`PROMPT_r4.md`). It
sealed the contract from epoch checkout `/home/jjyeung/agent_project_distill_epochs/998516b`
(`CONTRACT_drain_998516b...json`, sha256
`778fdaf3faf8cce4cc88a6a9df8178c35f623cfb6de6c4f84e3adf6399638ab1`) against the live registry
(digest `1e30c3ab...`). Attempt 3 had failed at bind on a stale or foreign collection lease
(last heartbeat 10:08Z); attempt 4 renewed the lease as its own agent through the
coordination tool (`STEP_2b_lease_r4.json`, 12:15Z), bound, published the attestation, and
wrote `READY_FOR_FAST_FORWARD_r4.json`. The orchestrator could not fast-forward `main`
because two documentation commits had landed on it after `71a934b`, so it merged `998516b`
into `main` as commit `612a32531c7ecb8d9bb197d1b247ed9728edf254`, with
`git diff 998516b HEAD -- collector/` empty. The handshake file
`OUT/ORCHESTRATOR_FAST_FORWARDED.json` records this and tells lanes to check ancestry plus an
empty `collector/` diff rather than HEAD equality.

Watchdog v5 relaunched at 12:29:51Z (PID 1119334, trinity-1-3); `BLOCKED.json` and
`WATCHDOG_ALARM.json` are archived by rename, not deleted. The controller launched at
12:36:34Z with 8 workers, the lease heartbeats from trinity-1-3, and finalized traces ran
6,565 to 6,570 by 12:46Z against the 20,000 target. The ramp plan: the relaunch lane takes 8
to 16 workers after 30 minutes of growth; after that the orchestrator adds 4 workers whenever
the trailing 5-minute input rate stays under 70 percent of the 8M tok/min ceiling with no
429/503 events, up to the watchdog ceiling of 64 (`R/watchdog_control_v5.json`). Watchdog v6
(lease-owned, no cold scan) stays the takeover path if v5 wedges again
(`D/codex_watchdog_v6_lease/out/LAUNCH.md`).

Never change `collector/` on `main` while a collector runs. The sequence stays: seal the
contract from an epoch checkout, bind, attest, fast-forward (or ancestor-merge with an empty
`collector/` diff) `main`, then relaunch.

### Gemini tokens-per-minute readout

Devin lane `collector_tpm_readout_20260919` built `out/gemini_tpm_readout.py` (35 tests). The
orchestrator runs it as a background process on trinity-1-3; it dies with the session and
restarts with the `NEEDS-LAUNCHER` command recorded in its `out/REPORT.md`. It writes
`R/TPM_READOUT.json` and `R/TPM_READOUT.log` every minute from the provider journals. At
12:44Z, with 8 collector workers running, the trailing 1-minute window showed 850k input
tokens/min (10 percent of the 8M ceiling), 41 calls/min, and zero throttling events. Its
`out/RAMP_GUIDE.md` sets the ramp thresholds the orchestrator uses above. The bulk rewrite
lowered its own concurrency from 24 to 12 at 12:33Z (`O/CONCURRENCY.json`, O =
`/data2/jjyeung/agent_project_data/devin_lane_out/converter_freeform_v3_20260919_out/`)
because the collector holds key priority per the goal.

### OneThinker single-GPU baseline (`finetune_diagnostic_v2_20260918`)

Training continues on trinity-1-13 GPU 2: step 343 of 656 at 12:29Z, about 53 seconds per
step, ETA about 17:14Z. The Opus babysitter subagent cycles every 30 minutes
(`D/babysitter_finetune/NOTES.md`) and, once `PUBLISHED.json` appears under
`/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918/`, launches the 4-shard
evaluation through `D/codex_luna_launch_eval_onethinker`.

### Multi-GPU trainer v4

Branch `trainer-multigpu-v4-20260919`, worktree
`agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`. Commit chain:
`5d6c21d` v4.1 reviewed PASS; `fceddd8` v4.2 position-selects logits; `21dd34d` v4.3 adds FSDP;
`fb36e01` v4.4 makes FSDP publication rank-0 only (Devin `trainer_v4_4_fsdp_fix_20260919`,
four two-process tests pass); `06a9664` v4.5 fixes DDP admission by stringifying torch's
`_CUuuid` before parsing (Devin `trainer_v4_5_uuid_probe_fix_20260919`, 80 tests). The frozen
checkout for launches is `D/codex_luna_launch_ddp_v4_a_onethinker/work_checkout_06a9664`; all
four `LAUNCH_PARAMS.env` files now name `06a9664`.

Both staged smokes cleared admission and then failed the memory-fit probe: arm A OneThinker
attempt 4 on trinity-2-28 passed admission on all four ranks but failed at microbatch 1
(allocated 38,679,001,088 B, reserved 46,502,248,448 B, limit 45,780,664,320 B; `SMOKE_r4.md`);
Qwen FSDP attempt 2 on trinity-1-3 GPUs 1 to 4 failed the same gate (allocated
38,779,788,800 B, reserved 50,147,098,624 B; `SMOKE_r2.md`). Both share a cause: the probe
judges peak reserved memory, and the caching allocator fragments about 7 to 11 GB on the
stress sample.

In flight: arm A attempt 5 (`BRIEF_r5.md`, DDP with `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`,
FSDP fallback inside the lane, artifacts suffixed `_r5`); Qwen attempt 3 (`BRIEF_r4.md`, FSDP
plus the same allocator setting, artifacts suffixed `_r3`); arm E attempt 5 (`BRIEF_r5.md`,
gated on arm A's `SMOKE_r5.md`, trinity-0-3 GPUs 0, 4, 5, 6); and Devin lane
`trainer_v4_6_memory_gate_20260919`, which bakes the allocator setting into the batch script,
records it in `run.json`, and judges allocated bytes times a 1.15 safety factor when
expandable segments are active. `e_qwen` stays queued: no 4 free GPUs exist until
trinity-0-18 frees near 13:48Z. trinity-2-28 shows load average about 870 from other users'
idle thread pools, with idle CPU and GPUs and responsive storage
(`D/codex_luna_t228_load_diag/out/REPORT.md`); proceed there, but stop if a smoke step takes
more than 150 seconds.

### Rewrite (free-form C-N ablation)

The v3.1 bulk run of 3,852 rows continues in `D/codex_rewrite_v3_1_bulk` (attempt 2,
`PROMPT_r2.md`): 966 rows finalized by 12:35Z, with 20 rejections (18
`source_qualification_uncovered`, 2 `target_artifact`), 1,925 of 12,000 leased calls used. The
runner refuses any lease whose `admitted_at` exceeds 5 minutes, so the orchestrator's
scratchpad issuer re-issues `O/API_LEASE_bulk_v3_1.json` whenever
`O/API_LEASE_REFRESH_REQUEST_bulk_v3_1.json` changes; a successor must restart that issuer.
Devin lane `rewrite_numeric_fidelity_audit_20260919` is building a full-coverage independent
number, entity, and answer audit and re-runs it every 15 minutes until a final index appears.
v3.2 fluency stays parked: every variant scored 1.0 of 5.

### Format E (`converter_zero_call_v4_20260919`)

Unchanged: provisionally admitted, 3,867 rows, partial chains excluded.

### Base evaluations

Observer window 6, `D/codex_base_evals_v8` (Luna), adopted the completed cells at 12:38Z:
Qwen VSI union 431 of 500, Qwen VSTI union 370 of 450, OneThinker DSI continuing. It scores
completed Qwen cells per-question-type offline. VSTI shard 0 relaunched, supervised, on
trinity-1-13 GPU 3 as attempt 6 (`D/codex_place_qwen_vsti_shard0_r6`, supervisor PID 539719,
worker PID 539731, 21 of 113 at 12:28Z) after attempts 4 and 5 had the supervisor assert on a
pre-existing `shard_0.log`. The other orchestrator warns that no answer-bank registration
should happen until `answer_bank_registry_index.py verify` passes (its index is under
rebuild); it has taken rounds r1329 to r1331, and this lane's buffer (r1316 to r1319) stays
untouched.

### Lane table

| Lane | Status at 12:50Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` | Attempt 4 sealed, bound, attested, and merged (`612a325`); watchdog v5 running with 8 workers. | Ramp per `R/watchdog_control_v5.json`; watch the TPM readout for headroom. |
| `codex_luna_t323_reach_poll` | Still polling every 5 minutes; trinity-3-23 remains unreachable. | Keep polling; no longer blocks the collector. |
| `codex_watchdog_v6_lease` | Built and tested, 32 tests. | Takeover path only if watchdog v5 wedges. |
| `finetune_diagnostic_v2_20260918` | OneThinker step 343/656 at 12:29Z. | Wait for `PUBLISHED.json`, then launch the 4-shard eval. |
| Trainer v4 DDP smokes (arm A, Qwen FSDP, arm E) | All hit the memory-fit probe on allocator fragmentation; attempts with `expandable_segments:True` in flight. | Watch `SMOKE_r5.md` (arm A), `SMOKE_r3.md` (Qwen), then arm E; land `trainer_v4_6_memory_gate_20260919`. |
| `codex_rewrite_v3_1_bulk` | 966/3,852 finalized by 12:35Z, 20 rejections. | Keep the lease issuer alive; watch the fidelity audit's 15-minute cycles. |
| `converter_zero_call_v4_20260919` | Format E provisionally admitted, unchanged. | None pending. |
| `codex_base_evals_v8` | Qwen VSI 431/500, Qwen VSTI 370/450 adopted; VSTI shard 0 relaunched attempt 6. | Monitor shard 0 progress; union and dedup on completion. |

## 2. What dies with this session and how to relaunch it

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the Opus babysitter subagent; the bulk-lease issuer
for `codex_rewrite_v3_1_bulk`; the Gemini TPM readout background process (restart with the
`NEEDS-LAUNCHER` command in `collector_tpm_readout_20260919`'s `out/REPORT.md`); every Codex
and Devin lane (re-dispatch each with its resume preamble); and the 30-minute orchestrator
tick.

The following survive: GPU jobs started through real shells, including the OneThinker
baseline, the trainer v4 smokes, and the base-eval workers; all lane artifacts; and git.

## 3. Pending user rulings

- RULED about 11:50Z: the goal statement quoted in full in section 1 above supersedes prior
  phrasing of the lane's objective; its priority order and deadline (paper-ready numbers by
  2026-09-24Z) govern GPU and API-key contention.
- RULED through the main-repo queue, executor preference, verbatim: "Actually, could we
  prefer to use claude subagents? It's still okay to escalate to Astra or use Luna when you
  need to SSH into other nodes, but we are starting to run out of codex usage. Devin or
  Claude Subagents." Applied: every new lane uses Claude subagents (Sonnet for reads and
  mechanical work, Opus for launch-and-babysit and analysis) or a Devin builder; Codex Luna
  is for ssh relays only; Codex Astra is for gate reviews and escalation only; in-flight
  Codex lanes finish out.
- RULED through the main-repo queue, relaunches, verbatim: "if you're just relaunching an
  experiment that's already been designed and has been running for a while now, you don't
  need a reviewer to review any changes you do, right? Don't waste tokens. Please don't want
  reviewers if you're just relaunching an experiment that collapsed for some reason." Applied:
  a relaunch of an already-designed, already-running experiment skips independent review; a
  new design, a new admission or scoring path, or a first launch still gets one. The user
  also confirmed the 5-minute Devin heartbeat as the monitoring mechanism and asked that Devin
  sessions spread across nodes; the cross-node launcher
  (`D/codex_luna_devin_launch_r3`, `ssh -f` form) still fails silently on trinity-1-13,
  trinity-0-3, and trinity-0-18 (no `devin.out` created), so every Devin lane still runs
  locally on trinity-1-3 until that launch form is diagnosed.
- RULED 23:50Z (2026-09-18): Qwen3.5 DSI is dropped from evaluation; OneThinker DSI base
  continues.
- RULED 23:58Z (2026-09-18): evidence that distillation works on a partial training set comes
  before full-scale runs.
- RULED 03:00Z: the free-form rewrite arm is approved as an ablation, trained on the qid
  intersection with the zero-call arm.
- RULED 03:45Z: use every reachable node; the ICLR deadline is about 2026-09-26.
- RULED 03:58Z: fine-tune the 8B and 9B students first; a 27B/31B-class student is a later
  go-or-hold decision.
- RULED 08:30Z to 08:35Z: use standard multi-GPU VLM LoRA practice; keep the one-GPU pilot as
  a baseline only; maximize Gemini-key throughput once other experiments finish.
- Open: whether to overturn the provisional Format E admission (numbered anchors to delivered
  student frames were treated by the orchestrator as grounded facts, not tool artifacts).
- Open: the tiered target-admission rubric, the numeric tolerance band, preparers for the
  remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays parked), and the
  27B/31B student go-or-hold, all pending the 9B result.

## 4. Standing constraints

- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane
  (ssh relays) or a Claude subagent.
- The pre-shell guard blocks any command text containing the words for deleting or
  truncating, even inside a heredoc.
- The auto-mode classifier refuses a brief that would write an attestation misstating the
  verifying host; an attestation must record the host that actually gathered its evidence.
- Codex lanes die with the orchestrator session; every lane writes per-step artifacts and
  resumes from a preamble rather than depending on the dispatching session's memory.
- Devin `-p` needs `--respect-workspace-trust false` and a `timeout` wrapper.
- The recurring 30-minute orchestrator tick is session-only and must be recreated by each
  successor session.
- Never change `collector/` on `main` while the collector runs, blocked or not; land fixes on
  a branch, seal the contract from an epoch checkout under
  `/home/jjyeung/agent_project_distill_epochs/<commit>`, bind, attest, fast-forward (or
  ancestor-merge with an empty `collector/` diff), relaunch (CLAUDE.md production source tree
  rule). When `main` cannot fast-forward because documentation commits landed after the base,
  merge instead and verify with ancestry plus an empty `collector/` diff, not HEAD equality.
- Lanes never switch branches or create branches in the main working tree; branch work
  happens in a separate `git worktree` under the lane's `work/` directory, landed on `main` by
  fast-forward.
- `BLOCKED.json` and `WATCHDOG_ALARM.json` get moved aside to acknowledge, never deleted.
- Do not treat a D-state controller with fast stateless NFS stats on its node as storage load;
  diagnose the node's NFS session state first.
- A subagent brief that mentions stopping a process is refused by the classifier ("Interfere
  With Workloads"); Codex ssh/pgrep/kill lanes die on `access_programs.cyber` HTTP 400 after
  40 minutes to 2.5 hours, so kill steps route through the user rather than automation; write
  per-step artifacts and have the orchestrator write the final record.
- Devin lane briefs must authorize new templates or parsers explicitly, or the lane defers
  building them.
- The Codex "review" preset runs read-only and cannot write lane deliverables; use `mech` with
  a writable root for genuine reviews.
- Devin `-p` processes linger after their final answer; stop them by task once `REPORT.md`
  ends with `DEVIN_LANE_DONE`.
- Never write bulk lane data under `/home`; every Devin lane's `out/` and Codex receipts live
  on `/data2` via symlinks.
- The DDP/FSDP memory-fit probe judges peak reserved allocator memory, which fragments 7 to
  11 GB on the stress sample; treat a failure there as an allocator-fragmentation question
  first, not a true out-of-memory condition, until `trainer_v4_6_memory_gate_20260919` lands
  its allocated-times-safety-factor judgment.

## 5. Key paths

- Collector remediation root: R =
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Attestation branch `collector-remote-attestation-20260919` at
  `998516b0e4a298ac5f82cddd8557c16418435df4`, merged into `main` as `612a32531c7ecb8d9bb197d1b247ed9728edf254`;
  epoch checkout `/home/jjyeung/agent_project_distill_epochs/998516b`.
- Collector relaunch and reach lanes: `D/codex_relaunch_r1315_drain_attest` (attempt 4, bound
  and published), `D/codex_luna_t323_reach_poll`, `collector_remote_drain_attestation_20260919`,
  `D/codex_watchdog_v6_lease`. Gemini TPM readout: `collector_tpm_readout_20260919`, writing
  `R/TPM_READOUT.json` and `R/TPM_READOUT.log`.
- OneThinker baseline: `agent/scratch/devin_lanes/finetune_diagnostic_v2_20260918/`; publish
  root `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918`. Babysitter notes:
  `D/babysitter_finetune/NOTES.md`.
- Trainer v3.1 (for launches still pinned to it): commit `0de12a565e59ca727239653291d6916c20c29708`.
  Trainer v4 worktree: `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`,
  branch `trainer-multigpu-v4-20260919`, tip `06a9664` (v4.5). Launch lanes:
  `D/codex_luna_launch_ddp_v4_a_onethinker` (frozen checkout `work_checkout_06a9664`),
  `..._e_onethinker`, `..._a_qwen`, `..._e_qwen`. Memory-gate fix in flight:
  `trainer_v4_6_memory_gate_20260919`.
- Rewrite v3.1 bulk: `D/codex_rewrite_v3_1_bulk`, lease `API_LEASE_bulk_v3_1.json`, refresh
  request `API_LEASE_REFRESH_REQUEST_bulk_v3_1.json`. Fidelity audit:
  `rewrite_numeric_fidelity_audit_20260919`. Format E: `converter_zero_call_v4_20260919`.
- Base evaluations: `D/codex_base_evals_v8` (successor to v7). VSTI shard 0 relaunch:
  `D/codex_place_qwen_vsti_shard0_r6`.
- Cross-orchestrator channel: `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` and
  `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.

## 6. Executor policy

The user moved this lane's default executor off Codex and onto Claude subagents (Sonnet for
reads and mechanical work, Opus for launch-and-babysit and analysis) or Devin builders, to
conserve Codex usage; Codex Luna still handles ssh relays to other nodes, and Codex Astra is
reserved for gate reviews and escalation, never for routine development. In-flight Codex
lanes run to completion rather than being cut off mid-task. Separately, a relaunch of an
experiment that was already designed and has been running skips independent review; review
still gates a new design, a new admission or scoring path, or a first launch. The Devin
5-minute heartbeat remains the monitoring mechanism, and the user asked that Devin sessions
spread across nodes; that spread is blocked today because `D/codex_luna_devin_launch_r3`
fails silently (no `devin.out`) on trinity-1-13, trinity-0-3, and trinity-0-18, so every Devin
lane still runs locally on trinity-1-3 pending a diagnosis of the `ssh -f` launch form.

## 7. Cross-orchestrator channel

A second, non-training orchestrator runs alongside this lane and shares lane root D. The two
exchange notes through `D/INBOX_FROM_NONTRAINING_ORCHESTRATOR_<UTC>.md` (their messages to
this lane) and `D/INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>.md` (this lane's messages to them).
The first exchange happened at 12:40Z. Check both files on every tick; the other
orchestrator's warning about answer-bank registration (section 1, base evaluations) came
through this channel.

## 8. Memory index

Memory files added or updated today, in
`/home/jjyeung/.claude/projects/-home-jjyeung-agent-project-distill/memory/`:
`trinity-0-28-session-death-20260919`, `collector-require-drained-block-20260919`,
`api-lease-admission-window`, `crossnode-devin-launch-silent-failure`,
`nontraining-orchestrator-inbox-channel`, `executor-tiering`, `distillation-lane-goal`,
`production-source-tree-rule`, `qwen-oom-48gb-cards`, `student-trainer-readiness`.
