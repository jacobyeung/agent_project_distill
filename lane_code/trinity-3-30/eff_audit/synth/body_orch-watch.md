# Build brief 6 of 8: orch-watch (lane `eff_orch_watch`, branch `eff/orch-watch`, Claude Opus, effort high, size M: 6 to 8 agent-hours)

Replace per-lane polling loops and polling operator sessions with one watcher that reports state changes, and replace the wall-clock lane limit with a lease on the orchestrator's heartbeat.

## Why

- Four of six live Opus lanes at 10:54Z were operators whose task is to poll and to submit on conditions (cont_ops6: "one small poll every 5 minutes"; trin_read3: "Poll the cards ... every 10 minutes"). Each lane wrote its own loops: `loop5.sh`, `loop7.sh`, `watch_b.sh`, `poll.sh`, `poll2.sh`, `q1.sh` to `q5.sh`, `w1.sh` to `w2loop.sh`, and 19 `inv*.sh` probes (`AUD/kits/INVENTORY.md` section 3, row "Watch/poll loops").
- A poll missed a whole job: "squeue at 09:31Z showed it PENDING, but sacct says it started at 09:31:11Z and FAILED at 09:34:33Z" (`B/events/k1_ops3/20261116T0942Z_BLOCKER_170193_failed_in_staging.md`). Job 170111 started about 9.5 h before its Slurm estimate.
- Lanes end on a wall clock (`B/tools/devin_bg.sh`: `timeout "$SECS"`), which caused 14 rotations in 18 h and a reviewer that had ended before its confirmation was due (29 to 45 min lost on the K1 path).
- `B/tools/evwait.sh` logs in to hung trinity-2-28 every 10 minutes; each attempt hangs 25 s.

{{COMMON}}

## Scope

**`tools/orchkit/watch.py`.** One poller for every registered Orchard job.
- Registry: a JSONL file of rows `{token, job_id, lane, markers: [path on the batch host], metrics: {path, lines}, cadence_s, actions: [{when, do, go_file}]}`. A lane registers a job by appending a row (`util.append_jsonl_locked`).
- Cycle: one batched call through `ORCHKIT_OSSH` for all jobs together, at most once per 600 s: `TZ=UTC squeue` and `sacct` for the job ids, an existence test per marker, a bounded tail per metrics file. `sacct` decides the state, so a job that started and ended between two cycles is seen. One failed call waits 2 minutes and retries once; a second failure writes a BLOCKER event and the cycle ends.
- Output: `WATCH_STATE.json`, rewritten atomically each cycle, a heartbeat stamp, and one event in the lane's event folder per state change (PENDING to RUNNING, a start earlier than the estimate, a marker that appears, an end state), never an event without a change.
- Actions: default mode `--observe` takes none. With `--act`, an action runs only when its GO file exists, names the token and the action, and its predicate is one of the registered kinds (`state == FAILED`, `marker exists`, `alarm` from a rule function that checks its record's sha256). `scancel` and `submit` go through `launch.py` of orchkit-core; if that module is absent, the watcher writes the event and the command it would have run. You never run the watcher against the real `ossh.sh`.

**`tools/orchkit/lease.py` and `agent/scripts/orch/lane_run.sh`.** A lane wrapper that replaces the wall-clock `timeout`: the lane runs while `B/ORCH_HEARTBEAT` (touched by the orchestrator's event loop) is younger than 60 minutes, and ends at a hard ceiling given on the command line. A lane without an orchestrator therefore still ends within the hour, and a lane with one is not cut at a fixed time. The wrapper starts the lane from an empty trusted directory on `/scratch` instead of the repository root on `/home`, so a failed command can no longer leave files in the repository. Rotation near 300K tokens stays the lane's own duty.

**`agent/scripts/orch/evwait2.sh`.** The event loop of `B/tools/evwait.sh` with four changes: it touches `B/ORCH_HEARTBEAT` every pass; it probes trinity-2-28 every 30 minutes; it reports a watcher heartbeat older than two cycles as a blocker; and on a `*_RESULT_rotate*` event it prints the ready launch command for the successor (the brief comes from `tools/docs/mkbrief.py successor` if lane eff_state_entrypoint has delivered it; otherwise it names the predecessor's brief). It launches nothing itself.

## Files you own

`tools/orchkit/watch.py`, `lease.py`, `tests/test_watch.py`, `tests/test_lease.py`, `tests/fixtures/watch/`, `agent/scripts/orch/lane_run.sh`, `agent/scripts/orch/evwait2.sh`, `agent/scripts/orch/README.md`.

## Tests (folder `tools/orchkit/tests/`; a fake `ossh` replays recorded text)

1. Transitions from recorded `squeue` and `sacct` output (take real samples from the loop logs in `REF/trinity-1-3/cont_ops*/work/` if they are there; otherwise write them in Slurm's format): PENDING to RUNNING to COMPLETED gives three events; a repeated state gives none.
2. The 170193 case: `squeue` shows PENDING in one cycle and nothing in the next, `sacct` shows FAILED after 3 min 22 s: the watcher reports FAILED with the elapsed time.
3. The 170111 case: a start 9 h before the estimate gives one event in the cycle that sees it.
4. All registered jobs share one call per cycle: the fake records exactly one invocation for five jobs.
5. Transport failure: one failure, a retry after the wait (shortened in the test), then a BLOCKER event and no third call.
6. Actions: `--observe` runs none; `--act` without a GO file runs none; a GO file naming another token runs none; a matching GO file runs the fake action once.
7. Lease: with a fresh heartbeat the child keeps running; when the heartbeat stops, the wrapper ends the child within the lease plus a grace period (seconds in the test); the hard ceiling ends it regardless.
8. The suite passes on `/usr/bin/python3` and under the bwrap run of rule 8.

## Deliverables

Branch `eff/orch-watch`; `W/REPORT.md` with the adoption steps (which tmux session the watcher runs in on trinity-3-30, how a lane registers a job, how the orchestrator switches its event loop and lane launcher at a moment when no lane depends on the old ones, and that Devin's folder trust for the new start directory must be checked on the first launch); the RESULT event; the result block in RECORD.

## Out of scope

Editing `B/tools/evwait.sh`, `devin_bg.sh` or `launch_remote.sh` in place; watching the jobs that run now (170111, 170209, K1 keep their lanes and loops); polling Trinity cards, which needs ssh into nodes; launching or stopping any lane; any real Orchard call.

## Review

None required: the watcher admits and scores nothing. Before the orchestrator turns on `--act`, one reader checks the action path (test 6) once.
