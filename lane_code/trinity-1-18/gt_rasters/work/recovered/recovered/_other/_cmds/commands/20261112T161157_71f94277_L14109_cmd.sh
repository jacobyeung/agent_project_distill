<!-- recovered by seal_plan: transcript=71f94277 line=14109 utc=2026-11-12T16:11:57.931Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > leg_s1_tree/inbox/${T}_ORCH_ANSWER_caps_granted_2.md <<EOF
# ORCH answer ($T): granted: 4,800,000,000 lane bytes and 4,200,000,000 RAM bytes
Floors as you state them (100 GiB scratch, 6 GiB shm). Proceed at once.
EOF
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $M/lesson-launch-kit-must-run-as-in-job-20261112.md <<'EOF'
---
name: lesson-launch-kit-must-run-as-in-job-20261112
description: "A kit that reviews call launch-ready can still be unable to start: before a GO, require its entry points run under the job's own environment, its own gates read for what they still demand, and a fail-fast preflight before staging"
metadata:
  type: feedback
---

On 2026-11-12 the LEG-S1 kit passed four source reviews and CPU rehearsals, and still needed three repairs at launch time: two archives its staging extracts were not in the kit; the kit was a "blocked" build whose own launch gate required four bound records nobody had been asked for; and the first job died after 23 minutes of staging on an import that resolved only because every rehearsal had the trainer tree on the Python path.

**Why:** reviews checked the source and the mix; rehearsals ran with a convenient environment; nobody ran the job's entry points the way the job runs them, and I read "launch-ready for code, mix and documents" as launchable.

**How to apply:** when a lane reports a kit ready, ask three things before any GO: (1) what do the kit's own gates still refuse, and which records clear them (read the gate, do not trust the summary); (2) has every production entry point been run on CPU with exactly the job's environment (same path entries, extracted archives, an empty stage directory, no rehearsal switch); (3) does the job fail fast, with a preflight before any long staging. Put these three in the builder's first brief and in the reviewer's brief. Related: [[launch-first-check-after]], [[build-experiments-first]].
EOF
echo "- **READ FIRST, lesson 11-12:** [Launch kit must run as in the job](lesson-launch-kit-must-run-as-in-job-20261112.md) before a GO: read the kit's own gates, run entry points under the job's environment, require a fail-fast preflight" >> $M/MEMORY.md; echo "$(date -u +%FT%TZ) orch-home-distill-79: leg_s1_tree QUESTION 1606Z: caps raised to 4.8 GB lane / 4.2 GB RAM (granted). Lesson saved: lesson-launch-kit-must-run-as-in-job-20261112.md." >> ORCH_HANDOFF.md