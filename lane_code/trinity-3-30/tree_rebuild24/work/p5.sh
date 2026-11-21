W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z7/out; date -u +%TZ; P=$Z/tree_rebuild_b24m4z7_7daf1570.tar
cat $P.sha256; sha256sum $P | cut -c1-64
cat $Z/BUILD24M4Z7_REPORT.md; echo ==NEEDS; cat $Z/NEEDS_OTHER_FILE_24M4Z7.md | head -20
echo ==OBS; grep -n "HTTPSConnection" $Z/tgcs/observe.py $Z/e3/observe.py | head; sha256sum $Z/tgcs/*.py $Z/tgcs/run_tgcs.sh | cut -c1-90
sha256sum $W/w24z4/out/kit_n/b/gc.py $W/w24z7/out/kit_n/b/gc.py 2>&1 | cut -c1-90
O=$W/work/tgcs_900002; test -e $O && { echo EXISTS; exit 1; }
ls -l /scratch/jjyeung/orch_n30/n_ops8_x/ | cut -c1-120
timeout 500 bash $Z/tgcs/run_tgcs.sh 900002 /scratch/jjyeung/orch_n30/n_ops8_x/sess_900002.json $Z/kit_n $O; echo rc=$?
M='s#https?://[^ "]*#[URL]#g'; cd $O && { ls logs; sed -E "$M" RESULT.json | head -50; echo ==HTTP; sed -E "$M" logs/http.jsonl 2>/dev/null | sed -E 's/"time": ?[0-9.]+,? ?//' | sort | uniq -c | sort -rn | head; echo ==GCERR; sed -E "$M" logs/gc.stderr 2>/dev/null | tail -8; }
timeout 200 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/n30_mirror/tree_rebuild23 && cat > /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) | cut -c1-16'" < /dev/null
