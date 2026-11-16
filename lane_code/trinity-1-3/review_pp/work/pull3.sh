B=/scratch/jjyeung/orch_n30/native_r2; W=$B/work
F="$W/full_c8r/x/native/paired/IN_JOB_ADMISSION.json $W/full_c8r/x/native/R1.json.pin.json $W/parent/r5/merge_results/B2048.json $W/parent/r5/merge_results/B2048_kit_summary.json $W/parent/r5/merge_results/MERGE_INPUTS.json $W/parent/r5/merge_results/MERGE_COMPLETE.json $W/parent/r5/SCORING_DEV.md $W/parent/r5/dev_scoring.py $W/parent/r3/TASKS.jsonl $W/parent/r3/FRAMES.json $W/parent/r3/RUNCARD.md $W/direct/DIRECT_B2048_COMPACT.json $B/builds/06_parent_adapter/out/items_parent_main.jsonl"

T=$(du -cb $F | tail -1 | cut -f1); echo total $T >&2
sha256sum $F >&2
[ "$T" -lt 19000000 ] && tar cf - $(for f in $F; do echo ${f#/}; done) -C / || echo TOO BIG >&2
