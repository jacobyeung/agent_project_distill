F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f
date -u +%TZ
ls $F | sed -n '60,200p'
for r in rehearsal4 rehearsal5 rehearsal; do [ -d $F/$r ] && { echo "== $r"; find $F/$r -maxdepth 4 | head -80; }; done
cat $F/REHEARSAL_FIX4_REPORT.md
