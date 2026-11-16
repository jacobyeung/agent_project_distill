<!-- recovered by seal_plan: transcript=71f94277 line=28035 utc=2026-11-14T03:13:01.892Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_APPROVED_sbatch_path_and_plan_for_slow_queue.md <<'EOF'
# ORCH answers to QUESTION 0311Z

## 1. Approved: the executable path, one fresh test, one real submission

Replace only argument 0 of the two supplied lists by `/usr/local/bin/sbatch` (the path your own submissions use). `BATCH.sh` (sha 220885c3...), seal 8d5bdd73 and token a35f2d78fe7c5ee8d are unchanged. Run one fresh `--test-only` call; if it passes, the one real submission. If the test fails for any other reason, stop and post the raw return. Tell lane if_p0's inbox the corrected path so its hand-off file is fixed for later arms.

## 2. The forecast of 13:50Z for job 169367

Understood: about ten and a half hours, by a forecast that assumes every running job uses its full limit. Keep 169367 and the P0 job queued; they cost nothing and gain age.

Plan B, which I am preparing and you should design now on CPU: when the production leg's allocation ends (wall end 15:25Z, trainer stop about 14:25Z) our four-GPU cap on `advanced` is free. The `advanced` cap is four GPUs on one node per user, so the form is ONE four-GPU job that runs up to four single-GPU tasks side by side: the step-200 read, the step-400 read, the final-step read, and IF-P0's P0. Write `work/milestone/PACKED_ADVANCED_PLAN.md` (at most 40 lines): how your accepted launcher's job script would run several reads in one allocation (one staging of the shared runtime and base, one export per read, one card each by index), what changes in the launcher and what needs confirmation, the staging time and disk on the node, and the expected wall time. Do not build it yet; I decide when I see the plan and the queue. If either queued `general` job starts first, that read simply drops out of the packed job.

## 3. Still owed from my 0234Z note

Two lines on what a direct step-200 read on a Trinity card would need (runtime and kits, card, disk on the node, duration), now that the export is landing on trinity-0-28. Disk on that node is tight and shared with a main run, so say the bytes.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx QUESTION 0311Z: IF-P0 P0 test-only returned 127 (/usr/bin/sbatch absent on the login host; /usr/local/bin/sbatch exists); nothing submitted; queue and main notices checked (only our 169367 in general). Login host is EST; with TZ=UTC Slurm forecasts job 169367 at 13:50:00Z. APPROVED ($N): argument 0 -> /usr/local/bin/sbatch, one fresh test-only, one real submission. PLAN B requested (design only): one four-GPU advanced job after the leg's allocation ends, packing the step-200, step-400 and final reads and IF-P0 P0; Trinity direct-read needs still owed. Re-armed evwait (b5qxuqk87)." >> $C/ORCH_HANDOFF.md; echo $N