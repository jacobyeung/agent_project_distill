W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z7/out; date -u +%TZ; D=$W/work/tgcs3; test -e $D && { echo EXISTS; exit 1; }
mkdir -p $D && cp $Z/tgcs/run_tgcs.sh $Z/tgcs/driver.py $D/ && cp $W/work/tgcs2/observe.py $D/ && sha256sum $D/* | cut -c1-90
O=$W/work/tgcs_900002b; timeout 500 bash $D/run_tgcs.sh 900002 /scratch/jjyeung/orch_n30/n_ops8_x/sess_900002.json $Z/kit_n $O; echo rc=$?
M='s#https?://[^ "]*#[URL]#g'; cd $O && { ls logs; sed -E "$M" RESULT.json | head -80; echo ==HTTP; sed -E "$M" logs/http.jsonl | sed -E 's/"time": ?[0-9.]+, ?//' | sort | uniq -c | sort -rn | head; echo ==GCERR; sed -E "$M" logs/gc.stderr | tail -5; echo ==COPERR; sed -E "$M" logs/copier.stderr | tail -5; }
echo ==E3; cat $Z/e3/E3_USAGE.md | head -70; wc -l $Z/e3/*.sh $Z/e3/*.py
