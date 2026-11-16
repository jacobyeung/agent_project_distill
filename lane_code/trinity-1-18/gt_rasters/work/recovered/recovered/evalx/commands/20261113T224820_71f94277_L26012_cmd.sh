<!-- recovered by seal_plan: transcript=71f94277 line=26012 utc=2026-11-13T22:48:20.706Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_ORDER_cheap_run_bundle_acf803e7_go.md <<'EOF'
# ORCH order: the replacement bundle is confirmed; cheap state-copy run, conditional go, bundle acf803e7

I read the diff against 0842ce32 myself (`leg_s1_canary/out/STATE_COPY_MOUNT_DIFF_20261113T2245Z_3acb80b4.patch`, sha 59e419ce): the login spool parent is now a required argument limited to `/tmp` or `/var/tmp`; the node path stays the job's private `/tmp`; every disk check records the selected mount entry and all `/tmp` entries, on success and on refusal, and a storage refusal returns a recoverable record; the memory-accounting discovery records its mount selection. The validator, the return record and `state_copy.py` are unchanged; 94 fixtures pass. Accepted.

**Use:** bundle `/scratch/jjyeung/orch_cd/leg_s1_canary/out/state_copy_169097_20261113T2245Z_76ef20de.tgz` (sha256 acf803e7...), bootstrap pin 3c2d74e8..., operator file `out/STATE_COPY_OPERATOR_169097_20261113T2245Z_76ef20de.json` (dfbc98f0...). Bundles cc25e95e and 0842ce32 are superseded.

**Step 1, the harmless dry test on the login side** with `--spool-parent /var/tmp` and `--private /var/tmp/state_copy_login_169097_<nonce>`: the disk check must accept (a local ext4, xfs or btrfs entry selected by mount id; record the line), at least 1 GB free there, and the detached launch-and-fetch round trip must return a trivial command's output intact. No sessions, no step inside the job. If it refuses, stop and post the retained evidence.

**Step 2, the cheap run, once**, under the six conditions of my 2123Z order (job RUNNING with normal steps after the last save; no save due within 30 minutes and no milestone within 30 minutes; fresh object names minted only if absent from your map, capabilities through standard input only; detached launch, second short fetch, raw saved first; no retry; job checked before and after with step times).

**Timing.** The last ordinary save was at step 105 (about 21:52Z); the next is due about 23:52Z. If the dry test has passed and you can start the cheap run by 23:15Z, do. If not, wait for that save to complete and run in the window after it (about 00:00Z to 01:00Z; the step-200 export is due about 01:25Z, so start no later than 00:50Z).

Report as ordered in 2123Z, plus the spool files left on the login host (path, size) for the user's removal list. The full copy remains unauthorized.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> $C/ORCH_HANDOFF.md <<EOF
$T orch-home-distill-79: leg_s1_canary RESULT 2247Z: replacement state-copy bundle out/state_copy_169097_20261113T2245Z_76ef20de.tgz (sha acf803e7; bootstrap 3c2d74e8; operator file dfbc98f0; diff vs 0842ce32 out/STATE_COPY_MOUNT_DIFF_20261113T2245Z_3acb80b4.patch sha 59e419ce; 94 fixtures): required --spool-parent (/tmp or /var/tmp) for the login side, node path fixed, mount evidence retained on success and refusal in all three selectors. I READ THE RUNTIME DIFF (operator file, live_entry.py, operator_transport.py) and ACCEPT it. ORDER to orchard_cp2 ($N): login-side dry test on /var/tmp, then the cheap run once (start by 23:15Z or in the window after the ~23:52Z save, no later than 00:50Z); full copy still unauthorized.
$T orch-home-distill-79: orchard_cp2 RESULT 2247Z: evalx has the exact step-100 artifact (11,474 B, sha 927f51af); production step times around the two failed rehearsal jobs were 130.3-134.5 s (no per-step UTC bounds held, so no claim about slowdown during them).
EOF
echo done $N