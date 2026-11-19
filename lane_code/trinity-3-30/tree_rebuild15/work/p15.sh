W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; O=$W/w24/out; date -u +%TZ
cat $O/BUILD24K_REPORT.md; echo ====; ls -la $O/tree_rebuild_b24k_2ace1de4.tar; head -c 1500 $O/DELIVERY_24K.json; echo; cat $O/jr.sh; echo ====
cat $W/w24/work/build24f/REHEARSAL_FIX4_REPORT.md; echo ====
grep -n -E "'r'|== *.r.|mode r|def r\b|routing_selection|selection" $O/kit_n_go/b/a.py | head -30 | cut -c1-300
wc -l $O/UPLOADS_24K.list $O/UPLOADS_24K_GO.json
