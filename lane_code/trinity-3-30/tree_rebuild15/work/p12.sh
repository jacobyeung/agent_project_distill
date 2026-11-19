B=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f; date -u +%TZ; wc -l $B/live.py $B/live_tests.py
grep -n -E "sess|WRITER|def put|chmod|0o6|0o7|\.done|no sessions" $B/live.py | head -40 | cut -c1-250
grep -n -E "sess\.json|chmod|0o7|0o6|mkdir\(" $B/live_tests.py | head -20 | cut -c1-250
grep -n -E "def pass_once|def _export|sessions unusable|gcs_|\.done" $B/../../out/kit_n_go/b/pc.py | head -30 | cut -c1-250
