R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal4; T=$R/target/o/rehearsal/live; date -u +%TZ
for f in gcs_m2.json gcs_m3.json copy.json markers.json; do echo "== $f"; head -c 1500 $T/$f; echo; done
ls -la $R/target/o/gcs_claims | head; ls $R/sessions | head
grep -n -E "\.done|gcs_m|def " $R/../rehearsal_copier.py | head -30 | cut -c1-250
