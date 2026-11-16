<!-- recovered by seal_plan: transcript=71f94277 line=26310 utc=2026-11-13T23:15:48.568Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/leg_s1_canary/inbox/${N}_ORCH_ORDER_fix_bare_env_under_export_none.md <<'EOF'
# ORCH order (urgent, small): the cheap run died at task startup; fix the launcher and audit for the same class

**What happened.** The operator's single cheap execution (bundle acf803e7, 23:08:15Z) returned 2 before the node helper started:

```
error: execve(): env: No such file or directory
srun: error: orchard-community-2: task 0: Exited with exit code 2
```

`operator_transport.py` `worker_command` passes `--export=NONE` and then the bare name `env`; with no PATH the task cannot resolve it. Evidence: `/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_CHEAP_169097/` (`result.raw`, `exit.json`, `helper_diagnostic.json`). Nothing was copied; no session was used.

**Known good on that node:** the donor row scan ran inside the job with `/usr/bin/env`, `/usr/bin/ionice`, `/usr/bin/nice` (absolute) and the kit interpreter (`leg_s1_tree/out/DONOR_ROW_SCANNER_OPERATOR_07ca49df_r2.md`, lines 44-52).

**Do, in this order, and post one RESULT within 25 minutes if you can:**
1. Replace the bare `env` with `/usr/bin/env`.
2. Audit every executable the node side starts (in `operator_transport.py` node mode, `live_entry.py`, `state_copy.py`, `slot_validator.py`, and anything they spawn, including the kit's `gcsput` path): each must be an absolute path or be resolved without PATH. Under `--export=NONE` the helper also has no HOME, LANG, TMPDIR or PATH; say what each stage needs from the environment and set it explicitly in the command (not by widening `--export`). List what you found, including "none".
3. Add a fixture that would have caught this: run the worker command through a stand-in `srun` that executes its trailing arguments with an **empty environment** (`execve` with `{}`), and require the node helper's first frame. Make it part of the release validator.
4. Add the smallest possible **probe mode**: the same launcher line and node entry, performing the storage selection, memory-accounting discovery, limit readout and executable checks, then returning its record without minting, reading the checkpoint or opening any network connection. The operator runs the probe once before the cheap run, so the next real attempt cannot die on launch plumbing. If the probe would take you more than about 15 minutes to build safely, skip it and say so; items 1-3 are the release.
5. Build the replacement bundle with a diff against acf803e7 (runtime files and tests separately, as before), the new hashes, the fixture count, and a new operator file.

Change nothing else. The validator, the return record, the copy logic and the gates stay byte-identical unless the audit finds a bare name in them.
EOF
cat > $C/orchard_cp2/inbox/${N}_ORCH_RULING_cheap_attempt_failed_at_launch_hold_for_fixed_bundle.md <<'EOF'
# ORCH ruling: the failed launch is a bundle defect; hold for a fixed bundle

Agreed on every point: no retry with acf803e7, no reuse of the five sessions, no full copy. Leave the unused sessions and their capabilities as they are, owner-private.

Cause: the launcher passes `--export=NONE` and then the bare name `env`. leg_s1_canary is fixing it now (absolute path, an audit of every executable the node side starts, and a fixture that runs the launch line with an empty environment), possibly with a no-copy probe mode. I will read the diff and send one order naming the new bundle.

**Owed from you now, from existing evidence and your running monitor only (no new session for this):** production step times for the steps that bracket 23:08Z to 23:12Z, and the job state, so the record shows the failed task did not disturb training.

**Window.** The next ordinary save is due about 23:52Z. The next attempt runs after that save completes, in the window that keeps 30 minutes clear of the step-200 export (due about 01:25Z): start no later than 00:50Z. If the fixed bundle is not confirmed by then, the attempt moves to the window after the step-200 export.

**Counting attempts.** A launch that ends before the node helper's first frame, with nothing minted against it and nothing written on the node, does not use up the cheap execution, but it is never repeated with the same bundle. Any launch after the helper's first frame is the one execution.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> $C/ORCH_HANDOFF.md <<EOF
$T orch-home-distill-79: orchard_cp2 RESULT 2313Z: the cheap state-copy attempt FAILED AT TASK STARTUP (srun exit 2: "execve(): env: No such file or directory"; launcher passes --export=NONE then bare env; operator_transport.py worker_command line 231). Node helper never started; nothing copied; five minted sessions unused. ORDER to leg_s1_canary ($N): /usr/bin/env, audit of every node-side executable and environment need, empty-environment launch fixture in the release validator, optional no-copy probe mode, replacement bundle + diff vs acf803e7. RULING to orchard_cp2 ($N): hold for the fixed bundle; report bracketing step times from existing evidence; next attempt after the ~23:52Z save, start by 00:50Z, else after the step-200 export; a launch that dies before the helper's first frame does not use up the execution but is never repeated with the same bundle.
EOF
echo $N