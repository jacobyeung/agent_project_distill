W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z7/out; cat $Z/e3/e3.sh; echo =====RUN; cat $Z/e3/run.sh; echo =====PY; cat $Z/e3/e3.py
echo =====REC; cd $W/work/tgcs_900002b && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json;r=json.load(open('RESULT.json'))
for x in r['receipts']: print(x['name'],x['bytes'],x['sha256'],x['md5'],x['generation'])"
