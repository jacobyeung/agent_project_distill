set -u
B=/scratch/jjyeung/orch_n30/native_r2
cd / 
{
echo "== host $(hostname -s)"
ls -la $B/work/full_c8r/x/native/ $B/work/full_c8r/x/native/paired/ $B/work/parent/r5/ $B/work/parent/r5/merge_results/ $B/work/parent/r3/ $B/work/meta/sj/orch_cd/legs1_reads/work/vendor/r3/ $B/work/direct/ 2>&1
} >&2
F="$B/work/full_c8r/x/native/R1.json $B/work/full_c8r/x/native/paired/IN_JOB_ADMISSION.json $B/work/parent/r5/merge_results/B2048.json $B/work/parent/r5/SCORING_DEV.md $B/work/parent/r3/TASKS.jsonl $B/work/parent/r3/FRAMES.json $B/work/parent/r3/STRATA.jsonl $B/work/parent/r3/RUNCARD.md $B/work/meta/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl $B/work/meta/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json"
for x in B2048_kit_summary.json MERGE_INPUTS.json MERGE_COMPLETE.json; do for d in $B/work/parent/r5/merge_results $B/work/parent/r5; do [ -f $d/$x ] && F="$F $d/$x"; done; done
G=""; for f in $F; do [ -f "$f" ] && G="$G ${f#/}"; done
T=$(du -cb $(for g in $G; do echo /$g; done) | tail -1 | cut -f1)
echo "== total bytes $T" >&2
sha256sum $(for g in $G; do echo /$g; done) >&2
if [ "$T" -lt 20000000 ]; then tar cf - $G; else echo "TOO BIG" >&2; fi
