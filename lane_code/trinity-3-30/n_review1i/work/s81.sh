W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; R=$W/w24/work/build24k/rehearsal_k6
date -u +%TZ
cd $W/w24z13b/out; sha256sum jn4.sh jn5.sh tree_rebuild_b24m4z13b_95045531.tar < /dev/null; cat tree_rebuild_b24m4z13b_95045531.tar.sha256 BUILD24M4Z13B_REPORT.md T_JN5_USAGE.md < /dev/null
echo "== jn5.sh"; cat -n jn5.sh < /dev/null
echo "== JN5.diff"; cat JN5.diff < /dev/null
echo "== rev24m4z13 log tail"; tail -c 5000 $W/work/rev24m4z13.log < /dev/null
echo "== MODEQ_WRITES"; cat $W/w24z15/out/MODEQ_WRITES.md < /dev/null
echo "== rehearsal files"; cd $R 2>/dev/null && find . -maxdepth 6 \( -name v.json -o -name identity.txt -o -name WAITING_REVIEW.json -o -name 'c[0-4].json' -o -name s2.json -o -name population.json -o -name 'indices.json*' -o -name reader_filters.json -o -name binding.json -o -name receipt.json -o -name f.json -o -name f1.json -o -name ADMIT.json \) -printf '%p %s\n' < /dev/null | head -60
for d in $W/work/d173912/173912 $W/work/d173966; do echo "== $d"; ls $d < /dev/null | tr '\n' ' '; echo; done
