W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z7/out; date -u +%TZ
for f in $Z/tgcs/observe.py $Z/e3/observe.py $W/work/tgcs2/observe.py; do echo "=== $f"; cat $f; done
diff $Z/tgcs/run_tgcs.sh $W/work/tgcs2/run_tgcs.sh && echo RUN_SAME; diff $Z/tgcs/driver.py $W/work/tgcs2/driver.py && echo DRIVER_SAME
grep -n -i "stop\|rate\|window\|reserve\|113" $Z/ENOSPC_24M4Z7.md | cut -c1-500 | head -30
