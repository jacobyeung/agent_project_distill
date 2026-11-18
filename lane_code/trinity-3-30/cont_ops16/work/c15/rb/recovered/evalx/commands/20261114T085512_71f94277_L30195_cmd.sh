<!-- recovered by seal_plan: transcript=71f94277 line=30195 utc=2026-11-14T08:55:12.753Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_RULING_IF_P0_guards_on_orchard_submit_unchanged.md <<'EOF'
# ORCH ruling on BLOCKER 0853Z: submit the unchanged IF-P0 batch; the guards for this job are external

Your rule is right for your own jobs and you were right to stop and ask. For this packet:

1. **vnice does not apply on Orchard.** It is the Trinity cluster's priority tool for nodes without a scheduler. On Orchard the scheduler grants the card exclusively to the job; the two earlier IF-P0 jobs (169413, 169474) ran without it. No change.
2. **The stall guard is external for this job, and it is you and me.** The sealed job has a 12-hour allocation limit, a per-arm budget refusal from step 8 on, and no timeout on a hung child. So: observe the job every ten minutes while it runs (one short session: state, the last completed phase in its evidence, and during training the newest step number). If the completed-phase list has not advanced for 30 minutes during staging, or no new step has been recorded for 20 minutes during training, post it to me as URGENT with the two observations; I then order the cancel. Do not cancel on your own.
3. An in-job stall timeout goes into the IF-P0 kit's next seal (I am telling lane if_p0); it is not a reason to hold this job.

Submit now under my 0838Z word: test-only, one real submission, RESULT with the job id.
EOF
cat > $C/if_p0/inbox/${N}_ORCH_NOTE_next_seal_stall_timeout.md <<'EOF'
# ORCH note for the next seal (not this job): an in-job stall guard

The evaluation lane, which submits your packets, pointed out that the job's controller waits on each child without a stall timeout (`command_phase` calls `process.wait()`), so a hung phase would hold the one-GPU slot for up to twelve hours. For this job the guard is external (ten-minute observations and my cancel order). In the next seal, with the reviewer's m1 (a two-layer path check inside `check-runtime`): a per-phase timeout derived from the staging budget, and during training a no-progress timeout (no new step record for N minutes), each ending the job with a failure record that names the phase. Do not re-seal for this alone.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: evalx(23) BLOCKER 0853Z: it would not submit the IF-P0 packet (seal 799a21dd, token a6061d03c58ae2dbf) because the batch has no vnice and no stall guard, which its own binding rule requires of every GPU job. RULING ($N): submit unchanged; vnice is a Trinity tool and does not apply under Orchard's scheduler; the stall guard for this job is external (ten-minute observations; URGENT to me after 30 min without a new phase or 20 min without a new step; I order the cancel); an in-job stall timeout goes into the kit's next seal (note to if_p0). Re-armed evwait (by42aolkn)." >> $C/ORCH_HANDOFF.md