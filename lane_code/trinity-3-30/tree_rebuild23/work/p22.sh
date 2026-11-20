W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z4/out; date -u +%TZ; test -e $W/work/se2.tar && { echo EXISTS; exit 1; }
cd $Z && tar cf $W/work/se2.tar e2/e2.sh e2/e2.py e2/observe.py e2/run.sh e2/k.tgz e2/pins.json && sha256sum $W/work/se2.tar && ls -l $W/work/se2.tar && sha256sum e2/e2.sh e2/e2.py e2/observe.py e2/run.sh e2/k.tgz e2/pins.json
grep -E "^\| e2/" e2/E2_USAGE.md; grep -n "job-name\|partition\|output\|error" e2/e2.sh; cat UPLOADS_24M4Z4_E2.list
