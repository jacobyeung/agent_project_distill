# Distillation lane handoff (REQ-20260917-232), written 2026-09-19 11:50Z

Read this, then `CLAUDE.md` (operating rules including production source tree, branch, and
test-gate rules), then the memory index for this project. The orchestrator verified
everything below at write time; re-verify before acting.

## 1. State of the goal

The previous orchestrator session died on trinity-0-28 about 10:10Z, most likely from NFS
I/O stalls it had itself caused. Every Codex lane it had dispatched died with it. The
successor session runs on trinity-1-3 and re-dispatched the lane's work at 10:58Z.

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

### Collector (r1315 teacher traces, target 20,000; 6,565 finalized)

The collector has been down since 10:37Z. Its controller crash-looped from 09:55Z with
"predecessor drainage unverified on foreign host": 313 workers had ended on trinity-3-23
without exit receipts, which `pool_harness/state.py require_drained` refuses to accept.
Watchdog v5 then died at 10:37Z on "12 launches/hour cap exhausted" and wrote
`R/BLOCKED.json` and `R/WATCHDOG_ALARM.json`, where R is
`/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
The coordination lease's last heartbeat was 10:08:17Z.

A fix branch, `collector-drain-attestation-20260919`, tips at
`d9a7b73485a18f0445f667d626e32bba64c4ff84` and adds `collector/attest_host_drained.py` plus
an acceptance path. Independent review at `D/codex_review_collector_drain_attestation/out/REVIEW.md`
returned REVISE: P1, unsigned evidence cannot prove host origin; P2, `SEAL_NOTES` pins an
older registry. The orchestrator's adjudication, `ORCHESTRATOR_ADJUDICATION.md` next to that
review, accepts the honest-writer trust model and requires the live registry read from
config. An epoch checkout exists at `/home/jjyeung/agent_project_distill_epochs/d9a7b73`.

The relaunch lane `D/codex_relaunch_r1315_drain_attest` (`PROMPT.md`) stopped at step 1:
ssh to trinity-3-23 stalls after the public-key offer because its home NFS is hung, so the
attestation cannot run on that host (`D/codex_luna_t323_reach_diag/out/REPORT.md`). A
fallback that would have written an attestation claiming host trinity-3-23 from a different
node was rejected as a misrepresentation. Two paths now run in parallel: a Luna poller,
`D/codex_luna_t323_reach_poll`, writes `out/REACHABLE.json` once a non-login ssh command
succeeds, after which the relaunch lane resumes on path A; and a Devin lane,
`collector_remote_drain_attestation_20260919`, builds a truthful remote-evidence attestation
schema that records the verifier host as itself and cites
`D/codex_relaunch_r1315_node_move/out/PREFLIGHT_T323.json` (the 07:24:51Z process snapshot).
That schema needs one independent review before it can seal. Watchdog v6 (lease-owned, no
cold scan) is built and tested (32 tests) at `D/codex_watchdog_v6_lease/out/` with
`LAUNCH.md`; the v5 relaunch is preferred first, and v6 is the takeover path only if v5
wedges again.

Never change `collector/` on main while a collector runs. The sequence stays: seal the
contract from the epoch checkout, bind, attest, fast-forward main, then relaunch.

### OneThinker single-GPU baseline (`finetune_diagnostic_v2_20260918`)

Training continues on trinity-1-13 GPU 2: step 273 of 656 at 11:34Z, 50 to 56 seconds per
step, ETA about 17:00Z. The Opus babysitter appends to `D/babysitter_finetune/NOTES.md`
every 5 minutes and, once `PUBLISHED.json` appears under
`/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918/`, launches the 4-shard
evaluation through Luna lane `D/codex_luna_launch_eval_onethinker` on trainer v3.1 commit
`0de12a565e59ca727239653291d6916c20c29708` with `SHARDS=4`.

### Multi-GPU trainer v4

Branch `trainer-multigpu-v4-20260919`, worktree
`agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo` (of
`/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo`). v4.1
(`5d6c21d`) reviewed PASS. v4.2 (`fceddd8`) position-selects logits. v4.3 (`21dd34d`) adds
`train-ddp --parallel fsdp`. v4.4 (`fb36e01`, Devin lane `trainer_v4_4_fsdp_fix_20260919`)
makes FSDP publication rank-0 only; all four two-process tests and 79 scoped tests pass.

One defect is open: DDP admission (`student_pilot/ddp_admission.py`) passes torch's
`_CUuuid` object straight to `physical_uuid`, which accepts only bytes, a UUID, or a str, so
every rank gets refused with "CUDA-visible device UUID is missing or malformed" (confirmed
by `D/codex_luna_t228_uuid_diag/out/REPORT.md`; the single-GPU probe in `diagnostic.py`
stringifies the value first and so does not hit the bug). Devin lane
`trainer_v4_5_uuid_probe_fix_20260919` is fixing it, running locally on trinity-1-3;
cross-node Devin launches through `D/codex_luna_devin_launch_r3` failed silently on
trinity-1-13, trinity-0-3, and trinity-0-18 (no `devin.out` was created), and the `ssh -f`
launch form still needs diagnosis.

Four launch lanes are staged, each with `LAUNCH_PARAMS.env` carrying `EXPECTED_COMMIT`:
`D/codex_luna_launch_ddp_v4_a_onethinker` (trinity-2-28, attempt 3 smoke refused at
admission, `REPORT_r3.md`); `..._e_onethinker` (trinity-0-3, stopped at the arm A gate,
`REPORT_r3.md`); `..._a_qwen` (trinity-1-3 GPUs 1 to 4, FSDP, its CPU gate failed on the FSDP
publication bug that v4.4 now fixes, `REPORT.md`, procedure in `BRIEF_r2.md`); and
`..._e_qwen` (queued for trinity-2-28). Each lane keeps frozen detached checkouts per commit
under `work_checkout_<sha7>`. Once the UUID fix lands: cut a frozen checkout at the new SHA,
update `EXPECTED_COMMIT` in all four env files, then relaunch `a_onethinker` (attempt 4),
`a_qwen` (attempt 2), and only then the `e` arms. Format-A arms take GPUs ahead of format-E
arms, per the goal's priority order.

### Rewrite (free-form C-N ablation)

The v3.1 fact-locked pilot reviewed PASS (`D/codex_review_rewrite_v3_1_pilot/out/REVIEW.md`,
15 of 16 Tier I clear, fluency 1.67 of 5). The orchestrator's GO is recorded at
`/data2/jjyeung/agent_project_data/devin_lane_out/converter_freeform_v3_20260919_out/ORCHESTRATOR_GO_v3_1.json`.
The bulk run of 3,852 rows has been running since 11:40Z in lane `D/codex_rewrite_v3_1_bulk`
(attempt 2, `PROMPT_r2.md`) under lease `API_LEASE_bulk_v3_1.json` (12,000 calls,
concurrency 24 while the collector is down). Drop `CONCURRENCY.json` once the collector
relaunches, since the goal gives the collector priority on the key. The lane runner refuses
any lease whose `admitted_at` is older than five minutes; the orchestrator's scratchpad
issuer re-issues the lease whenever `API_LEASE_REFRESH_REQUEST_bulk_v3_1.json` changes, and a
successor must restart that issuer (the `issue_bulk_lease_v2.sh` pattern) or hand-issue on
request. v3.2 fluency stays parked: every variant scored 1.0 of 5
(`D/codex_rewrite_v3_2_fluency/out/ORCHESTRATOR_DECISION.md`).

### Format E (`converter_zero_call_v4_20260919`)

Unchanged: provisionally admitted, 3,867 rows, partial chains excluded.

### Base evaluations

Observer window 5, `D/codex_base_evals_v7/out/` (`RATES.md` at 11:30Z): OneThinker DSI
3,419 of 7,076 at 346 per hour, ETA 22:04Z; Qwen VSI union 382 of 500 at 51 per hour, ETA
13:48Z; Qwen VSTI 299 of 450 at 9.4 per hour, ETA 2026-09-20 03:39Z. VSTI shard 0 is absent
after 5 receipts; relaunch lane `D/codex_place_qwen_vsti_shard0_r4` was dispatched 11:33Z for
trinity-1-13 GPU 3. Qwen DSI stays stopped by user ruling.

### Lane table

| Lane | Status at 11:50Z | Next action |
| --- | --- | --- |
| `codex_relaunch_r1315_drain_attest` | Stopped at step 1; trinity-3-23 ssh stalls on hung home NFS. | Wait on `codex_luna_t323_reach_poll` REACHABLE.json, or seal the remote-evidence attestation once reviewed. |
| `collector_remote_drain_attestation_20260919` | Truthful remote-evidence schema in Devin build. | Dispatch one independent review, then seal. |
| `codex_watchdog_v6_lease` | Built and tested, 32 tests. | Takeover path only if the v5 relaunch wedges. |
| `finetune_diagnostic_v2_20260918` | OneThinker step 273/656 at 11:34Z. | Wait for `PUBLISHED.json`, then launch 4-shard eval. |
| `trainer_v4_5_uuid_probe_fix_20260919` | Fixing the DDP UUID admission bug locally on trinity-1-3. | On merge, cut frozen checkouts and relaunch the four staged DDP lanes. |
| `codex_rewrite_v3_1_bulk` | Bulk of 3,852 rows running since 11:40Z under a 5-minute lease. | Keep the lease issuer alive; drop concurrency override when the collector returns. |
| `converter_zero_call_v4_20260919` | Format E provisionally admitted, unchanged. | None pending. |
| `codex_base_evals_v7` | Four cells in flight, VSTI shard 0 relaunching. | Monitor RATES.md; union and dedup on completion. |

## 2. What dies with this session and how to relaunch it

The following die with this session and need to be recreated: the queue watcher
(`bash agent/scripts/queue_watcher.sh`); the Opus babysitter subagent; the bulk-lease issuer
for `codex_rewrite_v3_1_bulk`; the fast-forward handshake watcher for the drain-attestation
relaunch lane (it waits for `OUT/READY_FOR_FAST_FORWARD.json`, then the orchestrator runs
`git merge --ff-only d9a7b73...` on main and writes `OUT/ORCHESTRATOR_FAST_FORWARDED.json`);
every Codex and Devin lane (re-dispatch each with its resume preamble); and the 30-minute
orchestrator tick.

The following survive: GPU jobs started through real shells, including the OneThinker
baseline and the base-eval workers; all lane artifacts; and git.

## 3. Pending user rulings

- RULED about 11:50Z (this session): the goal statement quoted in full in section 1 above
  supersedes prior phrasing of the lane's objective; its priority order and deadline
  (paper-ready numbers by 2026-09-24Z) govern GPU and API-key contention.
- RULED 23:50Z (2026-09-18): Qwen3.5 DSI is dropped from evaluation; OneThinker DSI base
  continues (memory `dsi-evaluation-ruling.md`).
- RULED 23:58Z (2026-09-18): evidence that distillation works on a partial training set
  comes before full-scale runs (memory `evidence-first-priority.md`).
- RULED 03:00Z: the free-form rewrite arm is approved as an ablation, trained on the qid
  intersection with the zero-call arm.
- RULED 03:45Z: use every reachable node; the ICLR deadline is about 2026-09-26 (memory
  `use-all-nodes-iclr-deadline.md`).
- RULED 03:58Z: fine-tune the 8B and 9B students first; a 27B/31B-class student is a later
  go-or-hold decision.
- RULED 08:30Z to 08:35Z: use standard multi-GPU VLM LoRA practice; keep the one-GPU pilot
  as a baseline only; maximize Gemini-key throughput once other experiments finish.
- Open: whether to overturn the provisional Format E admission (numbered anchors to
  delivered student frames were treated by the orchestrator as grounded facts, not tool
  artifacts).
- Open: the tiered target-admission rubric, the numeric tolerance band, preparers for the
  remaining datasets (ADT, ARKitScenes, ProcTHOR, S3DIS; ScanNet v3 stays parked), and the
  27B/31B student go-or-hold, all pending the 9B result.

## 4. Standing constraints

- The orchestrator's own ssh is denied; every cross-node action goes through a Luna lane.
- The pre-shell guard blocks any command text containing the words for deleting or
  truncating, even inside a heredoc.
- The auto-mode classifier refuses a brief that would write an attestation misstating the
  verifying host; an attestation must record the host that actually gathered its evidence.
- Codex lanes die with the orchestrator session; every lane writes per-step artifacts and
  resumes from a preamble rather than depending on the dispatching session's memory.
- Devin `-p` needs `--respect-workspace-trust false` and a `timeout` wrapper.
- The recurring 30-minute orchestrator tick is session-only and must be recreated by each
  successor session.
- Never change `collector/` on main while the collector runs, blocked or not; land fixes on
  a branch, seal the contract from an epoch checkout under
  `/home/jjyeung/agent_project_distill_epochs/<commit>`, bind, attest, fast-forward, relaunch
  (CLAUDE.md production source tree rule).
- Lanes never switch branches or create branches in the main working tree; branch work
  happens in a separate `git worktree` under the lane's `work/` directory, landed on `main`
  by fast-forward.
- `BLOCKED.json` gets moved aside to acknowledge, never deleted.
- Do not treat a D-state controller with fast stateless NFS stats on its node as storage
  load; diagnose the node's NFS session state first.
- A subagent brief that mentions stopping a process is refused by the classifier
  ("Interfere With Workloads"); Codex ssh/pgrep/kill lanes die on `access_programs.cyber`
  HTTP 400 after 40 minutes to 2.5 hours, so kill steps route through the user rather than
  automation; write per-step artifacts and have the orchestrator write the final record.
- Devin lane briefs must authorize new templates or parsers explicitly, or the lane defers
  building them.
- The Codex "review" preset runs read-only and cannot write lane deliverables; use `mech`
  with a writable root for genuine reviews.
- Devin `-p` processes linger after their final answer; stop them by task once `REPORT.md`
  ends with `DEVIN_LANE_DONE`.
- Never write bulk lane data under `/home`; every Devin lane's `out/` and Codex receipts
  live on `/data2` via symlinks.

## 5. Key paths

- Collector remediation root: R =
  `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/remediation_d9f7863f1e75`.
  Fix branch `collector-drain-attestation-20260919` at `d9a7b73485a18f0445f667d626e32bba64c4ff84`;
  epoch checkout `/home/jjyeung/agent_project_distill_epochs/d9a7b73`.
- Collector relaunch and reach lanes: `D/codex_relaunch_r1315_drain_attest`,
  `D/codex_luna_t323_reach_diag`, `D/codex_luna_t323_reach_poll`,
  `collector_remote_drain_attestation_20260919`, `D/codex_watchdog_v6_lease`.
- OneThinker baseline: `agent/scratch/devin_lanes/finetune_diagnostic_v2_20260918/`; publish
  root `/data3/jjyeung/agent_project_data/finetune_diagnostic_v2_20260918`. Babysitter notes:
  `D/babysitter_finetune/NOTES.md`.
- Trainer v3.1: commit `0de12a565e59ca727239653291d6916c20c29708`. Trainer v4 worktree:
  `agent/scratch/devin_lanes/trainer_multigpu_v4_20260919/work/trainer_repo`, branch
  `trainer-multigpu-v4-20260919`, tip `fb36e01`. UUID fix lane:
  `trainer_v4_5_uuid_probe_fix_20260919`. Launch lanes: `D/codex_luna_launch_ddp_v4_a_onethinker`,
  `..._e_onethinker`, `..._a_qwen`, `..._e_qwen`.
- Rewrite v3.1 bulk: `D/codex_rewrite_v3_1_bulk`, lease `API_LEASE_bulk_v3_1.json`, refresh
  request `API_LEASE_REFRESH_REQUEST_bulk_v3_1.json`. Format E: `converter_zero_call_v4_20260919`.
- Base evaluations: `D/codex_base_evals_v7/out/RATES.md`. VSTI shard 0 relaunch:
  `D/codex_place_qwen_vsti_shard0_r4`.
- Machine-readable liveness manifest: `agent/handoff_liveness.json`.
