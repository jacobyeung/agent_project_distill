<!-- recovered by seal_plan: transcript=71f94277 line=28452 utc=2026-11-14T04:09:15.949Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/if_p0/inbox/${N}_ORCH_TASK_later_arms_on_advanced_cross_seal_and_time_limit.md <<'EOF'
# ORCH task: make the later arms runnable on `advanced` after a P0 that ran under seal 8d5bdd73

Seal 810f8085 received; I will read its diff together with the change below, once, so do not wait for a confirmation of 810f8085 alone.

**The situation to design for.** P0 will most likely run on `general` as job 169413 under seal **8d5bdd73** (it is next in line there). IF8 is the arm at risk of not fitting twelve hours. After the production leg ends (about 15:00Z) the `advanced` partition is free for us, and its limit is 24 hours. So the natural plan is: P0 on `general` now under 8d5bdd73, then IF8 (and AT8 if admitted) on `advanced` as single one-GPU jobs.

Two things stop that today, as far as I can tell; confirm or correct each with file and line:
1. A later arm verifies P0's returned archive against its **own** kit seal, so a kit with a new seal refuses a P0 produced under 8d5bdd73.
2. The time admission is fixed at 43,200 seconds.

**Change (next seal, built on 810f8085):**
- **Predecessor admission.** A later arm may consume a P0 (or IF8) archive produced under an explicitly pinned predecessor seal, here 8d5bdd73 only, if and only if every file that determines the science is byte-identical between the two seals: model and branch code, optimizer and protocol, selection and exclusion code and inputs, the read and decision code, the row file. List those files with their hashes in a sealed table and have the gate recompute and compare them; anything else differing must be only job plumbing (partition admission, provenance fields, staging order). The result records both seals.
- **Time limit by partition.** `general`: 12 hours as now. `advanced`: the job requests 24 hours and the projection admits against 86,400 seconds minus the same reserve. The 300 steps are still never shortened.
- Nothing else changes.

**Deliver** one RESULT: the new seal; diffs against 8d5bdd73 in two parts (to 810f8085, and from 810f8085 to the new seal), runtime and tests separately; the sealed table of science files; test count; rehearsal results for a P0 under one seal consumed by IF8 under the other, on both partitions. No packet until I confirm and P0's real result exists.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: if_p0 RESULT 0408Z: advanced-capable kit sealed (out/advanced_v4/kit_ifp0_orchard_job_810f80852e86b5da; seal 810f8085; archive db907aa0; 75 tests; rehearsal 3/3 arms on both partitions). Confirmation deferred: TASK ($N) for the next seal so later arms can run on advanced (24 h) after a P0 run under seal 8d5bdd73: pinned predecessor-seal admission with a sealed table of byte-identical science files, and a per-partition time limit; I read both diffs together. Re-armed evwait (b3t4hel2v)." >> $C/ORCH_HANDOFF.md; echo $N