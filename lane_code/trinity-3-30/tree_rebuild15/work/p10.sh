B=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f; R=$B/rehearsal4; date -u +%TZ
stat -c "%a %n" $R/sessions $R/sessions/sess.json $R/target/o/gcs_claims
cat $B/go_rehearsal.sh
grep -n -E "sessions|chmod|0o7|mkdir" $B/rehearsal_copier.py $B/rehearsal_runner.py $B/make_rehearsal4.py $B/make_rehearsal4_launch.py 2>/dev/null | head -30 | cut -c1-260
grep -n -B3 -A3 "directory mode" $R/../../../out/kit_n_go/b/*.py 2>/dev/null | head -30 | cut -c1-260
